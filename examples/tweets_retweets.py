"""
Script makes figure of retweet propotion in the last week from the Hillary Clinton 2016 collection.

@jonathanronen 2015/6
"""

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection

plt.ion()

col = MongoTweetCollection('smapp.politics.fas.nyu.edu', 27011, 'smapp_readOnly', 'PASSWORD', 'USElection2016_Hillary')
plt.figure(12,12)
col.since(datetime.utcnow()-timedelta(days=7)).tweets_retweets_figure(show=False)
plt.title('Tweets and RT volume from Hillary 2016 collection')
plt.savefig('hillary_rts.png')