"""
Script makes figure of retweet propotion in the last week from the Hillary Clinton 2016 collection.

@jonathanronen 2015/6
"""

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection

plt.ion()

col = MongoTweetCollection('smapp.politics.fas.nyu.edu', 27011, 'smapp_readOnly', 'PASSWORD', 'Sean_Hungary')
plt.figure(figsize=(12,12))
col.since(datetime(2015,6,10)).until(datetime(2015,6,11)).tweets_with_hashtags_figure(group_by='hours', xtick_format='%H', show=False)
plt.title('Tweets with hashtags volume for a day in the Hungary collection')
plt.savefig('hungary_hts.png')