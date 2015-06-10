import pandas as pd
from collections import Counter
from datetime import datetime, timedelta
from counter_functions import _top_user_locations, _top_unigrams, _top_bigrams, _top_trigrams, _top_links


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

    def grouped_result(self, callable_):
        results = dict()
        for t, split in self._splits():
            results[t] = callable_(split)
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
