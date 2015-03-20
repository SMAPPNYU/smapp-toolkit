import re
import copy
import warnings
from datetime import timedelta
from collections import Counter
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

class MongoTweetCollection(object):
    """
    Collection object for performing queries and getting data out of a MongoDB collection 
    of tweets.

    Example:
    ########
    collection = MongoTweetCollection(localhost, 27017, 'test', 'tweets')
    collection.since(datetime(2014,1,1)).mentioning('bieber').count()

    collection.since(datetime(2014,1,1)).until(2014,2,1).mentioning('ebola').texts()
    """
    def __init__(self, address='localhost', port=27017, username=None, password=None,
                 dbname='test', metadata_collection='smapp_metadata', 
                 metadata_document='smapp-tweet-collection-metadata'):
        self._client = MongoClient(address, int(port))
        self._mongo_database = self._client[dbname]
        if username and password:
            self._mongo_database.authenticate(username, password)

        self._collection_metadata = self._mongo_database[metadata_collection].find_one({'document': metadata_document})
        
        # _mongo_collections list is a list of (collection_object, limit) pairs, in order to support good limit fctly
        self._mongo_collections = [(self._mongo_database[colname], 0) for colname in self._collection_metadata['tweet_collections']]
        self._queries = list()

        self._limit = 0
        self._sort = None

    def _regex_escape_and_concatenate(self, *terms):
        search = re.escape(terms[0])
        if len(terms) > 1:
            for term in terms[1:]:
                search += '|' + re.escape(term)
        return search

    def _copy_with_added_query(self, query):
        ret = copy.copy(self)
        ret._queries = copy.copy(self._queries)
        ret._queries.append(query)
        return ret

    def matching_regex(self, expr):
        return self._copy_with_added_query({'text': {'$regex': expr}})

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
        regex = re.compile(search, re.IGNORECASE, )
        return self._copy_with_added_query({field: regex})

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
        return self._copy_with_added_query({'coordinates.coordinates': {'$exists': True}})

    def non_geo_enabled(self):
        """
        Only return tweets that are NOT geo-tagged.
        """
        return self._copy_with_added_query({'coordinates.coordinates': {'$exists': False}})

    def since(self, since):
        """
        Only find tweets authored after a certain time. If no timezone is specified, UTC is assumed.
        Takes datetime.datetime object

        Example:
        ########
        from datetime import datetime

        collection.since(datetime(2014,10,1))
        """
        return self._copy_with_added_query({'timestamp': {'$gt': since}})

    def until(self, until):
        """
        Only find tweets authored before a certain time. If no timezone is specified, UTC is assumed.
        Takes datetime.datetime object

        Example:
        ########
        from datetime import datetime

        collection.until(datetime(2014,10,1))
        """
        return self._copy_with_added_query({'timestamp': {'$lt': until}})

    def language(self, *langs):
        """
        Only find tweets in certain languages. Goes by the 'lang' attribute in the tweet object.

        Example:
        ########

        collection.language('fr', 'de')
        """
        return self._copy_with_added_query({'lang': {'$in': langs}})

    def excluding_retweets(self):
        """
        Only find tweets that are not retweets.
        """
        return self._copy_with_added_query({'retweeted_status': {'$exists': False}})

    def only_retweets(self):
        "Only return retweets"
        return self._copy_with_added_query({'retweeted_status': {'$exists':True}})

    def sample(self, pct):
        """
        Sample *approximately* `pct` percent of the tweets in the database.
        Works by querying on a `random_number` field each tweet has assigned on insertion to database.
        Subsequent calls using the same `pct` will return the same tweets.

        Example:
        ########

        collection.sample(0.1).texts()
        """
        return self._copy_with_added_query({'random_number': {'$lt': pct}})

    def using_latest_collection_only(self):
        """
        Only apply query to the latest collection in the split-set.
        """
        ret = copy.copy(self)
        ret._mongo_collections = [self._mongo_collections[-1]]
        return ret

    def limit(self, count):
        """
        Only return `count` tweets from the collection. Note: this takes tweets from the
        beginning of the collection(s)

        Example:
        ########
        collection.limit(5).texts()
        """
        # Get copy of original object
        ret = copy.copy(self)
        ret._queries = copy.copy(self._queries)
        
        # Set new Object's mongo collections list to empty
        ret._mongo_collections = []

        # Iterate over old collections list, counting to get enough to satisfy limit.
        # Add collections that don't yet meet limit
        added_collection_count = 0
        for c, l in self._mongo_collections:
            c_count = c.find(limit=l).count(with_limit_and_skip=True)
            if count > added_collection_count + c_count:
                ret._mongo_collections.append((c, c_count))
                added_collection_count += c_count
                continue
            else:
                # count - added_collection_count is the number of tweets needed from
                # current collection to satisfy limit
                ret._mongo_collections.append((c, count - added_collection_count))
                break
        return ret

    def sort(self, field, direction=ASCENDING):
        """
        Order tweets by specified field in specified direction.

        Example:
        ########
        collection.order('timestamp', collection.DESCENDING).texts()
        """
        ret = copy.copy(self)
        ret._queries = copy.copy(self._queries)
        ret._sort = (field, direction)
        return ret

    def count(self):
        """
        The count of tweets in the collection matching all specified criteria.

        Example:
        ########

        collection.containing('peace').count()
        """
        return sum(col.find(self._query(), limit=lim).count(with_limit_and_skip=True) for col, lim in self._mongo_collections)

    def texts(self):
        """
        Return the tweet texts matching all specified criteria.

        Example:
        ########

        collection.since(datetime(2014,1,1)).texts()
        """
        return [tweet['text'] for tweet in self]



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
        unigrams = Counter()
        for tweet in self:
            tokens = get_cleaned_tokens(tweet["text"],
                                        keep_hashtags=hashtags,
                                        keep_mentions=mentions,
                                        rts=rts,
                                        mts=mts,
                                        https=https)
            unigrams.update(tokens)
        return unigrams.most_common(n)

    def top_bigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False):
        bigrams = Counter()
        for tweet in self:
            tokens = get_cleaned_tokens(tweet["text"],
                                        keep_hashtags=hashtags,
                                        keep_mentions=mentions,
                                        rts=rts,
                                        mts=mts,
                                        https=https)
            tweet_bigrams = get_ngrams(tokens, 2)
            bigrams.update(tweet_bigrams)
        return bigrams.most_common(n)

    def top_trigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False):
        trigrams = Counter()
        for tweet in self:
            tokens = get_cleaned_tokens(tweet["text"],
                                        keep_hashtags=hashtags,
                                        keep_mentions=mentions,
                                        rts=rts,
                                        mts=mts,
                                        https=https)
            tweet_trigrams = get_ngrams(tokens, 3)
            trigrams.update(tweet_trigrams)
        return trigrams.most_common(n)

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

    def _merge(self, a, b, path=None):
        "Merge dictionaries of dictionaries"
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self._merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a

    def _query(self):
        return reduce(self._merge, self._queries, {})

    def __iter__(self):
        if self._sort:
            return (tweet for collection, limit in self._mongo_collections for tweet in Cursor(collection, self._query(), limit=limit, sort=[self._sort]))
        else:
            return (tweet for collection, limit in self._mongo_collections for tweet in Cursor(collection, self._query(), limit=limit))

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
