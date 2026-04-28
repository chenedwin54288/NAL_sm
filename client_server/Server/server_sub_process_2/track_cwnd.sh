#!/bin/bash

CLIENT_IP="$1"

if [ -z "$CLIENT_IP" ]; then
    echo "Usage: $0 <client-ip>"
    exit 1
fi

while true; do
    # Get the timestamp
    TS=$(date +"%H:%M:%S.%N")
    
    # Extract the cwnd value for the specific connection
    # 'ss -it' gets internal TCP information
    CWND=$(ss -it dst $CLIENT_IP | grep -oP 'cwnd:\K\d+')
    
    # If a connection exists, log it
    if [ ! -z "$CWND" ]; then
        echo "$TS cwnd:$CWND" >> cwnd_log.txt
    fi
    
    sleep 0.01
done