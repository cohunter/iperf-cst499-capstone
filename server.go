package main

import (
	"log"
	"io"
	"net/http"
	"database/sql"
	_ "github.com/mattn/go-sqlite3" // go get github.com/mattn/go-sqlite3
)

func main() {
	db, err := sql.Open("sqlite3", "./client-data.sqlite3")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	_, err = db.Exec(`CREATE TABLE IF NOT EXISTS client_data (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, unix_timestamp INTEGER, command TEXT, output TEXT)`)
	if err != nil {
		log.Fatal(err)
	}
	dataPostHandler := func(w http.ResponseWriter, req *http.Request) {
		command	:= req.FormValue("command")
		output	:= req.FormValue("output")
		if len(output) == 0 || len(command) == 0 {
			http.NotFound(w, req)
			return
		}

		tx, err := db.Begin()
		if err != nil {
			log.Fatal(err)
		}
		stmt, err := tx.Prepare("INSERT INTO client_data (unix_timestamp, command, output) VALUES (strftime('%s','now'), ?, ?)")
		if err != nil {
			log.Fatal(err)
		}
		defer stmt.Close()
		_, err = stmt.Exec(command, output)
		if err != nil {
			log.Fatal(err)
		}
		tx.Commit()
		log.Println("Successfully stored client data to database")
		io.WriteString(w, "Thank you, goodbye.\n")
	}
	
	http.HandleFunc("/ingest", dataPostHandler)
	log.Fatal(http.ListenAndServe("[::1]:8080", nil))
}
