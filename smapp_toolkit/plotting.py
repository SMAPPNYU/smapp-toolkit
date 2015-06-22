"""
Module for plotting functions that work on data, not on live database connections.

@jonathanronen 2015/6
"""

import pytz
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import OrderedDict

def stacked_bar_plot(data, columns, x_tick_date_format='%Y-%m-%d', x_tick_step=2, bar_width=.8, alpha=.6, colors=sns.color_palette()):
    """
    Makes a stacked bars plot from data in a pandas.DataFrame.
    columns are the columns to be stacked.

    Example: Plot language proportions
    ##################################
        data = collection.group_by('days').language_counts(langs=['en','es','other'])

        plt.figure(figsize=(10,10))
        stacked_bar_plot(data, ['en','es','other'], colors=['royalblue', 'yellow', 'grey'])
        plt.title('Tweet proportions in English and Spanish', fontsize=24)
        plt.tight_layout()

    -----------------------------------------------------------------

    Example: Plot retweet proportion
    ################################
        data = col.since(datetime(2015,6,18,12)).until(datetime(2015,6,18,12,10)).group_by('minutes').entities_counts()
        data['original tweet'] = data['_total'] - data['retweet']

        plt.figure(figsize=(10,10))
        stacked_bar_plot(data, ['retweet', 'original tweet'], colors=['salmon', 'lightgrey'])
        plt.title('Retweet proportion', fontsize=24)
        plt.tight_layout()
    """
    bars = OrderedDict()
    bars[columns[0]] = plt.bar(range(len(data)),
                               data[columns[0]],
                               width=bar_width,
                               linewidth=0.0,
                               color=colors[0],
                               alpha=alpha,
                               label=columns[0])

    for l in columns[1:]:
        bars[l] = plt.bar(range(len(data)),
                          data[l],
                          width=bar_width,
                          linewidth=0.0,
                          color=colors[columns.index(l)],
                          alpha=alpha,
                          bottom=[c.get_y() + c.get_height() for c in bars[columns[columns.index(l)-1]].get_children()],
                          label=l)
    plt.xlim(0, len(data))
    plt.tick_params(axis="x", which="both", bottom="on", top="off", length=8, width=1, color="#999999")
    plt.legend(fontsize=14, loc=0)
    plt.xticks(np.arange(len(data))[::x_tick_step]+.4,
               [x.strftime(x_tick_date_format) for x in data.index[::x_tick_step]],
               rotation=45,
               fontsize=18)
    plt.yticks(fontsize=18)
    plt.tight_layout()

def line_with_annotations(data, events=[], x=None, y='count', x_tick_date_format='%Y-%m-%d', x_tick_timezone='UTC', x_tick_step=2, linewidth=2.0, alpha=.3, line_color='red', x_label_step=2):
    """
    Used to plot, for instance, tweets per day, with vertical lines to annotate events.
      `data` is a pandas.DataFrame object holding the line to be plotted
      `events` is a list of tuples with times, texts and alignments for events to be annotated onto figure
      `x` is the name of the column in the dataframe to use as the x-axis (defaults to the index)
      `y` is the column to plot on the y-axis


    Example (tweets per hour with annotations)
    #########################################
    data = collection.group_by('hours')
    events = [
      (datetime(2015,6,21,10), 'Sunrise', 'top'),
      (datetime(2015,6,21,22), 'Sunset', 'bottom')
    ]

    plt.figure(10,6)
    line_with_annotations(data, events, x_tick_timezone='America/New_York')
    plt.title('Tweets mentioning Donald Trump\non 2015-6-21', fontsize=24)
    """
    x = data[x] if x else data.index
    y = data[y]

    plt.plot(x, y, alpha=alpha, linewidth=linewidth, color=line_color)

    ymin, ymax = plt.ylim()
    for e in events:
        plt.axvline(e[0], linestyle="--", color="#999999")
        if e[2] == "bottom":
            plt.text(e[0], ymin + (0.05 * ymax), e[1], rotation=-90, verticalalignment="bottom")
        else:
            plt.text(e[0], ymax - (0.05 * ymax), e[1], rotation=-90, verticalalignment="top")

    plt.ylabel("# Tweets", fontsize=22)
    plt.tick_params(axis="x", which="both", bottom="on", top="off", length=8, width=1, color="#999999")
    plt.xticks(x[::x_label_step], [e.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(x_tick_timezone)).strftime(x_tick_date_format) for e in x[::x_label_step]], fontsize=16, rotation=90)
    plt.yticks(fontsize=16)
    plt.xlabel('Time\nin {}'.format(x_tick_timezone), fontsize=22)
