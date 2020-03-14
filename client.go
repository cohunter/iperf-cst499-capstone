package main

import (
	"fmt"
	"log"
	"math/rand"
	"time"
	"strings"
	"os/exec"
)

const (
	testInterval = 1*time.Hour
)

var (
	server_address = "192.168.64.3"
	commands = [...]string{
		"iperf -c %s -yC -t 1",		// iPerf 2 TCP, default options
		"iperf3 -c %s -J -t 1",		// iPerf 3 TCP, default options
		"iperf -c %s -u -yC -t 1",		// iPerf 2 UDP, default options
		"iperf3 -c %s -u -J -t 1",		// iPerf 3 UDP, default options
	}
)

func runTests() {
	// Each time the tests are run, we randomize the order of the commands.
	rand.Seed(time.Now().UnixNano())
	idxArray := rand.Perm(len(commands))
	
	for i := range idxArray {
		command := strings.Split(fmt.Sprintf(commands[idxArray[i]], server_address), " ")
		cmd := exec.Command(command[0], command[1:]...)
		output, err := cmd.CombinedOutput()
		if err != nil {
		    log.Println(fmt.Sprint(err) + ": " + string(output))
		    continue
		}
		switch command[0] {
			case "iperf3":
				log.Println("iPerf 3 Result")
				log.Println(string(output))
			case "iperf":
				log.Println("iPerf 2 Result")
				log.Println(string(output))
		}

	}
}

func main() {
	go runTests()
	for {
		select {
			case <-time.After(testInterval):
				go runTests()
		}
	}
}