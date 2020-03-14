package main

import (
	"fmt"
	"math/rand"
	"time"
	"strings"
)

const (
	testInterval = 1*time.Second
)

var (
	server_address = "192.168.64.3"
	commands = [...]string{
		"iperf -c '%s' -yC",		// iPerf 2 TCP, default options
		"iperf3 -c '%s' -J",		// iPerf 3 TCP, default options
		"iperf -c '%s' -u -yC",		// iPerf 2 UDP, default options
		"iperf3 -c '%s' -u -J",		// iPerf 3 UDP, default options
	}
)

func runTests() {
	// Each time the tests are run, we randomize the order of the commands.
	rand.Seed(time.Now().UnixNano())
	idxArray := rand.Perm(len(commands))
	
	for i := range idxArray {
		command := strings.Split(fmt.Sprintf(commands[idxArray[i]], server_address), " ")
		fmt.Println(command)
	}
}

func main() {
	for {
		select {
			case <-time.After(testInterval):
				go runTests()
		}
	}
}