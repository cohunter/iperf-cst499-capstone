# iperf-cst499-capstone

## Server Setup

    multipass launch -n iperf --cloud-init cloud-init.yaml

* Downloads and builds iPerf 2.0.13 & iPerf 3.7 from git
* Runs multiple instances of iPerf2 and iPerf3 under metasrv

## Metasrv

* Runs commands and parses output to CSV for data analysis
* See `metasrv.go`
