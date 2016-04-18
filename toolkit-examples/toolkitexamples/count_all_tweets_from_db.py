"""
Simple script to count all tweets in a given collection.
Examples for MongoTweetCollection and BSONTweetCollection

Using these in non-example code, paramterize and configure
more appropriately (these examples use globals and other 
bad practices)

Note: time printing is not super reliable, better to use timeit
or profiler.
"""

from datetime import datetime
from smapp_toolkit.twitter import MongoTweetCollection, BSONTweetCollection

# create a collection on which to
# query tweets from a database connection
# or use a BSON file as a backend
db = "OccupyWallStreet"
db_collection = MongoTweetCollection(address="smapp.politics.fas.nyu.edu",
                                     port=27011,
                                     username="DATABASE_USERNAME_GOES_HERE",
                                     password="DATABASE_PASSWORD_GOES_HERE",
                                     dbname=db)

# For DB-based collections, operation is in constant time:
before = datetime.now()

# count the actual number tweets
db_count = db_collection.count()

# grab the new date
after  = datetime.now()

# print some output telling us about how long the query took.
print "DB Collection {0}\n\tcount {1}, time {2}".format(db, db_count, after-before)
