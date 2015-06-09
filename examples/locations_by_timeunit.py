"""
Script demonstrates the "geolocation_names_per_day_figure" and "user_locations_per_day_figure" functionality.

@jonathanronen 2015/6
"""

from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection
import matplotlib.pyplot as plt

col = MongoTweetCollection('smapp.politics.fas.nyu.edu', 27011, 'smapp_readOnly', 'SECRET-PASSWORD', 'Britain_Geo')

col.geolocation_names_per_day_figure(start=datetime(2015,1,12,17,34), step_size=timedelta(minutes=10), num_steps=6, n_names=8, xtick_format='%H:%M')
plt.savefig('geolocation_names.png')

col.user_locations_per_day_figure(start=datetime(2015,1,12,17,34), step_size=timedelta(minutes=10), num_steps=6, n_names=8, xtick_format='%H:%M')
plt.savefig('user_locations.png')