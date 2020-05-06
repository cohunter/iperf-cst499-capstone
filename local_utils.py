# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 08:50:36 2020

@author: cohunter
"""

# This file holds utility functions common to the different types of analysis
# we plan to do for different testing periods and types of data.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import num2date
from datetime import timedelta

# set default figure size
plt.rcParams['figure.figsize'] = (16,9)

def reindex(*dfs, col='unix_timestamp'):
    """
    Reindex dataframes to datetime indexes based on values of `col`.

    Parameters
    ----------
    *dfs : pandas.DataFrame
        Dataframes to be reindexed, one or several. Modified in place.
    col : str, optional
        Column name to use as index. The default is 'unix_timestamp'.

    Returns
    -------
    None.

    """
    for df in dfs:
        if df.index.name is not col:
            df['unix_timestamp'] = pd.to_datetime(df[col], unit='s')
            df.set_index(df['unix_timestamp'], inplace=True)

def merge(*dfs, time=pd.Timedelta('5m')):
    """
    Merge two dataframes by index time within `time` of each other.

    Parameters
    ----------
    *dfs : pandas.DataFrame
        Dataframes to merge. Must have datetime indexes.
    time : pandas.Timedelta, optional
        The time difference range within which to merge rows. The default is pd.Timedelta('5m').

    Returns
    -------
    merged : pandas.DataFrame
        Single dataframe containing colname_x and colname_y values and 'unix_timestamp' column as copy of index.

    """
    # remove any rows without matching data to compare
    # we have 337 iPerf 3 results for Android -> Oregon and 335 iPerf 2 results
    merged = dfs[0].copy()
    for df in dfs[1:]:
        merged = pd.merge_asof(merged, df, left_index=True, right_index=True, tolerance=time, direction='nearest')
    merged['unix_timestamp'] = merged.index
    print('merged shape: {}; after dropna: {}'.format(merged.shape, merged.dropna().shape))
    return merged.dropna()

def reindex_and_merge(*dfs, col='unix_timestamp'):
    reindex(*dfs, col=col)
    return merge(*dfs)

def get_max_min(df, col='Jitter'):
    max = df[[col+'_x', col+'_y']].max().max()
    min = df[[col+'_x', col+'_y']].min().min()
    return (max, min)

def remove_colorbar_labels(figure, ownaxescount=2):
    axes = figure.get_axes()
    if len(axes) <= ownaxescount:
        return
    for i in range(ownaxescount, len(axes)):
        axes[i].set_ylabel('')

def adjust_xlim_to_index(ax, df):
    """
    For a given axes, assume that the x-axis is the datetime index of df and
    set the xlimits of the plot to +/- 1 hour of the max/min index value.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes with x-axis from datetime index of df.
    df : pandas.DataFrame
        Dataframe with a datetime index.

    Returns
    -------
    None.

    """
    ax.set_xlim(df.index.min()-timedelta(hours=1), df.index.max()+timedelta(hours=1))
    
def add_scale_labels(*axes, label='Unlabeled'):
    """
    Add top-left labels to each axis (subplot) passed as an argument.
    Assumes that the graph has dates on the x-axis.

    Parameters
    ----------
    *axes : matplotlib.axes.Axes
        Plots with dates as their x-axis and a numeric value as their y-axis.
    label : str, optional
        Label to add to the top-left of each plot. The default is 'Unlabeled'.

    Returns
    -------
    None.

    """
    for ax in axes:
        ax.text(num2date(ax.get_xlim()[0]), ax.get_ylim()[1] * 1.02, label, fontsize=12, fontname='Courier New')

def _check_merged(*dfs):
    if len(dfs) == 1:
        return dfs[0]
    else:
        return reindex_and_merge(*dfs)

def _pct_diff(i2, i3):
    """
    Calculate percent difference, iPerf 3 vs iPerf 2
    Parameters
    ----------
    i2 : number
        Value for iPerf 2.
    i3 : number
        Value for iPerf 3.

    Returns
    -------
    number
        Percent difference, i3 vs i2
    """
    return ((i3-i2)/i3) * 100

def compare_percentiles(*dfs, col='Jitter', title='Jitter', description='UDP Jitter', percentile=95):
    df = _check_merged(*dfs)
    iperf2_percentile = np.percentile(df[col+'_x'], percentile)
    iperf3_percentile = np.percentile(df[col+'_y'], percentile)
    pct_diff = _pct_diff(iperf2_percentile, iperf3_percentile)
    
    print(f'iPerf 2 {title}, {percentile}th percentile: {iperf2_percentile:.3f}\n'
          f'iPerf 3 {title}, {percentile}th percentile: {iperf3_percentile:.3f}\n'
          f'Percent difference, iPerf 3 vs iPerf 2 {description} {percentile}th percentile: {pct_diff:.0f}%')
    
    iperf2_mean = np.std(df[df[col+'_x'] <= iperf2_percentile][col+'_x'])
    iperf3_mean = np.std(df[df[col+'_y'] <= iperf3_percentile][col+'_y'])
    pct_diff = _pct_diff(iperf2_mean, iperf3_mean)
    print(iperf2_mean)
    
    print(f'iPerf 2 {title}, std below {percentile}th percentile: {iperf2_mean:.3f}\n'
          f'iPerf 3 {title}, std below {percentile}th percentile: {iperf3_mean:.3f}\n'
          f'Percent difference, iPerf 3 vs iPerf 2 {description} standard deviation below {percentile}th percentile: {pct_diff:.0f}%')
    
def get_percentiles(df, col, percentile=95):
    """
    Parameters
    ----------
    df : pandas.DataFrame
        A merged dataframe containing _x and _y columns.
    col : str
        Which column to look at.
    percentile : int, optional
        The percentile to calculate. The default is 95.

    Returns
    -------
    (float64, float64, float64)
        Tuple with percentile of col_x, col_y, and max of the two.

    """
    p1 = np.percentile(df[col + '_x'], percentile)
    p2 = np.percentile(df[col + '_y'], percentile)
    return (p1, p2, np.max([p1, p2]))
def compare_std(*dfs, col='Jitter', title='Jitter', description='UDP Jitter'):
    df = _check_merged(*dfs)
    
    iperf2_std = np.std(df[col+'_x'])
    iperf3_std = np.std(df[col+'_y'])
    
    pct_diff = ((iperf3_std - iperf2_std)/iperf3_std) * 100
    
    print(f'iPerf 2 {title}, standard deviation: {iperf2_std:.3f}\n'
          f'iPerf 3 {title}, standard deviation: {iperf3_std:.3f}\n'
          f'Percent difference, iPerf 3 vs iPerf 2 {description} standard deviation: {pct_diff:.0f}%')


def scatter_by_date(*dfs, col='Jitter', title='UDP Jitter by Date', subtitle='', label='Jitter (milliseconds)', dotscale=100):
    df = _check_merged(*dfs)
    #compare_std(df, col=col)
    max, min = get_max_min(df, col=col)
    
    fig, ax = plt.subplots(2, 1, sharex=True, sharey=True)
    
    df.plot.scatter(x='unix_timestamp', y=col+'_x', c=col+'_x', cmap='jet', s=df[col+'_x'] * dotscale, ax=ax[0], vmin=min, vmax=max)
    ax[0].set_ylabel('')
    ax[0].set_title(f'{title}\n{subtitle}\niPerf 2')
    
    
    df.plot.scatter(x='unix_timestamp', y=col+'_y', c=col+'_y', cmap='jet', s=df[col+'_y'] * dotscale, ax=ax[1], vmin=min, vmax=max)
    ax[1].set_title('iPerf 3')
    ax[1].set_ylabel('')
    
    ax[1].tick_params(axis='x', which='both', bottom=True, labelbottom=True, labelrotation=25)
    
    remove_colorbar_labels(fig)
    adjust_xlim_to_index(ax[0], df)
    add_scale_labels(ax[0], ax[1], label=label)
    return fig

def ratebydate(df1, df2, title, scale=1e7):
    merged = reindex_and_merge(df1, df2)
    p1_95th, p2_95th, max_95th = get_percentiles(merged, 'transfer_rate')
    pct_difference_95th = (((p1_95th / p2_95th)-1)*100)
    
    plt.rcParams['figure.figsize'] = (16,10)
    fig, ax = plt.subplots(2,1, sharey=True, sharex=True)
    fig.suptitle('Transfer Rate and Totals ({})'.format(title))
    merged['transfer_rate_x'].plot(ax=ax[0], alpha=0.9)
    merged['transfer_amount_x'].plot(ax=ax[0], alpha=0.5)
    ax[0].plot(merged['unix_timestamp'], [merged['transfer_rate_x'].mean()]*len(merged['unix_timestamp']), color='y', label='Mean', alpha=0.9)
    ax[0].annotate('  '+str(round(merged['transfer_rate_x'].mean()/scale,3)), xy=(ax[0].get_xlim()[1]-.75, merged['transfer_rate_x'].mean()), xycoords='data', textcoords='offset points', xytext=(0,0))
    ax[0].set_title('iPerf 3')
    ax[0].plot(merged['unix_timestamp'], [merged['transfer_rate_x'].median()]*len(merged['transfer_rate_x']), color='g', label='Median', alpha=0.9)
    ax[0].annotate('  '+str(round(merged['transfer_rate_x'].median()/scale,3)), xy=(ax[0].get_xlim()[0], merged['transfer_rate_x'].median()), xycoords='data', textcoords='offset points', xytext=(0,0))
    
    ax[0].legend(['bits per second', 'transfer amount (bytes)', 'mean (bits per second)', 'median (bits per second)'])
    
    merged['transfer_rate_y'].plot(ax=ax[1], alpha=0.9)
    merged['transfer_amount_y'].plot(ax=ax[1], alpha=0.5)
    ax[1].plot(merged['unix_timestamp'], [merged['transfer_rate_y'].mean()]*len(merged['unix_timestamp']), color='y', label='Mean', alpha=0.9)
    ax[1].annotate('  '+str(round(merged['transfer_rate_y'].mean()/scale,3)), xy=(ax[1].get_xlim()[1]-.75, merged['transfer_rate_y'].mean()), xycoords='data', textcoords='offset points', xytext=(0,0))
    
    ax[1].plot(merged['unix_timestamp'], [merged['transfer_rate_y'].median()]*len(merged['transfer_rate_y']), color='g', label='Median', alpha=0.9)
    ax[1].annotate('  '+str(round(merged['transfer_rate_y'].median()/scale,3)), xy=(ax[1].get_xlim()[0], merged['transfer_rate_y'].median()), xycoords='data', textcoords='offset points', xytext=(0,0))
    ax[1].set_title('iPerf 2')
    ax[1].legend(['bits per second', 'transfer amount (bytes)', 'mean (bits per second)', 'median (bits per second)'])
    
    pct_difference = ((merged['transfer_rate_x'].mean() / merged['transfer_rate_y'].mean())-1)*100
    ax[1].set_xlabel(f'Percent difference iPerf 3 vs iPerf 2, mean bits per second: {pct_difference:.3}%\n'+
                     f'95th percentile difference: {pct_difference_95th:.3}%')

    return fig