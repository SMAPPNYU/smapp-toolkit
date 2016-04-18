from datetime import datetime
from smapp_toolkit.twitter import MongoTweetCollection, BSONTweetCollection

# create a collection on which
# to query tweets from a bson file
# or hookup a MongoCollection
cfile = "/scratch/smapp/obama_romney/obama_romney_tweets_8_15.bson"
bson_collection = BSONTweetCollection(cfile)

# get tweets FROM the start date
start = datetime(2012, 1, 1)

# get tweets UNTIL the end date
end = datetime(2012,1, 8)

before = datetime.now()

# get the tweets since the start date until the end
db_count = db_collection.since(start).until(end).count()

after = datetime.now()

# print a pretty message telling us how long it took.
print "DB Collection {0}\n\ton range {1}-{2},\n\tcount {3}, time {4}".format(db,
    start, end, db_count, after-before)
