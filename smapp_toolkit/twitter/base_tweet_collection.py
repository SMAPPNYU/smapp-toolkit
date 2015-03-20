import re
from abc import ABCMeta, abstractmethod

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