#!/usr/bin/env python

import json
import argparse
import hashlib
import pyshark
from os import path
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sender')
    parser.add_argument('--receiver')
    parser.add_argument('--scheme', help='scheme to test')
    parser.add_argument('--data-dir', help='data dir')
    args = parser.parse_args()

    data = {}
    data[args.scheme] = {}

    data[args.scheme]['mean'] = {}
    data[args.scheme]['mean']['all'] = {}
    data[args.scheme]['mean']['all']['tput'] = []
    data[args.scheme]['mean']['all']['delay'] = []

    for run_id in range(1, 11):
        send_pkts = {}
        send_pcap_name = '{scheme}-send-{run_id}.pcap'.format(
                scheme=args.scheme, run_id=run_id)
        send_pcap = pyshark.FileCapture(path.join(args.data_dir, send_pcap_name))
        for pkt in send_pcap:
            if pkt.ip.dst != args.receiver:
                continue

            # uid = hashlib.sha256(str(pkt.tcp) + str(pkt.ip)).hexdigest()
            uid = pkt.tcp.seq
            ts = float(pkt.sniff_timestamp)
            size = int(pkt.ip.len)
            send_pkts[uid] = (ts, size)

        # calculate avg. tput
        first_ts = None
        last_ts = None
        total_size = 0

        # calculate 95th delay
        delays = []

        recv_pcap_name = '{scheme}-recv-{run_id}.pcap'.format(
                scheme=args.scheme, run_id=run_id)
        recv_pcap = pyshark.FileCapture(path.join(args.data_dir, recv_pcap_name))
        for pkt in recv_pcap:
            if pkt.ip.src != args.sender:
                continue

            #uid = hashlib.sha256(str(pkt.tcp) + str(pkt.ip)).hexdigest()
            uid = pkt.tcp.seq
            ts = float(pkt.sniff_timestamp)

            if first_ts is None or ts < first_ts:
                first_ts = ts

            if last_ts is None or ts > last_ts:
                last_ts = ts

            size = int(pkt.ip.len)
            total_size += size

            if uid in send_pkts:
                delays.append(ts - send_pkts[uid][0])

        tput = total_size / (1024 * 1024 * (last_ts - first_ts))
        delay = 1000 * np.percentile(delays, 95, interpolation='nearest')

        data[args.scheme][run_id] = {}
        data[args.scheme][run_id]['all'] = {}
        data[args.scheme][run_id]['all']['tput'] = tput
        data[args.scheme][run_id]['all']['delay'] = delay

        data[args.scheme]['mean']['all']['tput'].append(tput)
        data[args.scheme]['mean']['all']['delay'].append(delay)

    data[args.scheme]['mean']['all']['tput'] = np.mean(data[args.scheme]['mean']['all']['tput'])
    data[args.scheme]['mean']['all']['delay'] = np.mean(data[args.scheme]['mean']['all']['delay'])

    perf_data_path = path.join(args.data_dir, 'pcap_data.json')
    with open(perf_data_path, 'w') as fh:
        json.dump(data, fh)


if __name__ == '__main__':
    main()
