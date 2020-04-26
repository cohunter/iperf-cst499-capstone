# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 08:18:48 2020

@author: cohunter
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import local_utils

i2 = pd.read_csv("iperf2-udp.csv")
i3 = pd.read_csv("iperf3-udp.csv")



def show_columns():
    print("iPerf 2 columns:")
    print(i2.columns.values)
    
    print("iPerf 3 columns:")
    print(i3.columns.values)

show_columns()

merged = local_utils.reindex_and_merge(i2, i3, col='Time')

local_utils.compare_std(merged)
local_utils.compare_percentiles(merged)
#local_utils.compare_percentiles(merged, percentile=100)
local_utils.scatter_by_date(merged)
local_utils.scatter_by_date(merged, col='lost_packets', title='Lost Packets by Date', label='Lost Packets (count)', dotscale=10)
