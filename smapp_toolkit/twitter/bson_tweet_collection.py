import os
import re
import copy
import pytz
from random import random
from datetime import datetime
from bson import decode_file_iter
from base_tweet_collection import BaseTweetCollection

class BSONTweetCollection(BaseTweetCollection):
    def __iter__(self):
        with open(self._filename, 'rb') as f:
            i = 1
            for tweet in decode_file_iter(f):
                if self._limit and i > self._limit:
                    raise StopIteration
                if all(func(tweet) for func in self._filter_functions):
                    i += 1
                    yield tweet

    """
    Collection object for performing queries and getting data out of a BSON file 
    of tweets.

    Example:
    ########
    collection = BSONTweetCollection("/home/smapp/data/RawTweets.bson")
    """
    def __init__(self, filename):
        self._filename = filename
        if not os.path.isfile(filename):
            raise IOError("File not found")
        self._filter_functions = list()
        self._limit = None
        for tweet in self:
            break
        if tweet['timestamp'].tzinfo:
            self._has_tzinfo = True
        else:
            self._has_tzinfo = False

    def __repr__(self, ):
        return "BSON Tweet Collection (source, # filters, limit): {0}, {1}, {2}".format(
            self._filename, len(self._filter_functions), self._limit)

    def _copy_with_added_filter(self, filter_function):
        ret = copy.copy(self)
        ret._filter_functions = copy.copy(self._filter_functions)
        ret._filter_functions.append(filter_function)
        return ret

    def matching_regex(self, expr):
        """
        Select tweets where the text matches a regex

        Example:
        ########
        collection.matching_regex(r'@[A-Za-z]{1,3}')
        # will return tweets with mentions of users with short handles
        """
        ex = re.compile(expr, re.IGNORECASE | re.UNICODE)
        def regex_filter(tweet):
            return ex.search(tweet['text'])
        return self._copy_with_added_filter(regex_filter)

    def field_containing(self, field, *terms):
        """
        Select tweets where `field` contains one of `terms`.

        Example:
        ########
        collection.field_containing('user.description', 'python', 'data', 'analysis', 'mongodb')
        # will return tweets where the user has any of the terms 'python', 'data', 'analysis', 'mongodb'
        # in their description.
        """
        search = self._regex_escape_and_concatenate(*terms)
        regex = re.compile(search, re.IGNORECASE | re.UNICODE)
        def field_contains_filter(tweet):
            to_search = self._recursive_read(tweet, field)
            return regex.search(to_search)
        return self._copy_with_added_filter(field_contains_filter)

    def geo_enabled(self):
        """
        Only return tweets that are geo-tagged.
        """
        def geo_enabled_filter(tweet):
            return "coordinates" in tweet and \
                tweet["coordinates"] is not None and \
                "coordinates" in tweet["coordinates"]
        return self._copy_with_added_filter(geo_enabled_filter)

    def non_geo_enabled(self):
        """
        Only return tweets that are NOT geo-tagged.
        """
        def non_geo_enabled_filter(tweet):
            return 'coordinates' not in tweet or \
                tweet['coordinates'] is None or \
                'coordinates' not in tweet['coordinates']
        return self._copy_with_added_filter(non_geo_enabled_filter)

    def since(self, since):
        """
        Only find tweets authored after a certain time. If no timezone is specified, UTC is assumed.
        Takes datetime.datetime object

        Example:
        ########
        from datetime import datetime

        collection.since(datetime(2014,10,1))
        """
        if self._has_tzinfo and since.tzinfo is None:
            since = since.replace(tzinfo=pytz.UTC)

        def since_filter(tweet):
            # Should this use parsedate(),
            # for cases where we don't have proper 'timestamp's?
            return tweet['timestamp'] > since
        return self._copy_with_added_filter(since_filter)

    def until(self, until):
        """
        Only find tweets authored before a certain time. If no timezone is specified, UTC is assumed.
        Takes datetime.datetime object

        Example:
        ########
        from datetime import datetime

        collection.until(datetime(2014,10,1))
        """
        if self._has_tzinfo and until.tzinfo is None:
            until = until.replace(tzinfo=pytz.UTC)

        def until_filter(tweet):
            # Should this use parsedate(),
            # for cases where we don't have proper 'timestamp's?
            return tweet['timestamp'] < until
        return self._copy_with_added_filter(until_filter)

    def language(self, *langs):
        """
        Only find tweets in certain languages. Goes by the 'lang' attribute in the tweet object.

        Example:
        ########

        collection.language('fr', 'de')
        """
        def lang_filter(tweet):
            return tweet['lang'] in langs
        return self._copy_with_added_filter(lang_filter)


    def excluding_retweets(self):
        """
        Only find tweets that are not retweets.
        """
        def excluding_retweets_filter(tweet):
            return 'retweeted_status' not in tweet
        return self._copy_with_added_filter(excluding_retweets_filter)


    def only_retweets(self):
        "Only return retweets"
        def only_retweets_filter(tweet):
            return 'retweeted_status' in tweet
        return self._copy_with_added_filter(only_retweets_filter)

    def sample(self, pct):
        """
        Sample *approximately* `pct` percent of the tweets in the database.
        Works by querying on a `random_number` field each tweet has assigned on insertion to database.
        Subsequent calls using the same `pct` will return the same tweets.

        Example:
        ########

        collection.sample(0.1).texts()
        """
        def sample_filter(tweet):
            return random() < pct
        return self._copy_with_added_filter(sample_filter)

    def limit(self, count):
        """
        Only return `count` tweets from the collection. Note: this takes tweets from the
        beginning of the collection(s)

        Example:
        ########
        collection.limit(5).texts()
        """
        ret = copy.copy(self)
        ret._limit = count
        return ret

    def time_range(self, ):
        """
        Iterates over collection to find timestamp of first and last tweets. Because there
        is no guarantee of order, must check each timestamp.
        """
        min_date = datetime.max
        max_date = datetime.min
        for tweet in self:
            if tweet["timestamp"] < min_date:
                min_date = tweet["timestamp"]
            if tweet["timestamp"] > max_date:
                max_date = tweet["timestamp"]
        return (min_date, max_date)

    def sort(self, field, direction=1):
        raise NotImplementedError("Sort not implemented for BSON collections (inefficient)")

    def count(self):
        """
        The count of tweets in the collection matching all specified criteria.

        Example:
        ########

        collection.containing('peace').count()
        """
        return sum(1 for t in self)
