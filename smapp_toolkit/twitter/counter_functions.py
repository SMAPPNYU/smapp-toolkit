"""
Module contains functions to count top_things in collections of tweets.
"""

import pandas as pd
from collections import Counter
from smappPy.iter_util import get_ngrams
from smappPy.text_clean import get_cleaned_tokens
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

    # def top_urls(self, n=10):
    #     """
    #     See 'top_links()'. Same, but for only embedded links (not Tweet Media).
    #     """
    #     return pd.DataFrame(Counter([u for tweet in self for u in get_urls(tweet)]).most_common(n), columns=['url', 'count'])

    # def top_images(self, n=10):
    #     return pd.DataFrame(Counter([i for tweet in self for i in get_image_urls(tweet)]).most_common(n), columns=['image', 'count'])

    # def top_hashtags(self, n=10):
    #     return pd.DataFrame(Counter([h for tweet in self for h in [x.lower() for x in get_hashtags(tweet)]]).most_common(n), columns=['hashtag', 'count'])

    # def top_mentions(self, n=10):
    #     """
    #     Same as other top functions, except returns the number of unique (user_id, user_screen_name) pairs.
    #     """
    #     return pd.DataFrame(Counter([m for tweet in self for m in get_users_mentioned(tweet)]).most_common(n), columns=['mention', 'count'])

    # def top_user_locations(self, n=10, count_each_user_once=True):
    #     """
    #     Return top user location strings.

    #     If `count_each_user_once` is True, a user's location string is only considered
    #     once, regardless of how often the user appears in the collection.
    #     If False, a user's location string is counted multiple times.
    #     """
    #     return _top_user_locations(self, n, count_each_user_once)

    # def top_geolocation_names(self, n=10):
    #     """
    #     Return top location names from geotagged tweets. Place names come from twitter's "Places".
    #     """
    #     loc_counts = Counter(tweet['place']['full_name'] if 'place' in tweet and tweet['place'] is not None else None for tweet in self.geo_enabled())
    #     return pd.DataFrame(loc_counts.most_common(n), columns=['place name', 'count'])