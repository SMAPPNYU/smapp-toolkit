"""
Module indicator
"""
try:
    import twitter_figure_makers
    NO_FIGURES = False
except:
    warnings.warn("smapp-toolkit: Missing some graphics packages. Making figures won't work.\n")
    NO_FIGURES = True

from mongo_tweet_collection import MongoTweetCollection
from bson_tweet_collection import BSONTweetCollection
