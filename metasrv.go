package main

import (
	"bufio"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

type command struct {
	Cmdline []string
	Retries int
}

var (
	// Must specify port explicitly for iPerf 2 so that reverse tests can be checked
	commands = [...]string{
		"iperf3 -s -J -p 5009 -I /tmp/iperf3.pid", // iperf 3 handles tcp/udp & multiple clients
		"iperf -s -u -yC -V -p 5001",                  // iperf 2 udp, ipv4/6
		"iperf -s -yC -V -p 5001",                     // iperf 2 tcp, ipv4/6
		"iperf -s -yC -V -p 5002",             // iperf 2 tcp alternate port
		"iperf -s -yC -u -V -p 5002",          // iperf 2 udp alternate port
	}

	wg sync.WaitGroup
)

func jsonHandler(jsonStream io.Reader, srcCmd command) {
	type iperf3output struct {
		Start struct {
			Version     string
			System_info string
			Timestamp   struct {
				Time     string
				Timesecs int64
			}
			Test_start struct {
				Protocol    string
				Num_streams int
				Blksize     int
				Duration    int
				Reverse     int
			}
			Connected []struct {
				Socket      int
				Local_host  string
				Local_port  int32
				Remote_port int32
				Remote_host string
			}
			Accepted_connection struct {
				Host string
				Port int32
			}
			Cookie          string
			Tcp_mss_default int
		}
		Intervals []struct {
			Streams []struct {
				Socket          int
				Start           float64
				End             float64
				Seconds         float64
				Bytes           int64
				Bits_per_second float64
				Omitted         bool
			}
			Sum struct {
				Start           float64
				End             float64
				Seconds         float64
				Bytes           int64
				Bits_per_second float64
				Omitted         bool
			}
		}
		End struct {
			Streams []struct {
				Sender struct {
					Socket          int
					Start           float64
					End             float64
					Seconds         float64
					Bytes           int64
					Bits_per_second float64
				}
				Receiver struct {
					Socket          int
					Start           float64
					End             float64
					Seconds         float64
					Bytes           int64
					Bits_per_second float64
				}
			}
			// UDP-Only
			Sum struct {
				Start           float64
				End             float64
				Seconds         float64
				Bytes           int64
				Bits_per_second float64
				Jitter_ms       float64
				Lost_packets    int64
				Packets         int64
				Lost_percent    float64
			}
			Sum_sent struct {
				Start           float64
				End             float64
				Seconds         float64
				Bytes           int64
				Bits_per_second float64
			}
			Sum_received struct {
				Start           float64
				End             float64
				Seconds         float64
				Bytes           int64
				Bits_per_second float64
			}
			Cpu_utilization_percent struct {
				Host_total    float64
				Host_user     float64
				Host_system   float64
				Remote_total  float64
				Remote_user   float64
				Remote_system float64
			}
		}
	}

	var jsonStr strings.Builder

	scanner := bufio.NewScanner(jsonStream)

	go func() {
		for scanner.Scan() {
			outputLine := scanner.Text()

			jsonStr.WriteString(outputLine)
			//log.Println(outputLine)

			// Read until a closing }, then attempt to parse the JSON
			if outputLine == "}" {
				jso := jsonStr.String() // Don't name this json

				jsonStr.Reset()
				m := iperf3output{}
				if err := json.Unmarshal([]byte(jso), &m); err != nil {
					log.Println("Can't decode JSON")
					log.Fatal(err)
				}

				switch protocol := m.Start.Test_start.Protocol; protocol {
				case "TCP":
					// Do something with TCP result data
					log.Printf("Received iPerf 3 TCP test results from %s", m.Start.Accepted_connection.Host)
					unixtime := strconv.FormatInt(time.Now().Unix(), 10)
					fn := "iperf3-tcp.csv"
					if m.Start.Test_start.Reverse == 1 {
						log.Printf("This is a REVERSE iPerf 3 TCP test result.")
						fn = "iperf3-tcp-reverse.csv"
					}

					f, err := os.OpenFile(fn, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
					if err != nil {
						log.Fatalf("Can't open CSV output file for iPerf 3 TCP test: %s", err)
					}
					w := csv.NewWriter(f)

					//if m.Start.Test_start.Reverse == 0 {
						sr := m.End.Sum_received
						if err := w.Write([]string{unixtime, m.Start.Accepted_connection.Host, fmt.Sprintf("%d", sr.Bytes), fmt.Sprintf("%f", sr.Bits_per_second), fmt.Sprintf("%f", sr.Seconds)}); err != nil {
							log.Fatal("Can't write to CSV output for iPerf 3 TCP test.")
						}
					//} else {
					//	log.Print("Reverse test result discarded -- not supported by iPerf 2")
					//}
					w.Flush()
					if err := w.Error(); err != nil {
						log.Fatalf("Can't write to CSV output for iPerf 3 TCP test: %s", err)
					}
					f.Close()
				case "UDP":
					// Do something with UDP result data
					log.Printf("Received iPerf 3 UDP test results from %s", m.Start.Accepted_connection.Host)
					unixtime := strconv.FormatInt(time.Now().Unix(), 10)
					fn := "iperf3-udp.csv"
					if m.Start.Test_start.Reverse == 1 {
						log.Printf("This is a REVERSE iPerf 3 UDP test result.")
						fn = "iperf3-udp-reverse.csv"
					}
					f, err := os.OpenFile(fn, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
					if err != nil {
						log.Fatalf("Can't open CSV output file for iPerf 3 UDP test: %s", err)
					}
					w := csv.NewWriter(f)
					//if m.Start.Test_start.Reverse == 0 {
						sr := m.End.Sum
						if err := w.Write([]string{unixtime, m.Start.Accepted_connection.Host, fmt.Sprintf("%f", sr.Jitter_ms), fmt.Sprintf("%d", sr.Bytes), fmt.Sprintf("%f", sr.Seconds), fmt.Sprintf("%d", sr.Lost_packets), fmt.Sprintf("%d", sr.Packets)}); err != nil {
							log.Fatal("Can't write to CSV output for iPerf 3 UDP test.")
						}
						log.Println("iperf3-udp columns: unix_time | host | jitter_ms | bytes_transferred | seconds | lost_packets | total_packets")
					//} else {
					//	log.Print("Reverse test result discarded -- not supported by iPerf 2")
					//}
					w.Flush()
					if err := w.Error(); err != nil {
						log.Fatalf("Can't write to CSV output for iPerf 3 UDP test: %s", err)
					}
					f.Close()
				}
			}
		}
		log.Print("iPerf 3 has exited")
		srcCmd.Retries += 1

		go handleCommand(srcCmd)
		wg.Done()
	}()
	return
}

func csvParser(output io.Reader, srcCmd command) {
	log.Printf("iPerf2 CSV %+v", srcCmd)
	scanner := csv.NewReader(output)
	scanner.FieldsPerRecord = -1 // iPerf2 CSV outout has two different lengths on client, also different for tcp, udp
	go func() {
		for {
			record, err := scanner.Read()
			if err == io.EOF {
				break
			}
			if err != nil {
				log.Println(err)
				break
			}
			
			unixtime := strconv.FormatInt(time.Now().Unix(), 10)
			
			switch len(record) {
				case 9: // TCP Result
				// [Datetime, Host_addr, Host_port, Client_addr, Client_port, Transfer_id, Duration, Transferred, Transfer_rate]
					log.Println("iPerf 2 TCP Result received from", record[3])
					fn := "iperf2-tcp-reverse.csv"
					
					// Check if host port is the same as given in command line
					for _, e := range srcCmd.Cmdline {
						if e == record[2] {
							fn = "iperf2-tcp.csv"
						}
					}
					if fn == "iperf2-tcp-reverse.csv" {
						log.Println("This is a REVERSE iPerf 2 TCP test.")
					}
					f, err := os.OpenFile(fn, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
					if err != nil {
						log.Fatalf("Can't open CSV output file for iPerf 2 TCP test: %s", err)
					}
					w := csv.NewWriter(f) // unixtime, host_addr, host_port, client_addr, client_port, duration, transfer_amount, bandwidth
					if err := w.Write([]string{unixtime, record[1], record[2], record[3], record[4], record[6], record[7], record[8]}); err != nil {
						log.Fatal("Can't write to CSV output for iPerf 2 TCP test.")
					}
					w.Flush()
					if err := w.Error(); err != nil {
						log.Fatalf("Can't write to CSV output for iPerf 2 TCP test: %s", err)
					}
					f.Close()

				case 14: // UDP Result
				// [Datetime, Host_addr, Host_port, Client_addr, Client_port, Transfer_id, Duration, Transferred, Transfer_rate, Jitter_ms, Lost_packets, Total_packets, Lost_pct, is_reversed]
					log.Println("iPerf 2 UDP Result received from", record[3])
					fn := "iperf2-udp.csv"
					if record[13] == "1" {
						fn = "iperf2-udp-reverse.csv"
						log.Println("This is a REVERSE iPerf 2 UDP test.")
					}
					f, err := os.OpenFile(fn, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
					if err != nil {
						log.Fatalf("Can't open CSV output file for iPerf 2 UDP test: %s", err)
					}
					w := csv.NewWriter(f) // unixtime, host_addr, host_port, client_addr, client_port, duration, transfer_amount, bandwidth, jitter, lost, total
					if err := w.Write([]string{unixtime, record[1], record[2], record[3], record[4], record[6], record[7], record[8], record[9], record[10], record[11]}); err != nil {
						log.Fatal("Can't write to CSV output for iPerf 2 UDP test.")
					}
					w.Flush()
					if err := w.Error(); err != nil {
						log.Fatalf("Can't write to CSV output for iPerf 2 UDP test: %s", err)
					}
					f.Close()
				default:
					log.Println("%d", len(record))
			}
			log.Println(record)
		}
		
		// The child process has exited. Let's try to restart it.
		srcCmd.Retries += 1
		log.Print("iPerf 2 has exited")
		go handleCommand(srcCmd)
		wg.Done()
	}()
}

func checkRegexp(re *regexp.Regexp, outputLine string) (matchmap map[string]string) {
	matchmap = make(map[string]string)
	matches := re.FindStringSubmatch(outputLine)
	if len(matches) > 0 {
		//log.Printf("Got regexp match: %+v", matches)

		for i, name := range re.SubexpNames() {
			if i == 0 || name == "" {
				continue
			}
			matchmap[name] = matches[i]
		}
		//log.Printf("%+v", matchmap)
	}
	return matchmap
}

func textParser(output io.Reader, srcCmd command) {
	log.Printf("iperf 2 %+v", srcCmd)
	scanner := bufio.NewScanner(output)

	// Each instance of textParser will have its own clients map
	clients := make(map[string]map[string]string)
	go func() {
		for scanner.Scan() {
			outputLine := scanner.Text()
			log.Println(outputLine)

			// for results of re.FindStringSubmatch, matches[0] is the full string and [1]... are the named groups
			re_start := regexp.MustCompile(`Server listening on (?P<proto>\w+) port (?P<port>\d+)`)
			matches := checkRegexp(re_start, outputLine)
			if len(matches) > 0 {
				log.Printf("Started iPerf 2 server of type %s on port %s", matches["proto"], matches["port"])
			}

			// matches:
			// client_number
			// server ip
			// server port
			// client ip
			// client port
			re_connect := regexp.MustCompile(`\[  ?(?P<client_number>\d?\d)\] local (?P<server_addr>[:\da-f\.]+) port (?P<server_port>\d+) connected with (?P<client_addr>[:\da-f\.]+) port (?P<client_port>\d+)`)
			matches = checkRegexp(re_connect, outputLine)
			if len(matches) > 0 {
				clients[matches["client_number"]] = matches
				log.Printf("Received iPerf 2 connection from %s source port %s", matches["client_addr"], matches["client_port"])
			}

			// matches:
			// client_number (reused)
			// test duration (seconds, float)
			// transferred (number, maybe float)
			// transferred (string, KBytes or Mbytes or Gbytes)
			// bandwidth (number, maybe float)
			// bandwidth (string, Gbits or Mbits or Kbits [/sec])
			// jitter (float)
			// jitter (string, ms)
			// lost datagrams (number, int)
			// total datagrams (number, int)
			re_udp_results := regexp.MustCompile(`\[  ?(?P<client_number>\d?\d)\]\s+0.0-\s*?(?P<duration>[\d\.]+)\s+sec\s+(?P<transfer_amount>[\d\.]+)\s+(?P<transfer_magnitude>\w+)\s+(?P<bandwidth>[\d\.]+)\s+(?P<bandwidth_magnitude>[\w]+)\/sec\s+(?P<jitter>[\d\.]+)\s+(?P<jitter_magnitude>\w+)\s+(?P<lost_datagrams>\d+)\/\s*?(?P<total_datagrams>\d+)`)
			matches = checkRegexp(re_udp_results, outputLine)
			if len(matches) > 0 {
				client := clients[matches["client_number"]]
				delete(clients, matches["client_number"])
				//log.Printf("%+v", client)
				//log.Printf("%+v", matches)
				log.Printf("Got iPerf 2 UDP test results from %s (%s %s jitter) %s %s transferred in %s seconds, %s/%s Lost/Total Datagrams", client["client_addr"], matches["jitter"], matches["jitter_magnitude"], matches["transfer_amount"], matches["transfer_magnitude"], matches["duration"], matches["lost_datagrams"], matches["total_datagrams"])

				unixtime := strconv.FormatInt(time.Now().Unix(), 10)
				f, err := os.OpenFile("iperf2-udp.csv", os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
				if err != nil {
					log.Fatalf("Can't open CSV output file for iPerf 2 UDP test: %s", err)
				}
				w := csv.NewWriter(f) //
				if err := w.Write([]string{unixtime, client["client_addr"], matches["jitter"], matches["jitter_magnitude"], matches["transfer_amount"], matches["transfer_magnitude"], matches["duration"], matches["lost_datagrams"], matches["total_datagrams"]}); err != nil {
					log.Fatal("Can't write to CSV output for iPerf 2 UDP test.")
				}
				w.Flush()
				if err := w.Error(); err != nil {
					log.Fatalf("Can't write to CSV output for iPerf 2 UDP test: %s", err)
				}
				f.Close()
			}

			re_tcp_results := regexp.MustCompile(`\[  ?(?P<client_number>\d?\d)\]\s+0.0-\s*?(?P<duration>[\d\.]+)\s+sec\s+(?P<transfer_amount>[\d\.]+)\s+(?P<transfer_magnitude>\w+)\s+(?P<bandwidth>[\d\.]+)\s+(?P<bandwidth_magnitude>[\w]+)\/sec$`)
			matches = checkRegexp(re_tcp_results, outputLine)
			if len(matches) > 0 {
				client := clients[matches["client_number"]]
				delete(clients, matches["client_number"])
				//log.Printf("%+v", client)
				//log.Printf("%+v", matches)
				log.Printf("Got iPerf 2 TCP test results from %s (%s %s transferred in %s seconds, %s %s/sec)", client["client_addr"], matches["transfer_amount"], matches["transfer_magnitude"], matches["duration"], matches["bandwidth"], matches["bandwidth_magnitude"])

				unixtime := strconv.FormatInt(time.Now().Unix(), 10)
				f, err := os.OpenFile("iperf2-tcp.csv", os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
				if err != nil {
					log.Fatalf("Can't open CSV output file for iPerf 2 TCP test: %s", err)
				}
				w := csv.NewWriter(f) //
				if err := w.Write([]string{unixtime, client["client_addr"], matches["transfer_amount"], matches["transfer_magnitude"], matches["duration"], matches["bandwidth"], matches["bandwidth_magnitude"]}); err != nil {
					log.Fatal("Can't write to CSV output for iPerf 2 TCP test.")
				}
				w.Flush()
				if err := w.Error(); err != nil {
					log.Fatalf("Can't write to CSV output for iPerf 2 TCP test: %s", err)
				}
				f.Close()
			}
		}
		if err := scanner.Err(); err != nil {
			// The child process has exited. Let's try to restart it.
			log.Print("iPerf 2 has exited with error")
		}
		srcCmd.Retries += 1
		log.Print("iPerf 2 has exited")
		go handleCommand(srcCmd)
		wg.Done()
	}()
}

func launchServer(thisCmd command) (output, errors io.Reader) {
	log.Println(thisCmd)
	cmd := exec.Command(thisCmd.Cmdline[0], thisCmd.Cmdline[1:]...)
	output, err := cmd.StdoutPipe()
	if err != nil {
		log.Fatal(err)
	}
	errors, err = cmd.StderrPipe()
	if err != nil {
		log.Fatal(err)
	}

	if err := cmd.Start(); err != nil {
		log.Fatal(err)
	}

	go func() {
		wg.Add(1)
		cmd.Wait()
		wg.Done()
	}()
	return output, errors
}

func handleCommand(thisCmd command) {
	wg.Add(1)
	if thisCmd.Retries > 0 {
		time.Sleep(100 * time.Millisecond)
	}

	switch thisCmd.Cmdline[0] {
	case "iperf3":
		output, errors := launchServer(thisCmd)
		jsonHandler(io.MultiReader(output, errors), thisCmd)

	case "iperf":
		// Start multiple servers to handle more than one client at a time
		output, _ := launchServer(thisCmd)
		csvParser(output, thisCmd)

	default:
		// Each handler calls wg.Done() eventually
		wg.Done()
	}
}

func main() {
	exec.Command("killall", "iperf").Run()
	exec.Command("killall", "iperf3").Run()

	for i := len(commands) - 1; i >= 0; i-- {
		handleCommand(command{Cmdline: strings.Split(commands[i], " "), Retries: 0})
	}

	wg.Wait()
}
