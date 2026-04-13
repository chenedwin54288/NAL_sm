#!/bin/bash

CLIENT_IP="128.178.122.39"

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