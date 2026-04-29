# Reset TBF parameters to new ones
# rate ? 
# burst ? 
# limit ?
sudo tc qdisc del dev eno1 root 2>/dev/null


# Calculate the optimal CWND size
# current rtt 
# optimal CWND = rtt*rate + limit - MSS


# 1> select the cca that we want to use
# -> pass to init_cca.sh
# -> pass to the server.py
# 2> select the dataSieze we want the serve to send (1GB, 2GB, 3GB....)


# if the cca == "my_cca"
#    => run init_cca.sh with (optimal CWND)
# else:
#    => do nothing

# start the server.py with log_extractor turned ON
# and with parameters (dataSize, selected cca)
# FIXME: the server should output the client port number after the connection ends (write to a log file)



# create a dir in DB with "{dataSize}/{dataSize}_{port}_{cwnd}"

# Run filter_ip.py
# Run extract_ip_info.py 
# Run filter_ip.py


# NOTE: this final step cpuld be further optimized
# if completion time < prev completion time
#   current rtt += 1
#   start from line 13
# else:
#   STOP 



