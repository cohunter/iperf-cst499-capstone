iperf3_udp_defaults_query = """
SELECT
    unix_timestamp,
    json_extract(
        output, '$.start.connected[0].remote_host'
    ) AS server,
    json_extract(output, '$.end.sum.jitter_ms') AS jitter_ms,
    json_extract(output, '$.end.sum.bytes') AS bytes,
    json_extract(output, '$.end.sum.seconds') AS seconds,
    json_extract(
        output, '$.end.sum.lost_packets'
    ) AS lost_packets,
    json_extract(output, '$.end.sum.packets') AS packets
FROM
    client_data
WHERE
    json_valid(output)
    AND json_extract(
        output, '$.start.test_start.protocol'
    ) IS 'UDP'
    AND command NOT LIKE '%-b%'
    AND client_name IS ?
"""

iperf3_udp_3m_query = """
SELECT
    unix_timestamp,
    json_extract(
        output, '$.start.connected[0].remote_host'
    ) AS server,
    json_extract(output, '$.end.sum.jitter_ms') AS jitter_ms,
    json_extract(output, '$.end.sum.bytes') AS bytes,
    json_extract(output, '$.end.sum.seconds') AS seconds,
    json_extract(
        output, '$.end.sum.lost_packets'
    ) AS lost_packets,
    json_extract(output, '$.end.sum.packets') AS packets
FROM
    client_data
WHERE
    json_valid(output)
    AND json_extract(
        output, '$.start.test_start.protocol'
    ) IS 'UDP'
    AND command LIKE '%-b 3m%'
    AND client_name IS ?
"""

iperf3_tcp_query = """
SELECT
    unix_timestamp,
    json_extract(
        output, '$.start.connected[0].remote_host'
    ) AS server,
    json_extract(output, '$.end.sum_received.bytes') AS transfer_amount,
    json_extract(output, '$.end.sum_received.bits_per_second') AS transfer_rate,
    json_extract(output, '$.end.sum_received.seconds') AS seconds
FROM
    client_data
WHERE
    json_valid(output)
    AND json_extract(
        output, '$.start.test_start.protocol'
    ) IS 'TCP'
    AND command NOT LIKE '%p 5008%'
    AND client_name IS ?
"""

multiperf3_tcp_query = """
SELECT
    unix_timestamp,
    json_extract(
        output, '$.start.connected[0].remote_host'
    ) AS server,
    json_extract(output, '$.end.sum_received.bytes') AS transfer_amount,
    json_extract(output, '$.end.sum_received.bits_per_second') AS transfer_rate,
    json_extract(output, '$.end.sum_received.seconds') AS seconds
FROM
    client_data
WHERE
    json_valid(output)
    AND json_extract(
        output, '$.start.test_start.protocol'
    ) IS 'TCP'
    AND command LIKE '%p 5008%'
    AND client_name IS ?
"""

# iperf 2 UDP (defaults)
iperf2_udp_defaults_query = """
SELECT
    unix_timestamp,
    extract_csv(1,1, output) AS server,
    extract_csv(1,9, output) AS jitter_ms,
    extract_csv(1,7, output) AS bytes,
    extract_csv(0,6, output) AS duration,
    extract_csv(1,10, output) AS lost_packets,
    extract_csv(1,11, output) AS packets
FROM
    client_data
WHERE
    command LIKE '%iperf %'
    AND command LIKE '%-u%'
    AND command NOT LIKE '%-b%'
    AND client_name IS ?
"""

# iperf 2 UDP (3mbit)
iperf2_udp_3m_query = """
SELECT
    unix_timestamp,
    extract_csv(1,1, output) AS server,
    extract_csv(1,9, output) AS jitter_ms,
    extract_csv(1,7, output) AS bytes,
    extract_csv(0,6, output) AS duration,
    extract_csv(1,10, output) AS lost_packets,
    extract_csv(1,11, output) AS packets
FROM
    client_data
WHERE
    command LIKE '%iperf %'
    AND command LIKE '%-u%'
    AND command LIKE '%-b 3m%'
    AND client_name IS ?
"""

# iperf 2 TCP
iperf2_tcp = """
SELECT
    unix_timestamp,
    extract_csv(0,1, output) AS local_addr,
    extract_csv(0,2, output) AS local_port,
    extract_csv(0,3, output) AS remote_addr,
    extract_csv(0,4, output) AS remote_port,
    extract_csv(0,6, output) AS duration,
    extract_csv(0,7, output) AS transfer_amount,
    extract_csv(0,8, output) AS transfer_rate
FROM
    client_data
WHERE
    command LIKE '%iperf %'
    AND command NOT LIKE '%-u%'
    AND client_name IS ?
"""
