package main

import (
	"io"
	"os"
	"fmt"
	"log"
	"math"
	"strings"
	"database/sql"
	_ "github.com/mattn/go-sqlite3"
	"strconv"
	"encoding/csv"
	"encoding/json"
)

// Appends to files; ensure they are empty before running.
// rm iperf3-*.csv
func jsonHandler(jsonStr string, timestamp int64, command string) {
	if ( true ) {
		return
	}
	var m map[string]interface{}
	if err := json.Unmarshal([]byte(jsonStr), &m); err != nil {
		log.Println("JSON decoding error")
		log.Fatal(err)
	}
	protocol := m["start"].(map[string]interface{})["test_start"].(map[string]interface{})["protocol"].(string)
	// This is iPerf 3 client results; we use start.connected[0].remote_host
	// on the server, we would use start.accepted_connection.host to get the client IP
	// since we only used one type of client per server this round, we select server IP
	remote_host := m["start"].(map[string]interface{})["connected"].([]interface{})[0].(map[string]interface{})["remote_host"].(string)
	reverse := (math.Round(m["start"].(map[string]interface{})["test_start"].(map[string]interface{})["reverse"].(float64)) == 1)
	
	// remote_host: 54.212.26.193			:: Android -> Oregon
	// remote_host: 2001:bc8:47a8:43b::1	:: AMS -> PAR [IPv6]
	// remote_host: 2001:bc8:1824:1148::1	:: PAR -> AMS [IPv6]
	// go run db-to-csv.go  | egrep "^remote_host:" | sort | uniq -c
	// 1074 remote_host: 2001:bc8:1824:1148::1
    // 1074 remote_host: 2001:bc8:47a8:43b::1
    // 1009 remote_host: 54.212.26.193
    
    var fn string
    switch remote_host {
    	case "54.212.26.193":
    		fn = "oregon-client.csv"
    	case "2001:bc8:47a8:43b::1":
    		fn = "ams-client.csv"
    	case "2001:bc8:1824:1148::1":
    		fn = "par-client.csv"
    	default:
    		log.Fatal("Unhandled remote_host for iPerf 3")
    }
    
	switch protocol {
		case "UDP":
			fn = fmt.Sprintf("udp-%s", fn)
		case "TCP":
			fn = fmt.Sprintf("tcp-%s", fn)
		default:
			log.Fatalf("Unhandled protocol for iPerf 3: %q", protocol) // %q for untrusted input
	}
	
	if ( strings.Contains(command, "-b 10m") ) {
    	fn = fmt.Sprintf("10m-%s", fn)
    }
	
	if ( reverse ) {
		fn = fmt.Sprintf("reverse-%s", fn)
	}
	
	fn = fmt.Sprintf("iperf3-%s", fn)
	
	switch protocol {
		case "TCP":
			f, err := os.OpenFile(fn, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
			defer f.Close()
			if err != nil {
				log.Fatalf("Can't open CSV output file %q for iPerf 3 TCP result: %q", fn, err)
			}
			w := csv.NewWriter(f)
			
			sr := m["end"].(map[string]interface{})["sum_received"].(map[string]interface{})
			
			unixtime := strconv.FormatInt(timestamp, 10)
			bytes := strconv.FormatFloat(sr["bytes"].(float64), 'f', -1, 64)
			bits_per_second := strconv.FormatFloat(sr["bits_per_second"].(float64), 'f', -1, 64)
			seconds := strconv.FormatFloat(sr["seconds"].(float64), 'f', -1, 64)
			
			if err := w.Write([]string{unixtime, remote_host, bytes, bits_per_second, seconds}); err != nil {
				log.Fatal(err)
			}
			
			w.Flush()
			if err := w.Error(); err != nil {
				log.Fatalf("Can't write to CSV output file %q for iPerf 3 TCP result: %q", fn, err)
			}
		case "UDP":
			f, err := os.OpenFile(fn, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
			defer f.Close()
			if err != nil {
				log.Fatalf("Can't open CSV output file %q for iPerf 3 UDP result: %q", fn, err)
			}
			w := csv.NewWriter(f)
			
			sr := m["end"].(map[string]interface{})["sum"].(map[string]interface{})
			
			unixtime := strconv.FormatInt(timestamp, 10)
			jitter_ms := strconv.FormatFloat(sr["jitter_ms"].(float64), 'f', -1, 64)
			bytes := strconv.FormatFloat(sr["bytes"].(float64), 'f', -1, 64)
			seconds := strconv.FormatFloat(sr["seconds"].(float64), 'f', -1, 64)
			// These are integers (0 decimal places)
			lost_packets := strconv.FormatFloat(sr["lost_packets"].(float64), 'f', 0, 64)
			packets := strconv.FormatFloat(sr["packets"].(float64), 'f', 0, 64)
			
			if err := w.Write([]string{unixtime, remote_host, jitter_ms, bytes, seconds, lost_packets, packets}); err != nil {
				log.Fatal(err)
			}
			
			w.Flush()
			if err := w.Error(); err != nil {
				log.Fatalf("Can't write to CSV output file %q for iPerf 3 UDP result: %q", fn, err)
			}
	}
	
	//fmt.Printf("fn: %s\n", fn)
	//fmt.Printf("proto: %+v\n", protocol)
	//fmt.Printf("remote_host: %+v\n", remote_host) 
	//fmt.Printf("%+v", m)
}

func csvHandler(csvStr string, timestamp int64, command string) {
	scanner := csv.NewReader(strings.NewReader(csvStr))
	scanner.FieldsPerRecord = -1
	for {
		record, err := scanner.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatal(err)
		}
		
		if len(record) == 1 {
			log.Printf("iPerf 2 error record: %+v", record)
			return
		}
		
		var fn string
		
		unixtime := strconv.FormatInt(timestamp, 10)
		
		var server_idx int
		server_report := false
		// Assume if port is 500x, this address is the server IP
		if ( strings.HasPrefix(record[2], "500") ) {
			server_idx = 1
			server_report = true
		} else if ( strings.HasPrefix(record[4], "500") ) {
			server_idx = 3
		} else {
			log.Fatal("Unhandled address/port combination: %+v", record)
		}
		
		switch record[server_idx] {
			case "54.212.26.193":
	    		fn = "oregon-client.csv"
	    	case "2001:bc8:47a8:43b::1":
	    		fn = "ams-client.csv"
	    	case "2001:bc8:1824:1148::1":
	    		fn = "par-client.csv"
	    	default:
	    		log.Fatal("Unhandled remote_host for iPerf 2")
		}
		
		if ( server_report ) {
			fn = fmt.Sprintf("server_report-%s", fn)
		}
		
		if ( strings.Contains(command, "-u") ) {
			fn = fmt.Sprintf("udp-%s", fn)
		} else {
			fn = fmt.Sprintf("tcp-%s", fn)
		}
		
		if ( strings.Contains(command, "-b 10m") ) {
	    	fn = fmt.Sprintf("10m-%s", fn)
	    }
	    
	    fn = fmt.Sprintf("iperf2-%s", fn)
	    
	    f, err := os.OpenFile(fn, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
	    defer f.Close()
	    if err != nil {
	    	log.Fatal(err)
	    }
	    w := csv.NewWriter(f)
	    
		switch len(record) {
			case 9:
				// [Datetime, local_addr, local_port, remote_addr, remote_port, transfer_id, start_time-end_time (%.1f), transferred, transfer_rate]
				if err := w.Write([]string{unixtime, record[1], record[2], record[3], record[4], record[6], record[7], record[8]}); err != nil {
					log.Fatalf("Can't write to CSV output file %q for iPerf 2 TCP test: %q", fn, err)
				}
				w.Flush()
				if err := w.Error(); err != nil {
					log.Fatalf("Can't flush CSV output file %q for iPerf 2 TCP test: %q", fn, err)
				}
			case 14:
				// [Datetime, local_addr, local_port, remote_addr, remote_port, transfer_id, start_time-end_time (%.1f), transferred, transfer_rate, jitter_ms, lost_packets, total_packets, lost_pct, is_reversed]
				// [20200323234234 54.212.26.193 5002 192.168.0.140 46492 3 0.0-9.9 1311240 1057408 2.713 0 892 0.000 0]
				if err := w.Write([]string{unixtime, record[1], record[2], record[3], record[4], record[6], record[7], record[8], record[9], record[10], record[11]}); err != nil {
					log.Fatalf("Can't write to CSV output file %q for iPerf 2 UDP test: %q", fn, err)
				}
				w.Flush()
				if err := w.Error(); err != nil {
					log.Fatalf("Can't flush CSV output file %q for iPerf 2 UDP test: %q", fn, err)
				}
		}
	}
}

func main() {
	db, err := sql.Open("sqlite3", "./client-data.sqlite3")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	
	rows, err := db.Query("SELECT unix_timestamp, command, output FROM client_data")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()
	
	for rows.Next() {
		var timestamp int64
		var command string
		var output string
		err = rows.Scan(&timestamp, &command, &output)
		if err != nil {
			log.Fatal(err)
		}
		if ( strings.HasPrefix(command, "iperf3") ) {
			//fmt.Println("iperf3 result")
			jsonHandler(output, timestamp, command)
		} else if ( strings.HasPrefix(command, "iperf ") ){
			//fmt.Println("iperf2 result")
			csvHandler(output, timestamp, command)
		} else {
			log.Fatal("unknown command")
		}
		//fmt.Printf("%d %s %s\n", timestamp, command, output)
	}
	err = rows.Err()
	if err != nil {
		log.Fatal(err)
	}
}