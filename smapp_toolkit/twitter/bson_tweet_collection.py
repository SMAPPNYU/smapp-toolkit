import re
import copy
import warnings
from random import random
from datetime import timedelta
from collections import Counter
from bson import decode_file_iter
from pymongo.cursor import Cursor
from pymongo import MongoClient, ASCENDING, DESCENDING
from smappPy.iter_util import get_ngrams
from smappPy.unicode_csv import UnicodeWriter
from smappPy.text_clean import get_cleaned_tokens

try:
    import twitter_figure_makers
    NO_FIGURES = False
except:
    warnings.warn("smapp-toolkit: Missing some graphics packages. Making figures won't work.\n")
    NO_FIGURES = True

class BSONTweetCollection(object):
    """
    Collection object for performing queries and getting data out of a BSON file 
    of tweets.

    Example:
    ########
    
    """
    def __init__(self, filename):
        self._filename = filename
        if not os.path.isfile(filename):
            raise IOError("File not found")
        self._filter_functions = list()
        self._limit = None


    def _copy_with_added_filter(self, filter_function):
        ret = copy.copy(self)
        ret._filter_functions = copy.copy(self._filter_functions)
        ret._filter_functions.append(filter_function)
        return ret

    def _regex_escape_and_concatenate(self, *terms):
        search = re.escape(terms[0])
        if len(terms) > 1:
            for term in terms[1:]:
                search += '|' + re.escape(term)
        return search

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
            return ex.search(tweet[field])
        return self._copy_with_added_filter(field_contains_filter)

    def containing(self, *terms):
        """
        Only find tweets containing certain terms.
        Terms are OR'd, so that

        collection.containing('penguins', 'antarctica')

        will return tweets containing either 'penguins' or 'antarctica'.
        """
        return self.field_containing('text', *terms)

    def user_location_containing(self, *names):
        """
        Only find tweets where the user's `location` field contains certain terms.
        Terms are ORed, so that

        collection.user_location_containing('chile', 'antarctica')

        will return tweets with user location containing either 'chile' or 'antarctica'.
        """
        return self.field_containing('user.location', *names)

    def geo_enabled(self):
        """
        Only return tweets that are geo-tagged.
        """
        def geo_enabled_filter(tweet):
            return 'coordinates' in tweet and 'coordinates' in tweet['coordinates']
        return self._copy_with_added_filter(geo_enabled_filter)


    def non_geo_enabled(self):
        """
        Only return tweets that are NOT geo-tagged.
        """
        def non_geo_enabled_filter(tweet):
            return 'coordinates' not in tweet or 'coordinates' not in tweet['coordinates']
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
        self._limit = count

    def sort(self, field, direction=ASCENDING):
        raise NotImplementedError("Sort not implemented for BSON collections")

    def count(self):
        """
        The count of tweets in the collection matching all specified criteria.

        Example:
        ########

        collection.containing('peace').count()
        """
        return sum(1 for t in self)

    def texts(self):
        """
        Return the tweet texts matching all specified criteria.

        Example:
        ########

        collection.since(datetime(2014,1,1)).texts()
        """
        return [tweet['text'] for tweet in self]


    def _top_ngrams(self, ngram, n, hashtags, mentions, rts, mts, https):
        counts = Counter()
        for tweet in self:
            tokens = get_cleaned_tokens(tweet["text"],
                                        keep_hashtags=hashtags,
                                        keep_mentions=mentions,
                                        rts=rts,
                                        mts=mts,
                                        https=https)
            ngrams = get_ngrams(tokens, ngram)
            counts.update(tokens)
        return counts.most_common(n)


    def top_unigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False):
        """
        Return the top 'n' unigrams (tokenized words) in the collection.
        Warning: may take a while, as it has to iterate over all tweets in collection.
        Use with a limit for best (temporal) results.
        
        'hastags' and 'mentions' instruct the tokenizer to not remove hashtag 
        and mention symbols when breaking words into tokens (all other non-alphanumeric + 
        underscore characters are discarded). When set to True, this will differentiate
        between the terms "#MichaelJackson" and "MichaelJackson" (two different tokens).
        When False, these terms will become the same token, "MichaelJackson"

        'rts', 'mts', and 'https' instruct the tokenizer to drop the following tokens,
        respectively:
            - "rt" only
            - "mt" only
            - any token containing the substring "http"
        """
        return self._top_ngrams(1, **kwargs)

    def top_bigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False):
        return self._top_ngrams(2, **kwargs)

    def top_trigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False):
        return self._top_ngrams(3, **kwargs)

    def top_links(self, n=10):
        raise NotImplementedError()

    def top_images(self, n=10):
        raise NotImplementedError()

    def top_hashtags(self, n=10):
        raise NotImplementedError()

    def top_mentions(self, n=10):
        raise NotImplementedError()


    COLUMNS = ['id_str', 'user.screen_name', 'timestamp', 'text']
    def _make_row(self, tweet, columns=COLUMNS):
        row = list()
        for col_name in columns:
            path = col_name.split('.')
            try:
                value = tweet[path.pop(0)]
                for p in path:
                    if isinstance(value, list):
                        value = value[int(p)]
                    else:
                        value = value[p]
            except:
                value = ''
            row.append(u','.join(unicode(v) for v in value) if isinstance(value, list) else unicode(value))
        return row

    def dump_csv(self, filename, columns=COLUMNS):
        """
        Dumps the matching tweets to a CSV file specified by `filename`.
        The default columns are ['id_str', 'user.screen_name', 'timestamp', 'text'].
        Columns are specified by their path in the tweet dictionary, so that
            'user.screen_name' will grab tweet['user']['screen_name']

        Example:
        ########
        collection.since(one_hour_ago).dump_csv('my_tweets.csv', columns=['timestamp', 'text'])
        """
        with open(filename, 'w') as outfile:
            writer = UnicodeWriter(outfile)
            writer.writerow(columns)
            for tweet in self:
                writer.writerow(self._make_row(tweet, columns))

    def __iter__(self):
        with open(self._filename, 'rb') as f:
            i = 0
            for tweet in decode_file_iter(f):
                if self._limit and i > self._limit:
                    raise StopIteration
                if all(filter_fnc(tweet) for filter_fnc in funs):
                    i += 1
                    yield tweet

    def __getattr__(self, name):
        if name.endswith('_containing'):
            field_name = '.'.join(name.split('_')[:-1])
            def containing_method(*terms):
                return self.field_containing(field_name, *terms)
            return containing_method
        elif name.endswith('_figure') and not NO_FIGURES:
            figure_name = '_'.join(name.split('_')[:-1])
            method = twitter_figure_makers.__getattribute__(figure_name)
            def figure_method(*args, **kwargs):
                return method(self, *args, **kwargs)
            return figure_method
        else:
            return object.__getattribute__(self, name)
