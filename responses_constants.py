# Reddit API information
APP_ID = ''
APP_SECRET = ''
APP_AGENT = 'Darkest Dungeon Response Bot v0.1 - /u/JoshLmao'

# Username and password of the Reddit bot
BOT_NAME = 'dd_responses_bot'
BOT_PASSWORD = ''
# Message should contain 2 strings to add at runtime in this order: Description, Audio Url
BOT_MESSAGE = '''[%s](%s)\n\n------\n\n[^(Source)](https://github.com/JoshLmao/DarkestDungeonResponseBot) ^(|) [^(Issues)](https://github.com/JoshLmao/DarkestDungeonResponseBot/Issues) ^(|) [^(Maintained by JoshLmao)](https://reddit.com/u/joshlmao) ^(|) [^(Support ☕)](https://ko-fi.com/joshlmao)'''

# Relevant file name of the JSON database file (same folder as .py)
DATABASE_FILE_NAME = "voice_lines.json"
# Key value of database, value holds array of data
DATABASE_MASTER_KEY = "voice-lines"

# Subreddit to check over
SUBREDDIT = 'darkestdungeon'
# Amount of new & hot posts to check comments on
NEW_POST_LIMIT = 15
HOT_POST_LIMIT = 30
