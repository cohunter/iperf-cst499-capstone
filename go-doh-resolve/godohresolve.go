package godohresolve

import (
	"net"
	"net/url"
	"net/http"
	"time"
	"strings"
	"context"
	"encoding/json"
)

// https://developers.cloudflare.com/1.1.1.1/dns-over-https/json-format/
type DoHResponse struct {
	Status int
	TC bool
	RD bool
	RA bool
	AD bool
	CD bool
	Question []struct {
		Name string
		Type int
	}
	Answer []struct {
		Name string
		Type int
		Ttl int
		Data string
	}
}

// Replaces the default http transport with one that queries Cloudflare's DoH
// Assumes no use of internal (non-public) DNS names
// Why is this useful?
// When cross-compiling for Android as generic Linux, golang tries to read /etc/resolv.conf
// This file doesn't typically exist on Android, and can't be created without root.
// Here we use DoH queries instead of the builtin resolver.
func init() {
	http.DefaultTransport.(*http.Transport).DialContext = DoHQueryTransport
}

func DoHQueryTransport(ctx context.Context, network, addr string) (net.Conn, error) {
	dialer := &net.Dialer {
		Timeout: 30*time.Second,
		KeepAlive: 30*time.Second,
		DualStack: false,
	}
	// Assume format of addr is host:port
	hostport := strings.SplitN(addr, ":", 2)
	
	host := hostport[0]
	port := hostport[1]
	
	switch net.ParseIP(host) {
		case nil:
			break
		case Equal()
	}
	if host == "1.1.1.1" {
		return dialer.DialContext(ctx, network, addr)
	}
	
	// No need to query DNS when connecting to an IP address
	if net.ParseIP(host) != nil {
		return dialer.DialContext(ctx, network, addr)
	}
	
	var DoHQueryResult DoHResponse
	resolver, err := url.Parse("https://1.1.1.1/dns-query?name&type")
	params := resolver.Query()
	params.Set("name", host)
	params.Set("type", "A")
	
	req, err := http.NewRequest("GET", resolver.String(), nil)
	if err != nil {
		panic(err)
	}
	req.Header.Set("accept", "application/dns-json")
	req.URL.RawQuery = params.Encode()
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode == http.StatusOK {
		err := json.NewDecoder(resp.Body).Decode(&DoHQueryResult)
		if err != nil {
			panic(err)
		}
		switch len(DoHQueryResult.Answer) {
			case 0:
				panic("No Results")
			case 1:
				return dialer.DialContext(ctx, network, DoHQueryResult.Answer[0].Data + ":" + port)
			default:
				return dialer.DialContext(ctx, network, DoHQueryResult.Answer[0].Data + ":" + port)
		}
	}
	
	panic("DoH lookup failed")
}