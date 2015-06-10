"""
Module contains functions to count top_things in collections of tweets.
"""

import pandas as pd
from collections import Counter

def _top_user_locations(iterable, n=None, count_each_user_once=True):
    users = set()
    loc_counts = Counter()
    for tweet in iterable:
        if tweet["user"]["id"] in users and count_each_user_once:
            continue
        users.add(tweet["user"]["id"])
        if tweet["user"]["location"]:
            loc_counts[tweet["user"]["location"]] += 1
    if len(loc_counts) < 1:
        return pd.Series()
    if n:
        names, counts = zip(*loc_counts.most_common(n))
    else:
        names, counts = zip(*loc_counts.items())
    return pd.Series(counts, index=names)
