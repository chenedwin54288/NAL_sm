#!/bin/bash

while true; do 
    echo -n "$(date +"%H:%M:%S.%N") " >> backlog.txt
    tc -s qdisc show dev eno1 | grep "backlog" >> backlog.txt
    sleep 0.1
done