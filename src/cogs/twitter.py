import datetime
from discord.ext import commands, tasks
import tweepy
import dotenv
import os
from resources.lyrics import allQuotes as lyrics
import random

dotenv.load_dotenv()

API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_KEY_SECRET")
BEARER_TOKEN = fr"{os.getenv('X_BEARER_TOKEN')}"
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")


class Lyric:
    def __init__(self, data: dict):
        self.quote: str = data["quote"]
        self.song = data["song"]
        self.album = data["album"]

    def __str__(self):
        return f"{self.quote.lower()}\n\n{self.song} ({self.album})"


client = tweepy.Client(BEARER_TOKEN, API_KEY, API_SECRET,
                       ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET)
api = tweepy.API(auth)


class TwitterBot(commands.Cog):
    def __init__(self):
        self.client: tweepy.Client = client
        self.tweet_lyric.start()
        print("STARTED TWITTER BOT")

    @tasks.loop(time=[datetime.time(hour=12), datetime.time(hour=16), datetime.time(hour=20), datetime.time(hour=0), datetime.time(hour=4), datetime.time(hour=8)])
    async def tweet_lyric(self):
        lyric = Lyric(random.choice(lyrics))
        tweet: tweepy.Response = self.client.create_tweet(text=str(lyric))
        print(tweet)


def setup(bot):
    bot.add_cog(TwitterBot())
