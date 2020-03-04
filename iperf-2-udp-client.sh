#!/bin/bash
mkdir -p /iperf-2-udp
export FILE=$(mktemp -p "/iperf-2-udp/")
export TIME=$(date '+%s')

iperf -c 198.98.48.214 -u -b 10m 2>&1 1>"$FILE"
#export ROW=$(awk '/Mbits/ { print $5 "," $7 }' "$FILE")
# Transferred, bandwidth, jitter, lost, total
export ROW=$(awk 'BEGIN { OFS="," } /\%\)/ { print $5,$7,$9,$11,$12 }' "$FILE")

# results.csv contains rows of transfer amount, bandwidth (throughput)
echo "$ROW,$TIME"  >> /root/results-2-udp.csv

