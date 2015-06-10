import re
import pandas as pd
import figure_makers
import figure_helpers
import networkx as nx
from aggregator import Aggregator
from abc import ABCMeta, abstractmethod
from smappPy.iter_util import get_ngrams
from collections import Counter, defaultdict
from smappPy.unicode_csv import UnicodeWriter
from smappPy.retweet import is_official_retweet
from smappPy.store_tweets import tweets_to_file
from smappPy.text_clean import get_cleaned_tokens
from smappPy.xml_util import clear_unicode_control_chars
from counter_functions import _top_user_locations, _top_ngrams, _top_unigrams, _top_bigrams, _top_trigrams, _top_links, \
    _top_urls, _top_images, _top_hashtags, _top_mentions, _top_geolocation_names

class BaseTweetCollection(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def field_containing(self, field, *terms):
        pass

    def _regex_escape_and_concatenate(self, *terms):
        search = re.escape(terms[0])
        if len(terms) > 1:
            for term in terms[1:]:
                search += '|' + re.escape(term)
        return search

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

    def texts(self):
        """
        Return the tweet texts matching all specified criteria.

        Example:
        ########

        collection.since(datetime(2014,1,1)).texts()
        """
        return [tweet['text'] for tweet in self]

    def group_by(self, time_unit):
        """
        Get results by time slice ('days', 'hours', 'minutes', 'seconds').
        Returns a generator of times and tweet-generators, like this:

        Example:
        ########
        for time, tweets in collection.group_by('minutes'):
            for tweet in tweets:
                # do something

        ---------------------------------------------------

        Also supports top_x() methods like this:

        Example:
        ########

        collection.since(datetime(2015,6,1)).group_by('days').top_user_locations(n=5)
        >
        #            London  London, UK  Manchester  Scotland  UK
        # 2015-06-1       4           2           1         1   2
        # 2015-06-2      11           4           9         3   3
        # 2015-06-3      14           1           5       NaN   4
        # 2015-06-4      17           1           5         1   6
        # 2015-06-5      10           3           3         3   3
        """
        return Aggregator(self, time_unit=time_unit)

    def top_unigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
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
            - "rt" exactly
            - "mt" exactly
            - any token containing the substring "http"

        'stopwords' can be a list of words to remove from each tweet before considering.
        Seel nltk (http://www.nltk.org/book/ch02.html) stopwords corpuses, for example.

        Example (get top 100 unigrams, removing english stopwords from consideration):
        ##############################################################################
        import nltk
        collection.top_unigrams(n=100, stopwords=nltk.stopwords.words("english"))
        """
        return _top_unigrams(self, n, hashtags, mentions, rts, mts, https, stopwords)

    def top_bigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
        return _top_bigrams(self, n, hashtags, mentions, rts, mts, https, stopwords)

    def top_trigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
        return _top_trigrams(self, n, hashtags, mentions, rts, mts, https, stopwords)

    def top_links(self, n=10):
        """
        Returns a list of tuples representing the top 'n' links (default: 10) in the
        collection. 
        Note: "Links" include both URLs and Twitter Media (images, etc)
        Note: If a tweet contains the same link multiple times, each time is counted
        as one occurrence (ie, it is not top links-per-tweet).
        """
        return _top_links(self, n)

    def top_urls(self, n=10):
        """
        See 'top_links()'. Same, but for only embedded links (not Tweet Media).
        """
        return _top_urls(self, n)

    def top_images(self, n=10):
        return _top_images(self, n)

    def top_hashtags(self, n=10):
        return _top_hashtags(self, n)

    def top_mentions(self, n=10):
        """
        Same as other top functions, except returns the number of unique (user_id, user_screen_name) pairs.
        """
        return _top_mentions(self, n)

    def top_user_locations(self, n=10, count_each_user_once=True):
        """
        Return top user location strings.

        If `count_each_user_once` is True, a user's location string is only considered
        once, regardless of how often the user appears in the collection.
        If False, a user's location string is counted multiple times.
        """
        return _top_user_locations(self, n, count_each_user_once)

    def top_geolocation_names(self, n=10):
        """
        Return top location names from geotagged tweets. Place names come from twitter's "Places".
        """
        return _top_geolocation_names(self, n)

    DEFAULT_RT_COLUMNS = ['user.screen_name', 'created_at', 'text']
    def top_retweets(self, n=10, rt_columns=DEFAULT_RT_COLUMNS):
        """
        Returns a list of top retweets as a pandas DataFrame.
        Columns to include in the dataframe from the original retweet are passed in `rt_columns`.
        The default `rt_columns=['user.screen_name', 'created_at', 'text']`

        Example:
        ########
        col.top_retweets(rt_columns=['timestamp', 'text'])
        """
        rt_dict = {}
        rt_counts = Counter()
        for tweet in self:
            if is_official_retweet(tweet):
                rt_dict[tweet["retweeted_status"]["id"]] = tweet["retweeted_status"]
                rt_counts[tweet["retweeted_status"]["id"]] += 1
        return pd.DataFrame([[tid, tcount] + self._make_row(rt_dict[tid], rt_columns) for tid, tcount in rt_counts.most_common(n)], columns=['id', 'count']+rt_columns)

    def term_counts(self, terms, count_by='days', plot=False, plot_total=True, match='tokens', case_sensitive=False):
        """
        Returns a dict with term counts aggregated by `count_by`. Acceptable values for `count_by` are 'days', 'hours', 'minutes'.
        if `plot` is True, also plots a histogram.

        Example:
        ########
        collection.term_counts(['justin', 'miley'])
        >> {'2015-04-01': {'justin': 1312, 'miley': 837},
            '2015-04-02': {'justin': 3287, 'miley': 932}}
        """
        if count_by == 'days':
            KEY_FORMAT = '%Y-%m-%d'
        elif count_by == 'hours':
            KEY_FORMAT = '%Y-%m-%d %H:00'
        elif count_by == 'minutes':
            KEY_FORMAT = '%Y-%m-%d %H:%M'
        else:
            raise Exception("Illegal value for `count_by` ({}). Legal values are ['days', 'hours', 'minutes'].".format(count_by))

        if not case_sensitive:
            terms = [t.lower() for t in terms]

        _DEFAULT_COUNTS_TOKENIZER_REGEXP = re.compile('\w+')
        _DEFAULT_COUNTS_TOKENIZER = lambda s: _DEFAULT_COUNTS_TOKENIZER_REGEXP.findall(s)
        if match == 'tokens' and case_sensitive:
            contains = lambda text, term: term in _DEFAULT_COUNTS_TOKENIZER(text)
        elif match == 'tokens' and not case_sensitive:
            contains = lambda text, term: term in _DEFAULT_COUNTS_TOKENIZER(text.lower())
        elif match == 'substring' and case_sensitive:
            contains = lambda text, term: term in text
        elif match == 'substring' and not case_sensitive:
            contains = lambda text, term: term in text.lower()
        else:
            raise Exception("Illegal value for `match`. Legal values are ['tokens', 'substring'].")

        ret = defaultdict(lambda: {t: 0 for t in terms+['_total']})

        for tweet in self.containing(*terms):
            d = ret[tweet['timestamp'].strftime(KEY_FORMAT)]
            d['_total'] += 1
            for term in terms:
                if contains(tweet['text'], term):
                    d[term] += 1

        if plot:
            figure_helpers.term_counts_histogram(ret, KEY_FORMAT, count_by, plot_total)

        return ret

    def _recursive_read(self, tweet, col_name):
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
        return unicode(value)

    DEFAULT_CSV_COLUMNS = ['id_str', 'user.screen_name', 'timestamp', 'text']
    def _make_row(self, tweet, columns=DEFAULT_CSV_COLUMNS):
        row = list()
        for col_name in columns:
            value = self._recursive_read(tweet, col_name)
            row.append(u','.join(unicode(v) for v in value) if isinstance(value, list) else unicode(value))
        return row

    def dump_csv(self, filename, columns=DEFAULT_CSV_COLUMNS):
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

    def dump_json(self, filename, append=False, pure_json=False, pretty=False):
        """
        Dumps the matching tweets in raw Mongo JSON (default) or Pure JSON (pure_json=True)
        format. To append to given filename, pass append=True. To pretty-print (line breaks
        and spacing), pass pretty=True.
        """
        tweets_to_file(self, filename, append, pure_json, pretty)

    def _make_metadata_dict(self, obj, fields):
        return { field: clear_unicode_control_chars(self._recursive_read(obj, field))\
         for field in fields }

    def retweet_network(
        self,
        user_metadata=['id_str', 'screen_name', 'location', 'description'],
        tweet_metadata=['id_str', 'retweeted_status.id_str', 'timestamp', 'text', 'lang']):
        """
        Generate a retweet graph from the selection of tweets.
        Users are nodes, retweets are directed links.

        `user_metadata` is a list of fields from the User object that will be included as
        attributes in the nodes.
        `tweet_metadata` is a list of the fields from the Tweet object that will be included
        as attributes on the edges.

        If the collection result includes non-retweets as well, users with no retweets
        will also appear in the graph as isolated nodes. Only retweets are edges in the
        resulting graph.

        Example:
        ########
        imprt networkx as nx
        digraph = collection.containing('#AnyoneButHillary').only_retweets().retweet_network()
        nx.write_graphml(digraph, '/path/to/outputfile.graphml')
        """
        dg = nx.DiGraph(name=u"RT graph of {}".format(unicode(self)))
        for tweet in self:
            user = tweet['user']
            if user['id_str'] not in dg:
                dg.add_node(tweet['user']['id_str'],
                    attr_dict=self._make_metadata_dict(user, user_metadata))
            if 'retweeted_status' in tweet:
                retweeted_user = tweet['retweeted_status']['user']
                dg.add_node(retweeted_user['id_str'],
                    attr_dict=self._make_metadata_dict(retweeted_user, user_metadata))
                dg.add_edge(user['id_str'], retweeted_user['id_str'],
                    attr_dict=self._make_metadata_dict(tweet, tweet_metadata))
        return dg


    def __getattr__(self, name):
        """
        Object call redirector. Handle X_containing and Y_figure calls.
        """
        if name.endswith('_containing'):
            field_name = '.'.join(name.split('_')[:-1])
            def containing_method(*terms):
                return self.field_containing(field_name, *terms)
            return containing_method
        elif name.endswith('_figure'):
            figure_name = '_'.join(name.split('_')[:-1])
            method = figure_makers.__getattribute__(figure_name)
            def figure_method(*args, **kwargs):
                return method(self, *args, **kwargs)
            return figure_method
        else:
            return object.__getattribute__(self, name)

