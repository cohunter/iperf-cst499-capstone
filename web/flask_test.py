from flask import Flask, render_template, request, Response
import sqlite3

# used for UDF
import csv
from io import StringIO
from sys import stdout

# used for graphing
from io import BytesIO
import pandas as pd
import local_utils
import queries

# dependencies:
# pip3 install flask pandas matplotlib

app = Flask(__name__)

# SQLite has built-in JSON functions, but not equivalents for CSV.
# So we define our own function to extract data from the CSV fields.
def sqlite3_extract_csv(row, column, csv_data):
    try:
        buff = StringIO(csv_data)
        reader = csv.reader(buff)
        lines = [line for line in reader]
        #print(lines)
        value = lines[row][column]
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    except Exception as e:
        print('except', e)
        if stdout.isatty():
            print(repr(lines))
    return False

# We use the database as read-only
def get_database_connection(use_csv=False):
    conn = sqlite3.connect('/home/user/client-data.sqlite3', check_same_thread=False)
    
    if use_csv:
        conn.create_function("extract_csv", 3, sqlite3_extract_csv)

    return conn

def get_results_count(db):
    db.execute('SELECT COUNT(1) AS count from client_data')
    row = db.fetchone()
    return row[0]

def get_client_names(db):
    db.execute('SELECT client_name, COUNT(1) AS c FROM client_data GROUP BY client_name HAVING c > 72')
    clients = db.fetchall()
    return clients

def get_client_data(client_name):
    iperf3_udp_defaults = pd.read_sql_query(queries.iperf3_udp_defaults_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    
    iperf3_udp_3m = pd.read_sql_query(queries.iperf3_udp_3m_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    
    iperf3_tcp = pd.read_sql_query(queries.iperf3_tcp_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    
    multiperf3_tcp = pd.read_sql_query(queries.multiperf3_tcp_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    
    iperf2_udp_defaults = pd.read_sql_query(queries.iperf2_udp_defaults_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    
    iperf2_udp_3m = pd.read_sql_query(queries.iperf2_udp_3m_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    
    iperf2_tcp = pd.read_sql_query(queries.iperf2_tcp, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    
    udp_defaults = local_utils.merge(iperf3_udp_defaults, iperf2_udp_defaults)
    print(iperf2_udp_defaults.info())
    #local_utils.scatter_by_date(udp_defaults, col='jitter_ms')
    local_utils.scatter_by_date(iperf3_udp_defaults, iperf2_udp_defaults, col='jitter_ms')

def load_dataset_for_client(dataset, client_name, conn=get_database_connection(use_csv=True)):
    if dataset == 'tcp':
        iperf3 = pd.read_sql_query(queries.iperf3_tcp_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
        iperf2 = pd.read_sql_query(queries.iperf2_tcp, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    elif dataset == 'udp':
        iperf3 = pd.read_sql_query(queries.iperf3_udp_defaults_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
        iperf2 = pd.read_sql_query(queries.iperf2_udp_defaults_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    elif dataset == 'udp3m':
        iperf3 = pd.read_sql_query(queries.iperf3_udp_3m_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
        iperf2 = pd.read_sql_query(queries.iperf2_udp_3m_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
    elif dataset == 'multiperf3':
        multiperf = pd.read_sql_query(queries.multiperf3_tcp_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
        iperf3 = pd.read_sql_query(queries.iperf3_tcp_query, conn, index_col='unix_timestamp', parse_dates='unix_timestamp', params=[client_name])
        return (iperf3, multiperf)
    else:
        return 'Error: invalid dataset'
    return (iperf2, iperf3)
app.url_map.strict_slashes = False

@app.route("/")
@app.route("/client")
@app.route("/client/")
@app.route("/client/<client_name>")
def go(client_name=None):
    conn = get_database_connection()
    db = conn.cursor()

    clients = get_client_names(db)
    if client_name is None:
        client_name = clients[0][0]
    print(client_name)
    #get_client_data(client_name)
    return render_template('index.html', result_count=get_results_count(db), clients=clients, selected_client=client_name)

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
@app.route("/client/<client_name>/scatter.png")
def scatter_png(client_name=None):
    if client_name is None:
        return 'Error'
    dataset = request.args.get('dataset', default='udp')
    fig = local_utils.scatter_by_date(*load_dataset_for_client(dataset, client_name), col='jitter_ms', dotscale=2)
    fig.tight_layout()
    image = BytesIO()
    FigureCanvas(fig).print_png(image, metadata={'Author': 'Corey Hunter'})
    return Response(image.getvalue(), mimetype='image/png')

@app.route("/client/<client_name>/rate.png")
def rate_png(client_name=None):
    if client_name is None:
        return 'Error'
    dataset = request.args.get('dataset', default='tcp')
    print(dataset, 'dataset')
    fig = local_utils.ratebydate(*load_dataset_for_client(dataset, client_name), 'TCP Throughput', is_multiperf=(dataset == 'multiperf3'))
    fig.tight_layout()
    image = BytesIO()
    FigureCanvas(fig).print_png(image)
    return Response(image.getvalue(), mimetype='image/png')

@app.route("/client/<client_name>/<dataset>.csv")
def tcp_data(client_name=None, dataset=None):
    if client_name is None or dataset is None:
        return 'Error'
    merged = local_utils.merge(*load_dataset_for_client(dataset, client_name))
    return Response(merged.to_csv(compression='gzip'), mimetype='application/x-gzip')

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=False, debug=True)
