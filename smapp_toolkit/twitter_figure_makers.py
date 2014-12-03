"""
Module contains methods used to generate common figures from twitter data.

@jonathanronen, @dpb
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from seaborn import color_palette
import matplotlib.pyplot as plt


def languages_per_day(collection, start, step_size=timedelta(days=1), num_steps=31,
  languages=['en', 'es', 'other'], language_colors=['red', 'royalblue', 'grey'],
  x_label_step = 2, alpha=.65, bar_width=.8, print_progress_every=100000):
    # Set up language count dict
    language_counts = OrderedDict()
    for p in range(num_steps):
        language_counts[p] = OrderedDict()
        for l in languages:
            language_counts[p][l] = 0

    # Iterate over time period, querying for tweets and storing counts
    # NOTE: Could do this with a few mapreduce queries
    for step in range(num_steps):
        query_start = start + (step * step_size)
        print "{0}: {1} - {2}".format(step, query_start, query_start + step_size)

        # tweets = collection.find({"timestamp": {"$gte": query_start, "$lt": query_start + step_size}})
        tweets = collection.since(query_start).until(query_start+step_size)
        total = tweets.count()

        counter = 0
        for tweet in tweets:
            if counter % print_progress_every == 0:
                print "\t{0} of {1}".format(counter, total)
            counter += 1

            if "lang" not in tweet:
                tweet["lang"] = "unk"
            if tweet["lang"] in languages:
                language_counts[step][tweet["lang"]] += 1
            else:
                language_counts[step]["other"] += 1

        count_total = 0
        for l in languages:
            count_total += language_counts[step][l]
        assert count_total == total, "Error: Tweet by-language count does not match query total"
        print "\tQuery total: {0}, Count total: {1}".format(total, count_total)
        print "\t{0}".format(language_counts[step])

    # Plot tweets in bars by language (in order of languages list)
    bars = OrderedDict()
    bars[languages[0]] = plt.bar(range(num_steps),
                                 [language_counts[i][languages[0]] for i in range(num_steps)],
                                 width=bar_width,
                                 linewidth=0.0,
                                 color=language_colors[0],
                                 alpha=alpha,
                                 label=languages[0])

    for l in languages[1:]:
        bars[l] = plt.bar(range(num_steps),
                          [language_counts[i][l] for i in range(num_steps)],
                          width=bar_width,
                          linewidth=0.0,
                          color=language_colors[languages.index(l)],
                          alpha=alpha,
                          bottom=[c.get_y() + c.get_height() for c in bars[languages[languages.index(l)-1]].get_children()],
                          label=l)
    plt.xlim(0, num_steps)
    plt.tick_params(axis="x", which="both", bottom="on", top="off", length=8, width=1, color="#999999")
    # plt.xlabel(x_label)
    plt.ylabel("# Tweets (by language)")
    # plt.title(plot_title)
    plt.legend(fontsize=14, loc=0)
    plt.xticks(range(num_steps)[::x_label_step],
               ["{0}-{1}-{2}".format(d.year, d.month, d.day) for d in [start + (i * step_size) for i in range(num_steps)][::x_label_step]],
               rotation=55)
    plt.show()
