# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 14:32:15 2020

@author: User
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def reindex(df):
    df['unix_timestamp'] = pd.to_datetime(df['unix_timestamp'], unit='s')
    df.set_index(df['unix_timestamp'], inplace=True)

def scatter(df):
    pd.plotting.scatter_matrix(df, figsize=(24,16))

def ratebydate(df1, df2, title, scale=1e7):
    reindex(df1)
    reindex(df2)
    
    print(len(df1), len(df2))
    
    plt.rcParams['figure.figsize'] = (16,6)
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
    
    
    ax[1].set_xlabel('Percent difference iPerf 3 vs iPerf 2, mean bits per second: {:.3}%'.format(((df1['transfer_rate'].mean() / df2['transfer_rate'].mean())-1)*100))

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

scatter(iperf2_tcp_ams_client)
#scatter(iperf2_tcp_oregon_client)
#ratebydate(iperf3_tcp_oregon_client, iperf2_tcp_oregon_client, 'Android -> Oregon')
#ratebydate(iperf3_tcp_ams_client, iperf2_tcp_ams_client, 'AMS -> PAR', scale=1e8)
#ratebydate(iperf3_tcp_par_client, iperf2_tcp_par_client, 'PAR -> AMS', scale=1e8)