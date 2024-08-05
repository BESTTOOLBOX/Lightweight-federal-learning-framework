#!/bin/bash
client_udp_port_start=50001
client_tcp_port_start=50002
server_udp_port=49998
server_tcp_port=49999
client_ip=("127.0.0.1")
server_ip=("127.0.0.1")
client_num=16
clientnum_eachepoch=5 #K
client_local_epoch=10 #M
total_epoch=150 #R
 

client_udp_port=$client_udp_port_start
client_tcp_port=$client_tcp_port_start
int=0
while(( $int<$client_num ))
do
    echo "constructing client $int "
    screen -dmS $"Client$int"
    screen -S $"Client$int" -p bash -X stuff $"cd /root/workspace/FL/Client\n"
    screen -S $"Client$int" -p bash -X stuff $"cp /root/workspace/FL/code/Client.py /root/workspace/FL/Client/Client$int.py\n"
    screen -S $"Client$int" -p bash -X stuff $"conda activate FL\n"
    screen -S $"Client$int" -p bash -X stuff $"python Client$int.py ${client_ip[0]} $client_udp_port $client_tcp_port ${server_ip[0]} $server_udp_port $server_tcp_port\n"
    echo "UDP_PORT=$client_udp_port TCP_PORT=$client_tcp_port"
    let "int++"
    let "client_udp_port=client_udp_port+2"
    let "client_tcp_port=client_tcp_port+2"
done

echo "constructing Server"
screen -dmS Server
screen -S Server -p bash -X stuff $"cd /root/workspace/FL/Server\n"
screen -S Server -p bash -X stuff $"conda activate FL\n"
screen -S Server -p bash -X stuff $"cp /root/workspace/FL/code/Server.py /root/workspace/FL/Server/Server.py\n"
screen -S Server -p bash -X stuff $"cp /root/workspace/FL/code/Model.py /root/workspace/FL/Client/Model.py\n"
screen -S Server -p bash -X stuff $"python Server.py ${server_ip[0]} $server_udp_port $server_tcp_port $client_num $client_udp_port_start ${client_ip[0]} $clientnum_eachepoch $client_local_epoch $total_epoch\n"
