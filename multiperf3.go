package main

// What's this?
// A magical (not really) server multiplexer for iPerf 3 instances [TCP]

// Why is this?
// iPerf 3 is single-threaded and will only accept one client at a time.
// This program allows to run N iperf3 instances and split connections
// between them transparently (to the clients) based on the client IP.
// By default go will run as many processes as the server has logical CPU cores.
// Supports clients using -P, but note this is intended to provide for multiple
// low-speed clients rather than multiple connections from a single fast client.
// For high-speed clients, see:
// https://fasterdata.es.net/performance-testing/network-troubleshooting-tools/iperf/multi-stream-iperf3/

// How does it work?
// Rather than failing immediately, iPerf 3 clients will wait patiently
// for an iPerf 3 server to become available. If no server becomes
// available within waitSeconds, the client will be rejected.

// Set as many iPerf 3 instances in upstream_addrs as make sense for conditions.

// Author: Corey Hunter
// License: CC0-1.0, or 0BSD where CC0 not applicable
// https://spdx.org/licenses/CC0-1.0.html
// https://spdx.org/licenses/0BSD.html

import (
	"io"
	"log"
	"net"
	"time"
)

const (
	waitSeconds   = 11
	listenAddress = ":5201"
)

var (
	upstream_addrs = [...]string{
		"192.168.64.3:5202",
		"127.0.0.1:5203",
		"127.0.0.1:5204",
	}
	client_map = make(map[string]*client)
)

type client struct {
	ip          string
	upstream    string
	connections int
	rejected    bool
}

func gotClient(addr net.Conn) *client {
	remoteIP, _, err := net.SplitHostPort(addr.RemoteAddr().String())
	if err != nil {
		log.Fatal(err)
	}
	if currentClient, ok := client_map[remoteIP]; ok {
		currentClient.connections += 1
		return currentClient
	}

	currentClient := client{ip: remoteIP, connections: 1}
	client_map[currentClient.ip] = &currentClient
	return &currentClient
}

func pro(c net.Conn, s net.Conn) {
	go io.Copy(c, s)
	io.Copy(s, c)
}

func upstream(clientConn net.Conn, hosts chan string) {
	currentClient := gotClient(clientConn)

	if len(currentClient.upstream) == 0 {
		log.Println("New connection received", currentClient.ip)
		select {
		// Wait up to 11 seconds for an upstream to become available.
		// Default test duration is 10 seconds.
		case <-time.After(waitSeconds * time.Second):
			log.Println("No upstream available, will refuse test.")
			currentClient.upstream = upstream_addrs[0]
			currentClient.rejected = true
		case currentClient.upstream = <-hosts:
			log.Println("Got upstream:", currentClient.upstream)
			// Give the iPerf 3 process time to accept new client
			<-time.After(100 * time.Millisecond)
		}

		log.Println("Upstream selected", currentClient.upstream, "for", currentClient.ip)
	} else {
		log.Println("Re-using upstream", currentClient.upstream, "for client", currentClient.ip, "total connections:", currentClient.connections)
	}

	serverConn, err := net.Dial("tcp", currentClient.upstream)
	if err != nil {
		clientConn.Close()
		log.Fatal(err) // If the upstream is not available, exit.
	}
	defer serverConn.Close()
	defer clientConn.Close()

	pro(clientConn, serverConn)
	currentClient.connections -= 1
	if currentClient.connections < 1 {
		if !currentClient.rejected {
			hosts <- currentClient.upstream
			log.Println("Free'd upstream:", currentClient.upstream)
		}
		delete(client_map, currentClient.ip)
	}
}

func main() {
	l, err := net.Listen("tcp", listenAddress)
	if err != nil {
		log.Fatal(err)
	}
	defer l.Close()

	hosts := make(chan string, len(upstream_addrs))
	for _, host := range upstream_addrs {
		hosts <- host
	}

	for {
		conn, err := l.Accept()
		if err != nil {
			log.Fatal(err)
		}

		go upstream(conn, hosts)
	}
}
