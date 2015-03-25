import re
import copy
import warnings
from datetime import timedelta
from pymongo.cursor import Cursor
from pymongo import MongoClient, ASCENDING, DESCENDING
from base_tweet_collection import BaseTweetCollection

class MongoTweetCollection(BaseTweetCollection):
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

    def __repr__(self, ):
        return "Mongo Tweet Collection (DB, # filters, limit): {0}, {1}, {2}".format(
            "{0}:{1}/{2}".format(self._client.host, self._client.port, self._mongo_database.name),
            len(self._queries),
            self._limit)

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

        # Set self limit variable (for info only)
        ret._limit = count
        
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

    def time_range(self, ):
        """
        Returns a tuple: (first_tweet_date, last_tweet_date)

        Example:
        ########
        collection.time_range()
        >> (datetime.datetime(2014, 10, 8, 12, 51), datetime.datetime(2015, 3, 24, 5, 32))
        """
        first = list(self.sort("timestamp", direction=ASCENDING).limit(1))[0]["timestamp"]
        last = list(self.sort("timestamp", direction=DESCENDING).limit(1))[0]["timestamp"]
        return (first, last)

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





