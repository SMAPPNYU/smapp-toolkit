"""
Module contains methods used to generate common figures from twitter data.

@jonathanronen, @dpb
"""
import warnings
try:
    import seaborn as sns
    import matplotlib.pyplot as plt
except:
    warnings.warn("Error importing plotting libraries (seaborn and matplotlib). Plotting functionality will not work.")
from collections import OrderedDict, Counter
from datetime import datetime, timedelta


def languages_per_day(collection, start, step_size=timedelta(days=1), num_steps=31,
  languages=['en', 'es', 'other'], language_colors=['red', 'royalblue', 'grey'],
  x_label_step = 2, alpha=.65, bar_width=.8, print_progress_every=100000, show=True):
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
    if show:
        plt.show()

def tweets_per_day_with_annotations(collection, start, num_steps, step_size=timedelta(days=1),
    alpha=.4, line_width=2.0, line_color="red", x_label_step=10, events=[], show=True):
    """
    Script to plot tweets per day with vertical annotation lines
    """
    # Get tweets per day
    tweets_per_day = []
    for step in range(num_steps):
        query_start = start + (step * step_size)
        tweets = collection.since(query_start).until(query_start+step_size)
        total = tweets.count()
        tweets_per_day.append(total)
        print "{0}: {1} - {2}: {3}".format(step, query_start, query_start + step_size, total)

    # Plot
    plt.plot(range(num_steps), tweets_per_day, alpha=alpha, linewidth=line_width, color=line_color)

    ymin, ymax = plt.ylim()
    for e in events:
        plt.axvline(e[0], linestyle="--", color="#999999")
        if e[2] == "bottom":
            plt.text(e[0] + 0.2, ymin + (0.05 * ymax), e[1], rotation=-90, verticalalignment="bottom")
        else:
            plt.text(e[0] + 0.2, ymax - (0.05 * ymax), e[1], rotation=-90, verticalalignment="top")

    plt.xlim(0, num_steps-1)
    plt.ylabel("# Tweets")
    plt.tick_params(axis="x", which="both", bottom="on", top="off", length=8, width=1, color="#999999")
    plt.xticks(range(num_steps)[::x_label_step],
               ["{0}-{1}-{2}".format(d.year, d.month, d.day) for d in [start + (i * step_size) for i in range(num_steps)[::x_label_step]]],
               rotation=55)
    if show:
        plt.show()

def tweets_over_time(collection, start, step_size=timedelta(days=1), num_steps=31, alpha=.7, bar_width=.8, x_label_step=7,
    xtick_format=None, show=True):
    """
    Plot a barchart (tweets per timeunit)
    """
    x_label = "Time"
    y_label = "Tweets"

    times = [start + (i * step_size) for i in range(num_steps)]
    counts = []
    for step in times:
        tweets = collection.since(step).until(step + step_size)
        counts.append(tweets.count())

    sns.set_style("darkgrid")
    sns.set_palette("husl")

    bars = plt.bar(range(num_steps),
                   counts,
                   width=bar_width,
                   linewidth=0.0,
                   alpha=alpha,
                   align="edge")

    plt.xlim(0, num_steps)
    plt.tick_params(axis="x", which="both", bottom="on", top="off", length=8, width=1, color="#999999")
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if not xtick_format:
        if step_size.total_seconds() < 60*60:
            xtick_format = '%H:%M'
        elif step_size.total_seconds() < 60*60*24:
            xtick_format = '%m-%d %H:%M'
        else:
            xtick_format = '%Y-%m-%d'

    plt.xticks(range(num_steps)[::x_label_step],
               [t.strftime(xtick_format) for t in times[::x_label_step]],
               rotation=90)

    plt.tight_layout()
    if show:
        plt.show()
    return times,counts

def geolocation_names_per_day(collection, start, step_size=timedelta(days=1), num_steps=31,
  names=None, name_colors=None, n_names=10,
  x_label_step = 2, alpha=.65, bar_width=.8, print_progress_every=100000, show=True):
    """
    If `names` is set, use those. Otherwise, use top `n_names` names.
    """
    global_name_counts = Counter()
    # Set up count dict
    name_counts = OrderedDict()
    for p in range(num_steps):
        name_counts[p] = OrderedDict()
        # for l in names:
            # name_counts[p][l] = 0

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

            if not tweet.get('place', None):
                place_name = "unk"
            else:
                place_name = tweet['place']['full_name']
                global_name_counts[place_name] += 1
            if place_name not in name_counts[step]:
                name_counts[step][place_name] = 0
            name_counts[step][place_name] += 1

        count_total = 0
        for n in name_counts[step].keys():
            count_total += name_counts[step][n]
        # assert count_total == total, "Error: Tweet by-name count does not match query total"
        print "\tQuery total: {0}, Count total: {1}".format(total, count_total)
        print "\t{0}".format(name_counts[step])

    # Pick top N places
    if names is None:
        names = [e[0] for e in global_name_counts.most_common(n_names)]
    # Pick colors
    if name_colors is None:
        name_colors = sns.color_palette("hls", n_names)
    elif len(name_colors) != len(names):
        warnings.warn("name_colors length doesn't match names length. Picking new colors.")
        name_colors = sns.color_palette("hls", n_names)

    for step in range(num_steps):
        other = sum(name_counts[step][name] for name in name_counts[step] if name not in names)
        new_name_counts = OrderedDict()
        for name in names:
            new_name_counts[name] = name_counts[step].get(name, 0)
        new_name_counts['other'] = other
        name_counts[step] = new_name_counts

    # Plot tweets in bars by name (in order of names list)
    bars = OrderedDict()
    bars[names[0]] = plt.bar(range(num_steps),
                                 [name_counts[i][names[0]] for i in range(num_steps)],
                                 width=bar_width,
                                 linewidth=0.0,
                                 color=name_colors[0],
                                 alpha=alpha,
                                 label=names[0])

    for l in names[1:]:
        bars[l] = plt.bar(range(num_steps),
                          [name_counts[i][l] for i in range(num_steps)],
                          width=bar_width,
                          linewidth=0.0,
                          color=name_colors[names.index(l)],
                          alpha=alpha,
                          bottom=[c.get_y() + c.get_height() for c in bars[names[names.index(l)-1]].get_children()],
                          label=l)
    plt.xlim(0, num_steps)
    plt.tick_params(axis="x", which="both", bottom="on", top="off", length=8, width=1, color="#999999")
    # plt.xlabel(x_label)
    plt.ylabel("# Tweets (by geolocation place name)")
    # plt.title(plot_title)
    plt.legend(fontsize=14, loc=1)
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., fontsize=14)
    plt.xticks(range(num_steps)[::x_label_step],
               ["{0}-{1}-{2}".format(d.year, d.month, d.day) for d in [start + (i * step_size) for i in range(num_steps)][::x_label_step]],
               rotation=55)
    if show:
        plt.show()