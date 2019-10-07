import logging
import praw
import time
import json
import re
import string

import responses_constants as const
import reddit_service as reddit

# Removed any amount of white space left at beginning and end of string
def removeLeadingTrailingWhiteSpace(str):
    while str != "" and str[0] == ' ':
        str = str.lstrip()
    while str != "" and str[len(str) - 1] == ' ':
        str = str.rstrip()
    return str

# Removes any markdown syntax from the string
def removeMarkdown(str):
    markdownSyntax = [
        "\\*", 
        "\\_",
        "\\[", "\\]", "\\(", "\\)",
        "\\~",
        "\\^"
    ]
    removed = str
    for syntax in markdownSyntax:
        if syntax in removed:
            removed = removed.remove(syntax, "")
    return removed

# Cleans a string to remove any unwanted punctuation, emojis and/or line endings and converts to lower case, useful for comparing
def cleanString(phraseStr, toLower=True):
    # Remove punc
    phraseStr = phraseStr.translate(str.maketrans('', '', string.punctuation))
    # Remove Emojis 😭
    phraseStr = phraseStr.encode('ascii', 'ignore').decode('ascii')
    # Remove markdown formatting
    phraseStr = removeMarkdown(phraseStr)
    # Remove any unwanted white space at beginning or end
    phraseStr = removeLeadingTrailingWhiteSpace(phraseStr)
    if toLower:
        return phraseStr.lower()
    else:
        return phraseStr

# Searches the database for a match to the phrase
def checkDatabase(respDatabase, phrase):
    responses = respDatabase[const.DATABASE_MASTER_KEY]
    for r in responses:
        responseLine = cleanString(r['text'])
        # Criteria: Match completely...
        if phrase == responseLine:
            return r
        # OR users comment has part of full response line
        # Too many false positives, removed for now 
        # if (phrase in responseLine):
        #     return r

# Simple array contains function
def contains(list, checkItem):
    for item in list:
        if item == checkItem:
            return True

# Check to see if the bot already replied to the comment
def hasReplied(repliesArray):
    isMoreComments = False
    for reply in repliesArray:
        if hasattr(reply, 'children'):
            isMoreComments = True

        if isMoreComments:
            for childId in reply.children:
                active = reddit.getRedditActive()
                comment = active.comment(id=childId)
                if comment and comment.author and comment.author.name == const.BOT_NAME:
                    return True
        else:
            if reply and reply.author and reply.author.name == const.BOT_NAME:
                return True

def validateReply(respDatabase, repliedIds, reply):
    # Ignore deleted/removed comments
    # if "deleted" in comment.body or "removed" in comment.body:
    #     continue

    if reply and reply.author and reply.author.name == const.BOT_NAME:
        return False
    
    # Check if already posted a response
    # Shorten comment to 5 words for display purposes in cmd
    commentShort = " ".join(reply.body.split()[:5])
    commentAuthor = "Unknown"
    if reply.author:
        commentAuthor = reply.author.name
    if hasReplied(reply.replies) or contains(repliedIds, reply.id):
        logging.debug("Already replied to comment '%s' by '%s'" % (commentShort, commentAuthor))
        return False
        
    commentClean = cleanString(reply.body)
    dbMatch = checkDatabase(respDatabase, commentClean)
    if dbMatch != None:
        result = True #reddit.reply(reply, dbMatch)
        if result:
            repliedIds.append(reply.id)
            logging.info("Replying to comment '%s' - '%s'" % (commentAuthor, commentShort))
        return result

# Checks all comments in a post for a match
# Checks all top level comments, then second, etc...
def checkComments(respDatabase, repliedIds, post):
    # Snippet originally from
    # https://praw.readthedocs.io/en/latest/tutorials/comments.html#the-replace-more-method
    post.comments.replace_more(limit=None)
    comment_queue = post.comments[:]  
    while comment_queue:
        comment = comment_queue.pop(0)
        validateReply(respDatabase, repliedIds, comment)
        comment_queue.extend(comment.replies)

# Scans /new/ and then /hot/ for matching comments
def scan(respDatabase):
    # Store array of replied to comment id's this scan to not reply more than once
    repliedCommentIds = [ ]

    subreddit = reddit.getSub(const.SUBREDDIT)
    logging.info("Starting scan of 'New' posts")
    for post in subreddit.new(limit=const.NEW_POST_LIMIT):
        checkComments(respDatabase, repliedCommentIds, post)
        logging.info("Scanned post '%s'" % post.title)

    logging.info("Starting scan of 'Hot' posts")
    for post in subreddit.hot(limit=const.HOT_POST_LIMIT):
        checkComments(respDatabase, repliedCommentIds, post)
        logging.info("Scanned post '%s'" % post.title)

# Reads the db file name and returns the db
def loadDatabase():
    with open(const.DATABASE_FILE_NAME) as jsonFile:
        return json.load(jsonFile)

def clearDebugPost():
    if const.DEBUG_PROFILE_POST:
        profileSub = reddit.getRedditActive().subreddit("u_%s" % const.BOT_NAME)
        posts = profileSub.new()
        for post in posts:
            if "Live on subreddit" in post.title:
                logging.debug("Removing info post on own subreddit")
                post.delete()

def begin():
    if not const.APP_ID or not const.APP_SECRET:
        logging.error("Unable to start bot. APP_ID or APP_SECRET is requires")
        return

    # Post to profile with info
    clearDebugPost()
    if const.DEBUG_PROFILE_POST:
        profileSub = reddit.getRedditActive().subreddit("u_%s" % const.BOT_NAME)
        debugPost = profileSub.submit("Live on subreddit /r/%s" % const.SUBREDDIT, "Live on '%s' \n\nHot post count: '%s'\n\nNew post count: '%s'" % (const.SUBREDDIT, const.HOT_POST_LIMIT, const.NEW_POST_LIMIT))
        debugPost.mod.sticky()
        logging.debug("Created and stickied debug post on self subreddit")

    # Load database into memory
    responseDatabase = loadDatabase()
    while True:
        scan(responseDatabase)

        # Complete scan and sleep for X minutes
        logging.info("Completed scanning comments. Sleeping for %d minute(s)" % const.SLEEP_MINUTES)
        time.sleep(const.SLEEP_MINUTES * 60)
        