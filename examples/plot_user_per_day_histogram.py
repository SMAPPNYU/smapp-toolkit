"""
Script makes users-per-day histogram going N days back.

Usage:
    python plot_user_per_day_histograms.py -s smapp.politics.fas.nyu.edu -p 27011 -u smapp_readOnly -w SECRETPASSWORD -d USElection2016Hillary --days 10 --output-file hillary.png

@jonathanronen 2015/4
"""

import pytz
import argparse
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timedelta
from smapp_toolkit.twitter import MongoTweetCollection

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', default='smapp.politics.fas.nyu.edu', help="Mongodb server address ['smapp.politics.fas.nyu.edu]")
    parser.add_argument('-p', '--port', type=int, default=27011, help='Mongodb server port [27011]')
    parser.add_argument('-u', '--user', help='Mongodb username [None]')
    parser.add_argument('-w', '--password', help='Mongodb password [None')
    parser.add_argument('-d', '--database', help='Mongodb database name [None]')
    parser.add_argument('--days', default=7, help='How many days to go back [7]')
    parser.add_argument('--timezone', default='America/New_York', help='Time zone to consider [America/New_York]')
    parser.add_argument('--output-file', default='histogram.png', help='Output file [histogram.png]')

    args = parser.parse_args()
    print("Generating avg tweets/user/day histogram for {}".format(args.database))

    TIMEZONE = pytz.timezone(args.timezone)
    print("Days will be split according to time zone {}".format(args.timezone))

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=TIMEZONE)
    n_days_ago = today - timedelta(days=args.days)
    print("The period being considered is {} to {}".format(
        n_days_ago.strftime('%Y-%m-%d'),
        today.strftime('%Y-%m-%d')))

    print("Connecting to database")
    collection = MongoTweetCollection(args.server, args.port, args.user, args.password, args.database)

    ntweets = collection.since(n_days_ago).until(today).count()
    print("Considering {} tweets".format(ntweets))

    userids = set()
    counts = dict()
    for i in range(args.days):
        day_counts = defaultdict(lambda: 0)
        day_start = n_days_ago + i*timedelta(days=1)
        day_end   = n_days_ago + (i+1)*timedelta(days=1)
        print("Counting for {}".format(day_start.strftime('%Y-%m-%d')))
        for tweet in collection.since(day_start).until(day_end):
            day_counts[tweet['user']['id']] += 1
            userids.add(tweet['user']['id'])
        counts[day_start] = day_counts
    print("Done getting data from database.")

    #### AVERAGE TWEETS PER DAY COUNTS (how many users tweeted x times per day on average)
    user_avg_daily_tweets = { user: np.mean([counts[day][user] for day in counts]) for user in userids }

    fig = plt.figure(figsize=(10,8))
    plt.subplot(212)
    counts = np.log(user_avg_daily_tweets.values())
    bins = np.linspace(0, max(counts), max(counts)*10+1)
    plt.hist(counts, bins, color='r', alpha=.6)
    plt.ylabel('Num users')
    plt.xlabel('log(avg tweets per day)')

    plt.subplot(211)
    plt.title('Average number of tweets per day for users\n{}\n {} to {}'.format(
        args.database,
        n_days_ago.strftime('%Y-%m-%d'),
        today.strftime('%Y-%m-%d')))
    counts = np.array(user_avg_daily_tweets.values())
    bins = np.linspace(0, max(counts), max(counts)+1)
    plt.hist(counts, bins, color='r', alpha=.6)
    plt.ylabel('Num users')
    plt.xlabel('avg tweets per day')

    plt.tight_layout()
    plt.savefig(args.output_file)
    print("Done.")
