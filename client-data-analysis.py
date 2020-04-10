# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 14:32:15 2020

@author: cohunter
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Show me all the data. I said all of it. You heard me, pandas.
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

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

def reindex_and_merge(*dfs):
    reindex(*dfs)
    return merge(*dfs)

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

def get_maxminmean(df, col):
    max = df[[col+'_x', col+'_y']].max().max()
    min = df[[col+'_x', col+'_y']].min().min()
    return (max, min, df[col+'_x'].mean(), df[col+'_y'].mean())

def scatter(df):
    pd.plotting.scatter_matrix(df, figsize=(24,16))

def ratebydate(df1, df2, title, scale=1e7):
    merged = reindex_and_merge(df1, df2)
    p1_95th, p2_95th, max_95th = get_percentiles(merged, 'transfer_rate')
    pct_difference_95th = (((p1_95th / p2_95th)-1)*100)
    
    plt.rcParams['figure.figsize'] = (16,10)
    fig, ax = plt.subplots(2,1, sharey=True, sharex=True)
    fig.suptitle('Transfer Rate and Totals ({})'.format(title))
    df1['transfer_rate'].plot(ax=ax[0], alpha=0.9)
    df1['transfer_amount'].plot(ax=ax[0], alpha=0.5)
    ax[0].plot(df1['unix_timestamp'], [df1['transfer_rate'].mean()]*len(df1['unix_timestamp']), color='y', label='Mean', alpha=0.9)
    ax[0].annotate('  '+str(round(df1['transfer_rate'].mean()/scale,3)), xy=(ax[0].get_xlim()[1]-.75, df1['transfer_rate'].mean()), xycoords='data', textcoords='offset points', xytext=(0,0))
    ax[0].set_title('iPerf 3')
    ax[0].plot(df1['unix_timestamp'], [df1['transfer_rate'].median()]*len(df1['transfer_rate']), color='g', label='Median', alpha=0.9)
    ax[0].annotate('  '+str(round(df1['transfer_rate'].median()/scale,3)), xy=(ax[0].get_xlim()[0], df1['transfer_rate'].median()), xycoords='data', textcoords='offset points', xytext=(0,0))
    
    ax[0].legend(['bits per second', 'transfer amount (bytes)', 'mean (bits per second)', 'median (bits per second)'])
    
    df2['transfer_rate'].plot(ax=ax[1], alpha=0.9)
    df2['transfer_amount'].plot(ax=ax[1], alpha=0.5)
    ax[1].plot(df2['unix_timestamp'], [df2['transfer_rate'].mean()]*len(df2['unix_timestamp']), color='y', label='Mean', alpha=0.9)
    ax[1].annotate('  '+str(round(df2['transfer_rate'].mean()/scale,3)), xy=(ax[1].get_xlim()[1]-.75, df2['transfer_rate'].mean()), xycoords='data', textcoords='offset points', xytext=(0,0))
    
    ax[1].plot(df2['unix_timestamp'], [df2['transfer_rate'].median()]*len(df2['transfer_rate']), color='g', label='Median', alpha=0.9)
    ax[1].annotate('  '+str(round(df2['transfer_rate'].median()/scale,3)), xy=(ax[1].get_xlim()[0], df2['transfer_rate'].median()), xycoords='data', textcoords='offset points', xytext=(0,0))
    ax[1].set_title('iPerf 2')
    ax[1].legend(['bits per second', 'transfer amount (bytes)', 'mean (bits per second)', 'median (bits per second)'])
    
    pct_difference = ((df1['transfer_rate'].mean() / df2['transfer_rate'].mean())-1)*100
    ax[1].set_xlabel(f'Percent difference iPerf 3 vs iPerf 2, mean bits per second: {pct_difference:.3}%\n'+
                     f'95th percentile difference: {pct_difference_95th:.3}%')

def jitterbydate(df1, df2, title):
    bunchofspaces = '                                        '
    
    merged = reindex_and_merge(df1, df2)
    max_jitter = merged[['jitter_ms_x','jitter_ms_y']].max().max()
    min_jitter = merged[['jitter_ms_x','jitter_ms_y']].min().min()
    plt.rcParams['figure.figsize'] = (16, 10)
    
    fig, ax = plt.subplots(2, 1, sharey=True, sharex=True)
    fig.suptitle('UDP Jitter {} {}'.format(title, bunchofspaces))
    merged.plot.scatter(x='unix_timestamp', y='jitter_ms_x', c='jitter_ms_x', colormap='jet', ax=ax[0], alpha=0.25, vmin=min_jitter, vmax=max_jitter, s=50)
    merged.plot.scatter(x='unix_timestamp', y='jitter_ms_y', c='jitter_ms_y', colormap='jet', ax=ax[1], alpha=0.25, vmin=min_jitter, vmax=max_jitter, s=50)
    fig.get_axes()[0].set_ylabel('Jitter (ms)')
    fig.get_axes()[1].set_ylabel('Jitter (ms)')
    fig.get_axes()[2].set_ylabel('')
    fig.get_axes()[3].set_ylabel('')
    ax[0].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    #ax[1].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    ax[0].set_title('iPerf 3')
    ax[1].set_title('iPerf 2')
    ax[1].tick_params(axis='x', which='both', bottom=True, labelbottom=True, labelrotation=25)
    pct_difference = 'Percent difference iPerf 3 vs iPerf 2, UDP Jitter: {:.3}%'.format(((merged['jitter_ms_x'].mean()/merged['jitter_ms_y'].mean())-1)*100)
    ax[1].xaxis.set_label_text(pct_difference, figure=fig, visible=True)
    print('mean: {:.3}%'.format(((merged['jitter_ms_x'].mean()/merged['jitter_ms_y'].mean())-1)*100))

    p1_95th, p2_95th, max_95th = get_percentiles(merged, 'jitter_ms')
    
    fig, ax = plt.subplots(2, 1, sharey=True, sharex=True)
    fig.suptitle('95th percentile UDP Jitter {} {}'.format(title, bunchofspaces))
    merged[merged['jitter_ms_x'] < p1_95th].plot.scatter(x='unix_timestamp', y='jitter_ms_x', c='jitter_ms_x', colormap='jet', ax=ax[0], alpha=0.4, vmin=min_jitter, vmax=max_95th, s=50)
    merged[merged['jitter_ms_y'] < p2_95th].plot.scatter(x='unix_timestamp', y='jitter_ms_y', c='jitter_ms_y', colormap='jet', ax=ax[1], alpha=0.4, vmin=min_jitter, vmax=max_95th, s=50)
    fig.get_axes()[0].set_ylabel('Jitter (ms)')
    fig.get_axes()[1].set_ylabel('Jitter (ms)')
    fig.get_axes()[2].set_ylabel('')
    fig.get_axes()[3].set_ylabel('')
    ax[0].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    ax[1].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    ax[0].set_title('iPerf 3')
    ax[1].set_title('iPerf 2')
    ax[1].tick_params(axis='x', which='both', bottom=True, labelbottom=True, labelrotation=25)
    pct_difference = 'Percent difference iPerf 3 vs iPerf 2, 95th percentile UDP Jitter: {:.3}%'.format(((p1_95th/p2_95th)-1)*100)
    ax[1].xaxis.set_label_text(pct_difference, figure=fig, visible=True)
    return

def packetlossbydate(df1, df2, title):
    bunchofspaces = '                                        '
    # remove any rows without matching data to compare
    # we have 337 iPerf 3 results for Android -> Oregon and 335 for iPerf 2
    merged = reindex_and_merge(df1, df2)
    
    max_lost, min_lost, mean_x, mean_y = get_maxminmean(merged, 'lost_packets')
    if max_lost == 0:
        print('Error: max_lost is 0; unable to graph.')
        return
    
    plt.rcParams['figure.figsize'] = (16, 10)
    
    fig, ax = plt.subplots(2, 1, sharey=True, sharex=True)
    fig.suptitle('UDP Packet Loss {} {}'.format(title, bunchofspaces))
    #ax[0].set_xlim(df1['unix_timestamp'].min(), df1['unix_timestamp'].max())
    merged.plot.scatter(x='unix_timestamp', y='lost_packets_x', c='lost_packets_x', colormap='jet', ax=ax[0], alpha=0.5, vmin=min_lost, vmax=max_lost, s=50)
    merged.plot.scatter(x='unix_timestamp', y='lost_packets_y', c='lost_packets_y', colormap='jet', ax=ax[1], alpha=0.5, vmin=min_lost, vmax=max_lost, s=50)
    print(pd.to_datetime(merged['unix_timestamp_x'].min()), pd.to_datetime(merged['unix_timestamp_x'].max()))
    fig.get_axes()[0].set_ylabel('Lost Packets (count)')
    fig.get_axes()[1].set_ylabel('Lost Packets (count)')
    fig.get_axes()[2].set_ylabel('')
    fig.get_axes()[3].set_ylabel('')
    ax[0].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    ax[1].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    ax[0].set_title('iPerf 3')
    ax[1].set_title('iPerf 2')
    ax[1].tick_params(axis='x', which='both', bottom=True, labelbottom=True, labelrotation=25)
    pct_difference = 'Percent difference iPerf 3 vs iPerf 2, UDP Packet Loss: {:.3}%'.format((((mean_x+1)/(mean_y+1))-1)*100)
    ax[1].xaxis.set_label_text(pct_difference, figure=fig, visible=True)
    
    p1_90th, p2_90th, max_90th = get_percentiles(merged, 'lost_packets', 95)
    if max_90th == 0:
        print('Error: max 90th percentile packet loss is 0; unable to graph.')
        return
    fig, ax = plt.subplots(2, 1, sharey=True, sharex=True)
    fig.suptitle('95th percentile UDP Packet Loss {} {}'.format(title, bunchofspaces))
    merged[(merged['lost_packets_x'] < p1_90th) & (merged['lost_packets_x'] > 0)].plot.scatter(x='unix_timestamp', y='lost_packets_x', c='lost_packets_x', colormap='jet', ax=ax[0], alpha=0.4, vmin=min_lost, vmax=max_90th, s=50)
    merged[(merged['lost_packets_y'] < p2_90th) & (merged['lost_packets_y'] > 0)].plot.scatter(x='unix_timestamp', y='lost_packets_y', c='lost_packets_y', colormap='jet', ax=ax[1], alpha=0.4, vmin=min_lost, vmax=max_90th, s=50)
    fig.get_axes()[0].set_ylabel('Lost Packets (count)')
    fig.get_axes()[1].set_ylabel('Lost Packets (count)')
    fig.get_axes()[2].set_ylabel('')
    fig.get_axes()[3].set_ylabel('')
    ax[0].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    ax[1].set_xlim(pd.to_datetime(merged['unix_timestamp'].min()), pd.to_datetime(merged['unix_timestamp'].max()))
    ax[0].set_title('iPerf 3')
    ax[1].set_title('iPerf 2')
    ax[1].tick_params(axis='x', which='both', bottom=True, labelbottom=True, labelrotation=25)
    pct_difference = 'Percent difference iPerf 3 vs iPerf 2, 95th percentile UDP Packet Loss: {:.3}%'.format(((p1_90th/p2_90th)-1)*100)
    ax[1].xaxis.set_label_text(pct_difference, figure=fig, visible=True)
    return
iperf2_tcp_columns = ['unix_timestamp', 'local_addr', 'local_port', 'remote_addr', 'remote_port', 'duration', 'transfer_amount', 'transfer_rate']
#iperf2_10m_tcp_oregon_client = pd.read_csv("iperf2-10m-tcp-oregon-client.csv", names=iperf2_tcp_columns, header=0)
#iperf2_10m_tcp_par_client = pd.read_csv("iperf2-10m-tcp-par-client.csv", names=iperf2_tcp_columns, header=0)
#iperf2_10m_tcp_ams_client = pd.read_csv("iperf2-10m-tcp-ams-client.csv", names=iperf2_tcp_columns, header=0)

iperf2_udp_columns = ['unix_timestamp','local_addr','local_port','remote_addr','remote_port','duration','transfer_amount','transfer_rate','jitter_ms','lost_packets','total_packets']
iperf2_10m_udp_server_report_ams_client = pd.read_csv("iperf2-10m-udp-server_report-ams-client.csv", names=iperf2_udp_columns, header=0)
iperf2_10m_udp_server_report_par_client = pd.read_csv("iperf2-10m-udp-server_report-par-client.csv", names=iperf2_udp_columns, header=0)
iperf2_10m_udp_server_report_oregon_client = pd.read_csv("iperf2-10m-udp-server_report-oregon-client.csv", names=iperf2_udp_columns, header=0)

iperf2_tcp_ams_client = pd.read_csv("iperf2-tcp-ams-client.csv", names=iperf2_tcp_columns, header=0)
iperf2_tcp_par_client = pd.read_csv("iperf2-tcp-par-client.csv", names=iperf2_tcp_columns, header=0)
iperf2_tcp_oregon_client = pd.read_csv("iperf2-tcp-oregon-client.csv", names=iperf2_tcp_columns, header=0)

iperf2_udp_server_report_ams = pd.read_csv("iperf2-udp-server_report-ams-client.csv", names=iperf2_udp_columns, header=0)
iperf2_udp_server_report_par = pd.read_csv("iperf2-udp-server_report-par-client.csv", names=iperf2_udp_columns, header=0)
iperf2_udp_server_report_oregon = pd.read_csv("iperf2-udp-server_report-oregon-client.csv", names=iperf2_udp_columns, header=0)

iperf2_udp_server_report_ams = pd.read_csv("iperf2-udp-server_report-ams-client.csv", names=iperf2_udp_columns, header=0)
iperf2_udp_server_report_par = pd.read_csv("iperf2-udp-server_report-par-client.csv", names=iperf2_udp_columns, header=0)
iperf2_udp_server_report_oregon = pd.read_csv("iperf2-udp-server_report-oregon-client.csv", names=iperf2_udp_columns, header=0)

iperf3_udp_columns = ['unix_timestamp','remote_addr','jitter_ms','transfer_amount','duration','lost_packets','total_packets']
iperf3_10m_udp_ams_client = pd.read_csv("iperf3-10m-udp-ams-client.csv", names=iperf3_udp_columns, header=0)
iperf3_10m_udp_par_client = pd.read_csv("iperf3-10m-udp-par-client.csv", names=iperf3_udp_columns, header=0)
iperf3_10m_udp_oregon_client = pd.read_csv("iperf3-10m-udp-oregon-client.csv", names=iperf3_udp_columns, header=0)

iperf3_udp_ams_client = pd.read_csv("iperf3-udp-ams-client.csv", names=iperf3_udp_columns, header=0)
iperf3_udp_par_client = pd.read_csv("iperf3-udp-par-client.csv", names=iperf3_udp_columns, header=0)
iperf3_udp_oregon_client = pd.read_csv("iperf3-udp-oregon-client.csv", names=iperf3_udp_columns, header=0)

iperf3_tcp_columns = ['unix_timestamp','remote_addr','transfer_amount','transfer_rate','duration']
iperf3_tcp_ams_client = pd.read_csv("iperf3-tcp-ams-client.csv", names=iperf3_tcp_columns, header=0)
iperf3_tcp_par_client = pd.read_csv("iperf3-tcp-par-client.csv", names=iperf3_tcp_columns, header=0)
iperf3_tcp_oregon_client = pd.read_csv("iperf3-tcp-oregon-client.csv", names=iperf3_tcp_columns, header=0)

#scatter(iperf3_tcp_oregon_client)
#scatter(iperf3_udp_oregon_client)

#scatter(iperf2_tcp_ams_client)
#scatter(iperf2_tcp_oregon_client)
ratebydate(iperf3_tcp_oregon_client, iperf2_tcp_oregon_client, 'Android -> Oregon')
ratebydate(iperf3_tcp_ams_client, iperf2_tcp_ams_client, 'AMS -> PAR', scale=1e8)
ratebydate(iperf3_tcp_par_client, iperf2_tcp_par_client, 'PAR -> AMS', scale=1e8)

jitterbydate(iperf3_udp_oregon_client, iperf2_udp_server_report_oregon, 'Android -> Oregon')
jitterbydate(iperf3_10m_udp_oregon_client, iperf2_10m_udp_server_report_oregon_client, 'Android -> Oregon (10mbit)')
jitterbydate(iperf3_10m_udp_ams_client, iperf2_10m_udp_server_report_ams_client, 'AMS -> PAR (10mbit)')

packetlossbydate(iperf3_udp_oregon_client, iperf2_udp_server_report_oregon, 'Android -> Oregon')
packetlossbydate(iperf3_10m_udp_oregon_client, iperf2_10m_udp_server_report_oregon_client, 'Android -> Oregon (10mbit)')

packetlossbydate(iperf3_udp_ams_client, iperf2_udp_server_report_ams, 'AMS -> PAR')
packetlossbydate(iperf3_10m_udp_ams_client, iperf2_10m_udp_server_report_ams_client, 'AMS -> PAR (10mbit)')

packetlossbydate(iperf3_udp_par_client, iperf2_udp_server_report_par, 'PAR -> AMS')
packetlossbydate(iperf3_10m_udp_par_client, iperf2_10m_udp_server_report_par_client, 'PAR -> AMS (10mbit)')
