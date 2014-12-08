import re
import copy
import twitter_figure_makers
from datetime import timedelta
from pymongo.cursor import Cursor
from pymongo import MongoClient, ASCENDING, DESCENDING
from smappPy.unicode_csv import UnicodeWriter

class MongoTweetCollection(object):
    """
    Collection object for performing queries and getting data out of a MongoDB collection of tweets.

    Example:
    ########
    collection = MongoTweetCollection(localhost, 27017, 'test', 'tweets')
    collection.since(datetime(2014,1,1)).mentioning('bieber').count()

    collection.since(datetime(2014,1,1)).until(2014,2,1).mentioning('ebola').texts()
    """
    def __init__(self, address='localhost', port=27017, dbname='test', metadata_collection='smapp_metadata', metadata_document='smapp-tweet-collection-metadata', username=None, password=None):
        self._client = MongoClient(address, int(port))
        self._mongo_database = self._client[dbname]
        if username and password:
            self._mongo_database.authenticate(username, password)

        self.collection_metadata = self._mongo_database[metadata_collection].find_one({'document': metadata_document})
        self._mongo_collections = [self._mongo_database[colname]
            for colname in self.collection_metadata['tweet_collections']]
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
        Only return tweets that are geo-tagged.
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
        Only return `count` tweets from the collection.

        Example:
        ########
        collection.limit(5).texts()
        """
        ret = copy.copy(self)
        ret._queries = copy.copy(self._queries)
        ret._limit = count
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
        return sum(col.find(self._query()).count() for col in self._mongo_collections)

    def texts(self):
        """
        Return the tweet texts matching all specified criteria.

        Example:
        ########

        collection.since(datetime(2014,1,1)).texts()
        """
        return [tweet['text'] for tweet in self]

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
            return (tweet for collection in self._mongo_collections for tweet in Cursor(collection, self._query(), limit=self._limit).sort(*self._sort))
        else:
            return (tweet for collection in self._mongo_collections for tweet in Cursor(collection, self._query(), limit=self._limit))

    def __getattr__(self, name):
        if name.endswith('_containing'):
            field_name = '.'.join(name.split('_')[:-1])
            def containing_method(*terms):
                return self.field_containing(field_name, *terms)
            return containing_method
        elif name.endswith('_figure'):
            figure_name = '_'.join(name.split('_')[:-1])
            method = twitter_figure_makers.__getattribute__(figure_name)
            def figure_method(*args, **kwargs):
                return method(self, *args, **kwargs)
            return figure_method
        else:
            return object.__getattribute__(self, name)
