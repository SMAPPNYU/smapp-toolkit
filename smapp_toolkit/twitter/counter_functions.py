"""
Module contains functions to count top_things in collections of tweets.
"""

import pandas as pd
from collections import Counter
from smappPy.iter_util import get_ngrams
from smappPy.text_clean import get_cleaned_tokens
from smappPy.entities import get_users_mentioned, get_hashtags
from smappPy.entities import get_urls, get_links, get_image_urls

def _counter_to_series(counter, n=None):
    if len(counter) < 1:
        return pd.Series()
    if n:
        names, counts = zip(*counter.most_common(n))
    else:
        names, counts = zip(*counter.items())
    return pd.Series(counts, index=names)

def _top_user_locations(collection, n=None, count_each_user_once=True):
    users = set()
    loc_counts = Counter()
    for tweet in collection:
        if tweet["user"]["id"] in users and count_each_user_once:
            continue
        users.add(tweet["user"]["id"])
        if tweet["user"]["location"]:
            loc_counts[tweet["user"]["location"]] += 1
    return _counter_to_series(loc_counts, n)

def _top_ngrams(collection, ngram, n, hashtags, mentions, rts, mts, https, stopwords):
    counts = Counter()
    for tweet in collection:
        tokens = get_cleaned_tokens(tweet["text"],
                                    keep_hashtags=hashtags,
                                    keep_mentions=mentions,
                                    rts=rts,
                                    mts=mts,
                                    https=https,
                                    stopwords=stopwords)
        ngrams = get_ngrams(tokens, ngram)
        counts.update(' '.join(e) for e in ngrams)
    return _counter_to_series(counts, n)

def _top_unigrams(collection, n=None, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
    return _top_ngrams(collection, 1, n, hashtags, mentions, rts, mts, https, stopwords)

def _top_bigrams(collection, n=None, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
    return _top_ngrams(collection, 2, n, hashtags, mentions, rts, mts, https, stopwords)

def _top_trigrams(collection, n=None, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
    return _top_ngrams(collection, 3, n, hashtags, mentions, rts, mts, https, stopwords)

def _top_links(collection, n=None):
    counter = Counter([l for tweet in collection for l in get_links(tweet)])
    return _counter_to_series(counter, n)

def _top_urls(collection, n=None):
    counter = Counter([u for tweet in collection for u in get_urls(tweet)])
    return _counter_to_series(counter, n)

def _top_images(collection, n=10):
    counter = Counter([i for tweet in collection for i in get_image_urls(tweet)])
    return _counter_to_series(counter, n)

def _top_hashtags(collection, n=10):
    counter = Counter([h for tweet in collection for h in [x.lower() for x in get_hashtags(tweet)]])
    return _counter_to_series(counter, n)

def _top_mentions(collection, n=10):
    counter = Counter([m for tweet in collection for m in get_users_mentioned(tweet)])
    return _counter_to_series(counter, n)

def _top_geolocation_names(collection, n=10):
    loc_counts = Counter(tweet['place']['full_name'] if 'place' in tweet and tweet['place'] is not None else None for tweet in collection)
    return _counter_to_series(loc_counts, n)
