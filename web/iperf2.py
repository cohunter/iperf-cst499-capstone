import sqlite3
import pandas as pd
import local_utils
import csv
from io import StringIO
import sys
import queries
# We use the database as read-only
conn = sqlite3.connect('file:/home/user/client-data.sqlite3?mode=ro', check_same_thread=False, uri=True)

db = conn.cursor()

# SQLite has built-in JSON functions, but not equivalents for CSV.
# So we define our own function to extract data from the CSV fields.
def sqlite3_extract_csv(row, column, csv_data):
    try:
        buff = StringIO(csv_data)
        reader = csv.reader(buff)
        lines = [line for line in reader]
        #print(lines)
        return lines[row][column]
    except Exception as e:
        print('except', e)
        if sys.stdout.isatty():
            print(repr(lines))
    return False

conn.create_function("extract_csv", 3, sqlite3_extract_csv)


def get_results_count():
    db.execute('SELECT COUNT(1) AS count from client_data')
    row = db.fetchone()
    return row[0]

def get_client_names():
    db.execute('SELECT client_name, COUNT(1) AS c FROM client_data GROUP BY client_name HAVING c > 72')
    clients = db.fetchall()
    return clients

def get_client_data():
    #results = db.execute("SELECT unix_timestamp, json_extract(output, '$.start.connected[0].remote_host') AS server, json_extract(output, '$.end.sum.jitter_ms')  AS jitter_ms, json_extract(output, '$.end.sum.bytes') AS bytes, json_extract(output, '$.end.sum.seconds') AS seconds, json_extract(output, '$.end.sum.lost_packets') AS lost_packets, json_extract(output, '$.end.sum.packets') AS packets FROM client_data WHERE json_valid(output) AND json_extract(output, '$.start.test_start.protocol') is 'UDP' AND client_name is 'Alex';")
    #cols = [column[0] for column in results.description]
    #df = pd.DataFrame.from_records(data=results.fetchall(), columns=cols)

    df = pd.read_sql_query(queries.iperf3_udp_defaults_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=['mac-corey'])
    print(df)
    df = pd.read_sql_query(queries.iperf3_udp_3m_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=['mac-corey'])
    print(df)
    df = pd.read_sql_query(queries.iperf3_tcp_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=['mac-corey'])
    print(df)
    df = pd.read_sql_query(queries.multiperf3_tcp_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=['mac-corey'])
    print(df)
    df = pd.read_sql_query(queries.iperf2_udp_defaults_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=['mac-corey'])
    print(df)
    df = pd.read_sql_query(queries.iperf2_udp_3m_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=['mac-corey'])
    print(df)
    df = pd.read_sql_query(queries.iperf2_tcp, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=['mac-corey'])
    print(df)

get_client_data()