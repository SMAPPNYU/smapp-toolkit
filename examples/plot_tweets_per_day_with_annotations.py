"""
This script shows how you can use smapp-toolkit to plot tweets per day
volume, with vertical lines for annotating events.

The example in this case uses the #mikebrown collection, and shows the high spike in
tweet volume following the ferguson grand jury decision not to indict Darran Wilson,
and how there was no similar spike following the similar decition on Daniel Pantaleo.

You are invited to plot this for the "EricGarner" collection, which will show the enormous
volume of tweets using #ericgarner following that second no-indictment decision.

@jonathanronen
"""

from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection
from matplotlib import pyplot as plt

start_time = datetime(2014, 12, 3, 20)

collection = MongoTweetCollection(
    address='REAL SERVER',
    port=27011,
    username='smapp_readOnly',
    password='REAL PASSWORD',
    dbname='IfTheyGunnedMeDown'
)

events = [
    (19,  'No indictment for Darren Wilson', 'bottom'), # nov 24
    (28, 'No indictment for Daniel Pantaleo', 'top'),  # dec 3
]

collection.tweets_per_day_with_annotations_figure(
    start=datetime(2014,11,5),
    num_steps=31,
    step_size=timedelta(days=1),
    alpha=.4,
    line_width=2.0,
    line_color='red',
    x_label_step=3,
    events=events)
