import re
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
    def __init__(self, address='localhost', port=27017, dbname='test', collection_name='tweets', username=None, password=None):
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

    def count(self):
        """
        The count of tweets in the collection matching all specified criteria.

        Example:
        ########

        collection.containing('peace').count()
        """
        return self._mongo_collection.find(self._query()).count()

    def texts(self):
        """
        Return the tweet texts matching all specified criteria.

        Example:
        ########

        collection.since(datetime(2014,1,1)).texts()
        """
        return [tweet['text'] for tweet in self]

    

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
        return self._mongo_collection.find(self._query())
