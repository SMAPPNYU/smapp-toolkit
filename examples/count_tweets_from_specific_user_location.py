"""
This script counts all tweets from the Ukraine collection sent in the past 12 hours where the user's
specified 'location' field has one of the following words in it:
 - Kiev
 - Kyiv
 - Kiew
"""

from smapp_toolkit.twitter import MongoTweetCollection
from datetime import datetime, timedelta

collection = MongoTweetCollection(address='WRITE REAL DATABASE ADDRESS HERE',
                                  port=27011,
                                  username='smapp_readOnly',
                                  password='WRITE REAL PASSWORD HERE',
                                  dbname='Ukraine')

twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)

print "Matched {} tweets.".format(collection.user_location_containing('kiev', 'kiew', 'kyiv').since(twelve_hours_ago).count())