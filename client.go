package main

import (
	"fmt"
	"math/rand"
	"time"
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
	rand.Seed(time.Now().UnixNano())
	idxArray := rand.Perm(len(commands))

	// Each time the tests are run, we randomize the order of the commands.
	for i := 0; i < len(commands); i++ {
		command := fmt.Sprintf(commands[idxArray[i]], server_address)
		fmt.Println(command)
	}
}