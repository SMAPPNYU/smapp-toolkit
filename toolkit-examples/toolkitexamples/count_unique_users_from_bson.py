"""
Simple example of how to count unique users in a data set.
Must use user IDs, as users can change screen names over time.

Requires an iteration over all tweets, which is generally
slow against the Mongo Database and fast against a BSON file.

Note: because counting unique users requires an iteration over
all tweets, any other statistic that requires an iteration over
all tweets can be done in the same loop.
"""

from datetime import datetime
from smapp_toolkit.twitter import MongoTweetCollection, BSONTweetCollection

# swap the 'cfile' variable with the path to your bson file
# this creates a collection from a bson file
cfile = "/scratch/smapp/obama_romney/obama_romney_tweets_8_15.bson"
collection = BSONTweetCollection(cfile)

# store all unique users in a 
# dictionary based on the tweet
# object's user id string
unique_users = {}
before = datetime.now()
for tweet in collection:
    unique_users.add(tweet["user"]["id_str"])
after = datetime.now()

print "BSON Collection {0}:\n\t{1} unique users\n\tTime {2}".format(cfile,
    len(unique_users), after-before)

# Note: unique_users is a Python set (unique collection),
# and can be iterated over/processed like a list.