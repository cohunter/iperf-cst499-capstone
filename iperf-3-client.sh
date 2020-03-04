#!/bin/bash
mkdir -p /iperf-3-results
export FILE=$(mktemp -p "/iperf-3-results")
export TIME=$(date '+%s')

iperf3 -c 198.98.48.214 2>&1 1>"$FILE"
sleep 1
#export ROW=$(awk '/Mbits/ { print $5 "," $7 }' "$FILE")
export ROW=$(awk '/sender/ {print $5","$7}' test)

# rm "$FILE"

# results.csv contains rows of transfer amount, bandwidth (throughput)

echo "$ROW,$TIME"  >> /root/3-results.csv

#sleep 10

### UDP
mkdir -p /iperf3-udp-results
export UDPFILE=$(mktemp -p /iperf3-udp-results)
export TIME=$(date '+%s')

iperf3 -c 198.98.48.214 -u -b 10m 2>&1 >"$UDPFILE"
# Transferred (MB), Bandwidth (Mbps), Jitter (ms), Lost/Total Datagrams
export ROW=$(awk 'BEGIN { OFS="," } /\(/ { print $5,$7,$9,$11}' "$UDPFILE")

echo "$ROW,$TIME" >> /root/3-udp-results.csv
