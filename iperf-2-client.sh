#!/bin/bash
mkdir -p /iperf-2-results
export FILE=$(mktemp -p "/iperf-2-results")
export TIME=$(date '+%s')

iperf -c 198.98.48.214 2>&1 1>"$FILE"
export ROW=$(awk '/[KMG]bits/ { print $5 "," $7 }' "$FILE")

# rm "$FILE"

# results.csv contains rows of transfer amount, bandwidth (throughput)
echo "$ROW,$TIME"  >> /root/results.csv

