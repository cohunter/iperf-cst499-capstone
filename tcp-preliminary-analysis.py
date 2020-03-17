# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

i2 = pd.read_csv("iperf2-tcp.csv", header=None, names=["unixtime", "remote_host", "transfer_amount", "amount_magnitude", "seconds", "transfer_rate", "rate_magnitude"])
i2.remote_host = i2.remote_host.str.replace('::ffff:', '')

# Convert the transfer_amount and amount_magnitude to bytes
multipliers = {
    "MBytes": 1024*1024,
    "KBytes": 1024,
    "Bytes": 1
    }
datas = []
for key in i2.amount_magnitude.value_counts().keys():
    print(key)
    print(multipliers[key])
    print((i2[i2.amount_magnitude == key].transfer_amount * multipliers[key]).round(0).astype(int))
    datas.append((i2[i2.amount_magnitude == key].transfer_amount * multipliers[key]).round(0).astype(int))

i2["bytes"] = pd.concat(datas).sort_index()

# Convert the transfer_rate and rate_magnitude to bytes
multipliers = {
    "Mbits": 1000*1000,
    "Kbits": 1000,
    "bits": 1
    }
datas = []
for key in i2.rate_magnitude.value_counts().keys():
    print(key)
    print(multipliers[key])
    print((i2[i2.rate_magnitude == key].transfer_rate * multipliers[key]).round(0).astype(int))
    datas.append((i2[i2.rate_magnitude == key].transfer_rate * multipliers[key]).round(0).astype(int))
    
i2['bits_per_second'] = pd.concat(datas).sort_index()
i2.drop(['transfer_amount', 'amount_magnitude', 'transfer_rate', 'rate_magnitude'], axis=1, inplace=True)
i2 = i2[i2.columns.tolist()[0:2] + i2.columns.tolist()[3:] + i2.columns.tolist()[2:3]]
i2['unixtime'] = pd.to_datetime(i2['unixtime'], unit='s')

i3 = pd.read_csv("iperf3-tcp.csv", header=None, names=["unixtime", "remote_host", "bytes", "bits_per_second", "seconds"])
i3['unixtime'] = pd.to_datetime(i3['unixtime'], unit='s')

i2.set_index(i2.unixtime, inplace=True)
i3.set_index(i3.unixtime, inplace=True)

i2 = i2[i2.unixtime > '2020-03-05']
i3 = i3[i3.unixtime > '2020-03-05']

# Filter to our test IP only
i2 = i2.groupby('remote_host').get_group('209.141.36.43')
i3 = i3.groupby('remote_host').get_group('209.141.36.43')

plt.rcParams['figure.figsize'] = (16,6)
fig, ax = plt.subplots(1, 2, sharey=True, sharex=True)
fig.suptitle('Transfer Rate and Totals')
i3.bits_per_second.plot(ax=ax[0], color='r', alpha=0.9)
i3.bytes.plot(ax=ax[0], alpha=0.7)
ax[0].plot(i3.unixtime, [i3.bits_per_second.mean()]*len(i3.unixtime), color='y', label='Mean', alpha=0.9)
ax[0].annotate(' '+str(round(i3.bits_per_second.mean()/1e8,2)), xy=(ax[0].get_xlim()[1], i3.bits_per_second.mean()), xycoords='data', textcoords='offset points', xytext=(0,0))
ax[0].plot(i3.unixtime, [i3.bits_per_second.median()]*len(i3.unixtime), color='g', label='Median', alpha=0.9)
ax[0].annotate(' '+str(round(i3.bits_per_second.median()/1e8,2)), xy=(ax[0].get_xlim()[1], i3.bits_per_second.median()), xycoords='data', textcoords='offset points', xytext=(0,0))
ax[0].set_xlabel('iPerf 3')
ax[0].legend(['bits per second','bytes transferred', 'mean (bits per second)', 'median (bits per second)'])
i2.bits_per_second.plot(ax=ax[1], color='r', alpha=0.9)
i2.bytes.plot(ax=ax[1], alpha=0.7)
ax[1].plot(i2.unixtime, [i2.bits_per_second.mean()]*len(i2.unixtime), color='y', label='Mean', alpha=0.9)
ax[1].annotate(' '+str(round(i2.bits_per_second.mean()/1e8,2)), xy=(ax[1].get_xlim()[0], i2.bits_per_second.mean()), xycoords='data', textcoords='offset points', xytext=(0,0))
ax[1].plot(i2.unixtime, [i2.bits_per_second.median()]*len(i2.unixtime), color='g', label='Median', alpha=0.9)
ax[1].annotate(' '+str(round(i2.bits_per_second.median()/1e8,2)), xy=(ax[1].get_xlim()[0], i2.bits_per_second.median()), xycoords='data', textcoords='offset points', xytext=(0,0))
ax[1].set_xlabel('iPerf 2')
ax[1].legend(['bits per second', 'bytes transferred', 'mean (bits per second)', 'median (bits per second)'])
plt.show()

fig, ax = plt.subplots(1,1)
plt.title('Transfer rate (bits per second)')
i3.plot.scatter(ax=ax,x='unixtime', y='bits_per_second', xlim=(i2.unixtime.min(), i2.unixtime.max()), alpha=0.5)
i2.plot.scatter(ax=ax,x='unixtime', y='bits_per_second', xlim=(i2.unixtime.min(), i2.unixtime.max()), alpha=0.5, color='r')
ax.legend(['iPerf 3','iPerf 2'])
ax.set_xlabel('Date')
ax.set_ylabel('Bits per second (1e8)')
plt.show()

fig, ax = plt.subplots(1,1)
plt.title('Transfer totals (bytes)')
i3.plot.scatter(ax=ax,x='unixtime', y='bytes', xlim=(i2.unixtime.min(), i2.unixtime.max()), alpha=0.5)
i2.plot.scatter(ax=ax,x='unixtime', y='bytes', xlim=(i2.unixtime.min(), i2.unixtime.max()), alpha=0.5, color='r')
ax.legend(['iPerf 3','iPerf 2'])
ax.set_xlabel('Date')
ax.set_ylabel('Bytes (1e8)')
plt.show()
