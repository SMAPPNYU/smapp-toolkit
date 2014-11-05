import re
import copy
from datetime import timedelta
from pymongo import MongoClient


class MongoTweetCollection:
    """
    Collection object for performing queries and getting data out of a MongoDB collection of tweets.

    Example:
    ########
    collection = MongoTweetCollection(localhost, 27017, 'test', 'tweets')
    collection.since(datetime(2014,1,1)).mentioning('bieber').count()

    collection.since(datetime(2014,1,1)).until(2014,2,1).mentioning('ebola').texts()
    """
    def __init__(self, address='localhost', port=27017, dbname='test', metadata_collection='smapp_metadata', metadata_document='smapp-tweet-collection-metadata', username=None, password=None):
        self._client = MongoClient(address, port)
        self._mongo_database = self._client[dbname]
        if username and password:
            self._mongo_database.authenticate(username, password)

        self.collection_metadata = self._mongo_database[metadata_collection].find_one({'document': metadata_document})
        self._mongo_collections = [self._mongo_database[colname]
            for colname in self.collection_metadata['tweet_collections']]
        self._queries = list()

    def _copy_with_added_query(self, query):
        ret = copy.copy(self)
        ret._queries = copy.copy(self._queries)
        ret._queries.append(query)
        return ret

    def matching_regex(self, expr):
        return self._copy_with_added_query({'text': {'$regex': expr}})

    def containing(self, *terms):
        """
        Only find tweets containing certain terms.
        Terms are OR'd, so that

        collection.containing('penguins', 'antarctica')

        will return tweets containing either 'penguins' or 'antarctica'.
        """
        search = re.escape(terms[0])
        if len(terms) > 1:
            for term in terms[1:]:
                search += '|' + re.escape(term)
        return self._copy_with_added_query({'text': {'$regex': '.*{}.*'.format(search)}})

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

    def language(self, lang):
        """
        Only find tweets in a certain language. Goes by the 'lang' attribute in the tweet object.

        Example:
        ########

        collection.language('fr')
        """
        return self._copy_with_added_query({'lang': lang})

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

    def histogram(self, bins='days'):
        """
        Counts tweet volume by bins. Legal values are 'days', 'hours', 'minutes', 'seconds'.

        Example:
        ########

        bins, counts = collection.histogram(bins='minutes')
        plot(bins, counts)
        """
        try:
            dt = timedelta(**{bins: 1})
        except TypeError as e:
            raise Exception('"{}" is not a valid value for bins. Try "days", "hours", "minutes", "seconds.'.format(bins))

        bins = list()
        counts = list()

        for tweet in self:
            if len(bins) == 0:
                bins.append(tweet['timestamp'])
                counts.append(1)
            else:
                while tweet['timestamp'] > bins[-1] + dt:
                    bins.append(bins[-1] + dt)
                    counts.append(0)
                counts[-1] += 1

        return bins, counts

    def dump_csv(self):
        pass

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
        return (tweet for collection in self._mongo_collections for tweet in collection.find(self._query()))
