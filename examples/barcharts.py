"""
Script demonstrates plotting two histograms from the Ebola collection:
one of total tweets per minute for 1 hour on november 1st,
the other of only tweets containing the word "death" in that same hour.

@jonathanronen
"""

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection

start_time = datetime(2014, 12, 3, 20)

collection = MongoTweetCollection(
    address='REAL SERVER HERE',
    port=27011,
    username='smapp_readOnly',
    password='REAL PASSWORD HERE',
    dbname='Ebola'
)

start_time = datetime(2014,11,1)
plt.figure()

plt.subplot(211)
bins, counts = collection.histogram_figure(
    start_time,
    step_size=timedelta(minutes=1),
    num_steps=60,
    show=False)
plt.title('All tweets')

plt.subplot(212)
bins, counts = collection.containing('death').histogram_figure(
    start_time,
    step_size=timedelta(minutes=1),
    num_steps=60,
    show=False)
plt.title('Tweets containing "death"')
plt.show()
