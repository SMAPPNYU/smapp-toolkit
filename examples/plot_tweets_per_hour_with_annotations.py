"""
Demonstrate how to plot tweets per hour with annotation lines,
using the "data-then-plot" framework (the smapp_toolkit.plotting module)

@jonathanronen 2015/6
"""

import pytz
import getpass
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection
from smapp_toolkit.plotting import line_with_annotations

# Connect to database
print("Enter password for 'smapp_readOnly'")
col = MongoTweetCollection('smapp.politics.fas.nyu.edu', 27011, 'smapp_readOnly', getpass.getpass(), 'USElection2016_DTrumps')

# Set start time to a full day in the New York time zone
start_time = datetime(2015,6,21).replace(tzinfo=pytz.timezone('America/New_York')).astimezone(pytz.UTC).replace(tzinfo=None)
end_time = start_time + timedelta(days=1)

# Get the tweets per day data from the database
data = col.since(start_time).until(end_time).group_by('hours').count()

# Define the events to plot horizontal lines for
events = [
      (datetime(2015,6,21,10), 'Sunrise', 'top'),
      (datetime(2015,6,21,22), 'Sunset', 'bottom')
    ]

# Make plot
plt.figure(figsize=(10,6))
line_with_annotations(data, events, x_tick_timezone='America/New_York', x_tick_date_format='%H:%M')
plt.title('Tweets mentioning Donald Trump\non 2015-6-21', fontsize=24)
plt.tight_layout()
plt.savefig('a_day_in_a_life.png')