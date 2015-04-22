"""
Module contains helper functions for plotting.

@jonathanronen 4/2015
"""
try:
    import numpy as np
except:
    warnings.warn("Cannot import numpy. Plotting will not work.")
import warnings
try:
    import seaborn as sns
    import matplotlib.pyplot as plt
except:
    warnings.warn("Error importing plotting libraries (seaborn and matplotlib). Plotting functionality will not work.")
from datetime import datetime, timedelta


def plot_histo(d, *args, **kwargs):
    count_by = kwargs.pop('count_by', 'minutes')
    key_format = kwargs.pop('key_format', '%Y-%m-%d %H:%M')

    start_time = datetime.strptime(sorted(d.keys())[0], key_format)
    end_time = datetime.strptime(sorted(d.keys())[-1], key_format)
    if count_by == 'minutes':
        t,y = zip(*[(start_time + i*timedelta(minutes=1), d.get((start_time + i*timedelta(minutes=1)).strftime(key_format), 0)) for i in range(int(np.ceil((end_time - start_time).total_seconds()/60)))])
    elif count_by == 'hours':
        t,y = zip(*[(start_time + i*timedelta(hours=1), d.get((start_time + i*timedelta(hours=1)).strftime(key_format), 0)) for i in range(int(np.ceil((end_time - start_time).total_seconds()/(60*60))))])
    elif count_by == 'days':
        t,y = zip(*[(start_time + i*timedelta(days=1), d.get((start_time + i*timedelta(days=1)).strftime(key_format), 0)) for i in range(int(np.ceil((end_time - start_time).total_seconds()/(60*60*24))))])
    else:
        raise Exception("Can't plot histogram by {}. Legal values are ['minutes', 'hours', 'days'].".format(count_by))
    plt.plot(t,y, *args, **kwargs)
    return t,y


def term_counts_histogram(data, key_format, count_by, plot_total=True):
    """
    Function to make histogram plot for data created using `term_counts()`.

    If the data has the format:
    {
        '2015-01-01 18:10': {
            'justin': 12,
            'miley': 33
        },
        '2015-01-01 18:11': {
            'justin': 11,
            'miley': 9
        }
    }

    Then to make the plot, call

    figure_helpers.term_counts_histogram(data, '%Y-%m-%d %H:%M', count_by='minutes')
    ------------------------------------------------

    Legal values for count_by are ['days', 'hours', 'minutes']
    and the `key_format` is the strftime string for the keys of the data dict.
    """
    colors = sns.color_palette('hls', len(data[data.keys()[0]].keys()))

    terms = data[data.keys()[0]].keys()
    terms.remove('_total')
    for c, term in zip(colors,terms):
        t,y = plot_histo({k : data[k][term] for k in data}, label=term, color=c, count_by=count_by, key_format=key_format)

    if plot_total:
        plot_histo({k: data[k]['_total'] for k in data}, label='total', color='grey', linestyle='--', count_by=count_by, key_format=key_format)

    plt.legend()
    plt.xticks(t[::len(t)/10],
               [ts.strftime(key_format) for ts in t[::len(t)/10]],
               rotation=45)
    plt.tight_layout()
