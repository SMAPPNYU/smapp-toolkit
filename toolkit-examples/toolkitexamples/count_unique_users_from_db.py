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

db = "OccupyWallStreet"
collection = MongoTweetCollection(address="smapp.politics.fas.nyu.edu",
                                  port=27011,
                                  username="DATABASE_USERNAME_GOES_HERE",
                                  password="DATABASE_PASSWORD_GOES_HERE",
                                  dbname=db)

unique_users = {}
before = datetime.now()
for tweet in collection:
    unique_users.add(tweet["user"]["id_str"])
after = datetime.now()

print "DB Collection {0}:\n\t{1} unique users\n\tTime {2}".format(db,
    len(unique_users), after-before)

# Note: unique_users is a Python set (unique collection),
# and can be iterated over/processed like a list.
