import re
from collections import Counter
from abc import ABCMeta, abstractmethod
from smappPy.iter_util import get_ngrams
from smappPy.unicode_csv import UnicodeWriter
from smappPy.retweet import is_official_retweet
from smappPy.store_tweets import tweets_to_file
from smappPy.text_clean import get_cleaned_tokens
from smappPy.entities import get_users_mentioned, get_hashtags
from smappPy.entities import get_urls, get_links, get_image_urls

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

    def _top_ngrams(self, ngram, n, hashtags, mentions, rts, mts, https, stopwords):
        counts = Counter()
        for tweet in self:
            tokens = get_cleaned_tokens(tweet["text"],
                                        keep_hashtags=hashtags,
                                        keep_mentions=mentions,
                                        rts=rts,
                                        mts=mts,
                                        https=https,
                                        stopwords=stopwords)
            ngrams = get_ngrams(tokens, ngram)
            counts.update(ngrams)
        return counts.most_common(n)

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
        return self._top_ngrams(1, n, hashtags, mentions, rts, mts, https, stopwords)

    def top_bigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
        return self._top_ngrams(2, n, hashtags, mentions, rts, mts, https, stopwords)

    def top_trigrams(self, n=10, hashtags=True, mentions=True, rts=False, mts=False, https=False, stopwords=[]):
        return self._top_ngrams(3, n, hashtags, mentions, rts, mts, https, stopwords)

    def top_links(self, n=10):
        """
        Returns a list of tuples representing the top 'n' links (default: 10) in the
        collection. 
        Return: [(link_n, #occurrences), (link_m, #occurrences)...]
        Note: "Links" include both URLs and Twitter Media (images, etc)
        Note: If a tweet contains the same link multiple times, each time is counted
        as one occurrence (ie, it is not top links-per-tweet).
        """
        return Counter([l for tweet in self for l in get_links(tweet)]).most_common(n)

    def top_urls(self, n=10):
        """
        See 'top_links()'. Same, but for only embedded links (not Tweet Media).
        """
        return Counter([u for tweet in self for u in get_urls(tweet)]).most_common(n)

    def top_images(self, n=10):
        return Counter([i for tweet in self for i in get_image_urls(tweet)]).most_common(n)

    def top_hashtags(self, n=10):
        return Counter([h for tweet in self for h in get_hashtags(tweet)]).most_common(n)

    def top_mentions(self, n=10):
        """
        Same as other top functions, except returns the number of unique (user_id, user_screen_name) pairs.
        """
        return Counter([m for tweet in self for m in get_users_mentioned(tweet)]).most_common(n)

    def top_user_locations(self, n=10):
        """
        Return top user location strings. Note that a user's location string is only considered
        once, regardless of how often the user appears in the collection.
        """
        users = set()
        loc_counts = Counter()
        for tweet in self:
            if tweet["user"]["id"] in users:
                continue
            users.add(tweet["user"]["id"])
            if tweet["user"]["location"]:
                loc_counts[tweet["user"]["location"]] += 1
        return loc_counts.most_common(n)

    def top_retweets(self, n=10):
        """
        Returns a list of top retweets. Return is a list of triples:
        [(retweet ID, RT count, retweet), ...]
        """
        rt_dict = {}
        rt_counts = Counter()
        for tweet in self:
            if is_official_retweet(tweet):
                rt_dict[tweet["retweeted_status"]["id"]] = tweet["retweeted_status"]
                rt_counts[tweet["retweeted_status"]["id"]] += 1
        return [(tid, tcount, rt_dict[tid]) for tid, tcount in rt_counts.most_common(n)]

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

    def dump_json(self, filename, append=False, pure_json=False, pretty=False):
        """
        Dumps the matching tweets in raw Mongo JSON (default) or Pure JSON (pure_json=True)
        format. To append to given filename, pass append=True. To pretty-print (line breaks
        and spacing), pass pretty=True.
        """
        tweets_to_file(self, filename, append, pure_json, pretty)

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

