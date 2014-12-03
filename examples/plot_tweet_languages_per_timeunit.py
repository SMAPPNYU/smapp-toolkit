"""
This script shows how you can use smapp-toolkit to plot tweets languages by time unit.
For the purpose of demonstration, we'll plot english and spanish tweets about Ebola by minute for one hour
on December 3 2014.

@jonathanronen
"""

from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection

start_time = datetime(2014, 12, 3, 20)

collection = MongoTweetCollection(
    address='WRITE REAL DATABASE ADDRESS HERE',
    port=27011,
    username='smapp_readOnly',
    password='WRITE REAL PASSWORD HERE',
    dbname='Ebola')
)


collection.languages_per_day_figure(
    start=start_time,
    step_size=timedelta(minutes=1),
    num_steps=60,
    languages=['en', 'es', 'other'],
    language_colors=['red', 'royalblue', 'grey'])