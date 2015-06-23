import pandas as pd
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from smappPy.retweet import is_retweet
from smappPy.geo_tweet import is_geocoded
from smappPy.entities import contains_url, contains_image, contains_hashtag, contains_mention

import mongo_tweet_collection
from counter_functions import _top_user_locations, _top_unigrams, _top_bigrams, _top_trigrams, _top_links, _top_urls, \
    _top_images, _top_hashtags, _top_mentions, _top_geolocation_names, _counter_to_series, _language_counts


class Aggregator(object):
    """
    Aggregator class used to produce aggregate results grouped by time slice.
    Time slice can be 'days', 'hours', 'minutes', or 'seconds'. Iterates over collection, splitting by that time unit,
    and produces results for each of those splits.

    Usage example:
    ##############
        col = smapp_toolkit.twitter.BSONTweetCollection('tweets.bson') # or MongoTweetCollection()
        agg = smapp_toolkit.twitter.aggregator.Aggregator(col, 'hours')
        d = agg.top_user_locations(10)
    """

    def __init__(self, collection, time_unit):
        self._collection = collection
        self._time_unit = time_unit
        self._time_delta = timedelta(**{time_unit: 1})

    def _get_start_time(self):
        for t in self._collection:
            start_time = t['timestamp']
            break
        if self._time_unit == 'days':
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self._time_unit == 'hours':
            start_time = start_time.replace(minute=0, second=0, microsecond=0)
        elif self._time_unit == 'minutes':
            start_time = start_time.replace(second=0, microsecond=0)
        elif self._time_unit == 'seconds':
            start_time = start_time.replace(microsecond=0)
        return start_time

    def __iter__(self):
        if isinstance(self._collection, mongo_tweet_collection.MongoTweetCollection):
            return self._mongo_splits()
        else:
            return self._splits()

    def _splits(self):
        start_time = self._get_start_time()

        it = iter(self._collection)
        d = dict()
        d['t'] = next(it)
        d['stop'] = False

        def chunk(until):
            while d['t']['timestamp'] < until:
                yield d['t']
                try:
                    d['t'] = next(it)
                except StopIteration:
                    d['stop'] = True
                    raise StopIteration()
            raise StopIteration()

        while True:
            ch = chunk(start_time + self._time_delta)
            yield (start_time, ch)
            if d['stop']:
                raise StopIteration()
            start_time = start_time + self._time_delta

    def _mongo_splits(self):
        if not self._collection._get_until():
            raise Exception("Cannot time-split on a MongoTweetCollection without calling until()")
        start_time = self._get_start_time()
        end_time = self._collection._get_until()

        while start_time < end_time:
            tmpcol = self._collection._copy()
            tmpcol._override_since(start_time)
            tmpcol._override_until(start_time+self._time_delta)
            yield (start_time, tmpcol)
            start_time = start_time + self._time_delta

    def grouped_result(self, callable_, *args, **kwargs):
        results = dict()
        for t, split in self:
            results[t] = callable_(split, *args, **kwargs)
        return pd.concat(results, axis=1).T

    def grouped_top_n_result(self, n, callable_):
        res = self.grouped_result(callable_)
        su = res.sum()
        su.sort(ascending=False)
        return res[list(su[:n].index)]

    def top_user_locations(self, n=10):
        return self.grouped_top_n_result(n, _top_user_locations)

    def top_unigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
        return self.grouped_top_n_result(n, lambda col: _top_unigrams(col, n=None, hashtags=hashtags, mentions=mentions, rts=rts, mts=mts, https=https, stopwords=stopwords))

    def top_bigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
        return self.grouped_top_n_result(n, lambda col: _top_bigramss(col, n=None, hashtags=hashtags, mentions=mentions, rts=rts, mts=mts, https=https, stopwords=stopwords))

    def top_trigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
        return self.grouped_top_n_result(n, lambda col: _top_trigrams(col, n=None, hashtags=hashtags, mentions=mentions, rts=rts, mts=mts, https=https, stopwords=stopwords))

    def top_links(self, n=10):
        return self.grouped_top_n_result(n, _top_links)

    def top_urls(self, n=10):
        return self.grouped_top_n_result(n, _top_urls)

    def top_images(self, n=10):
        return self.grouped_top_n_result(n, _top_images)

    def top_hashtags(self, n=10):
        return self.grouped_top_n_result(n, _top_hashtags)

    def top_mentions(self, n=10):
        return self.grouped_top_n_result(n, _top_mentions)

    def top_geolocation_names(self, n=10):
        return self.grouped_top_n_result(n, _top_geolocation_names)

    def entities_counts(self, urls=True, images=True, hashtags=True, mentions=True, geo_enabled=True, retweets=True):
        def props(collection, urls=urls, images=images, hashtags=hashtags, mentions=mentions, geo_enabled=geo_enabled, retweets=retweets):
            res = Counter()
            for tweet in collection:
                res['_total'] += 1
                if urls and contains_url(tweet):
                    res['url'] += 1
                if images and contains_image(tweet):
                    res['image'] += 1
                if hashtags and contains_hashtag(tweet):
                    res['hashtag'] += 1
                if mentions and contains_mention(tweet):
                    res['mention'] += 1
                if geo_enabled and is_geocoded(tweet):
                    res['geo_enabled'] += 1
                if retweets and is_retweet(tweet):
                    res['retweet'] += 1
            return _counter_to_series(res)
        return self.grouped_result(props)

    def language_counts(self, langs):
        return self.grouped_result(_language_counts, langs=langs)

    def count(self):
        if isinstance(self._collection, mongo_tweet_collection.MongoTweetCollection):
            return self.grouped_result(lambda it: pd.Series(it.count(), index=['count']))
        else:
            return self.grouped_result(lambda it: pd.Series(sum(1 for e in it), index=['count']))
