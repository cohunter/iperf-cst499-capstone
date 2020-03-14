package main

import (
	"fmt"
)

var (
	server_address = "198.98.48.214"
	commands = [...]string{
		"iperf -c '%s'",		// iPerf 2 TCP, default options
		"iperf3 -c '%s'",		// iPerf 3 TCP, default options
		"iperf -c '%s' -u",		// iPerf 2 UDP, default options
		"iperf3 -c '%s' -u",	// iPerf 3 UDP, default options
	}
)

func main() {
	fmt.Println(len(commands))
	for _, e := range commands {
		fmt.Printf(e, server_address)
		fmt.Println()
	}
}