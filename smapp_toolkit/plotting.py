"""
Module for plotting functions that work on data, not on live database connections.

@jonathanronen 2015/6
"""


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
