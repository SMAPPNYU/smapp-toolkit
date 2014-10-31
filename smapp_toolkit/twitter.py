import copy
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
    def __init__(self, address, port, dbname, collection_name, username=None, password=None):
        self._client = MongoClient(address, port)
        self._mongo_database = self._client[dbname]
        if username and password:
            self._mongo_database.authenticate(username, password)
        self._mongo_collection = self._mongo_database[collection_name]
        self._queries = list()

    def _copy_with_added_query(self, query):
        ret = copy.copy(self)
        ret._queries = copy.copy(self._queries)
        ret._queries.append(query)
        return ret

    def mentioning(self, term):
        return self._copy_with_added_query({'text': {'$regex': '.*{}.*'.format(term)}})

    def since(self, since):
        return self._copy_with_added_query({'timestamp': {'$gt': since}})

    def until(self, until):
        return self._copy_with_added_query({'timestamp': {'$lt': until}})

    def count(self):
        return self._mongo_collection.find(self._query()).count()

    def texts(self):
        return [tweet['text'] for tweet in self]

    def _merge(self, a, b, path=None):
        "merges b into a"
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
        q = dict()
        for query in self._queries:
            q = self._merge(q, query)
        return q

    def __iter__(self):
        return self._mongo_collection.find(self._query())
