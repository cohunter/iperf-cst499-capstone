package main

import (
	"fmt"
	"log"
	"math/rand"
	"time"
	"strings"
	"os/exec"
	"net/http"
	"net/url"
)

const (
	testInterval = 1*time.Hour
	dataUploadUrl = "https://phone_home.regex.be/ingest/client-results-iperf"
)

var (
	server_address = "54.212.26.193"
	commands = [...]string{
		"iperf -c %s -yC -p 5002",		// iPerf 2 TCP, default options
		"iperf3 -c %s -J -p 5009",		// iPerf 3 TCP, default options
		"iperf -c %s -u -yC -p 5002",		// iPerf 2 UDP, default options
		"iperf3 -c %s -u -J -p 5009",		// iPerf 3 UDP, default options
		"iperf3 -c %s -J -u -b 10m -p 5009",	// iPerf 3 UDP, 10mbit bandwidth target
		"iperf -c %s -yC -u -b 10m -p 5002",	// iPerf 2 UDP, 10mbit bandwidth target
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
		resp, err := http.PostForm(dataUploadUrl,
			url.Values{"command": {commands[idxArray[i]]}, "output": {string(output)}})
		if err != nil {
			log.Println(fmt.Sprint(err))
		}
		resp.Body.Close()
		switch command[0] {
			case "iperf3":
				log.Println("iPerf 3 Result Captured")
			case "iperf":
				log.Println("iPerf 2 Result Captured")
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
