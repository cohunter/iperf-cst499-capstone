package main

import (
	"log"
	"io"
	"net/http"
)

func main() {
	dataPostHandler := func(w http.ResponseWriter, req *http.Request) {
		io.WriteString(w, "Thank you, goodbye.\n")
		log.Print(req.FormValue("command"))
		log.Print(req.FormValue("output"))
	}
	
	http.HandleFunc("/ingest", dataPostHandler)
	log.Fatal(http.ListenAndServe(":8080", nil))
}