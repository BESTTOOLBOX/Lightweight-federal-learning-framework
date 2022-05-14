#!/bin/bash
if screen -ls | grep 'Server' > /dev/null 2>&1; then
     screen -S Server -X quit
fi
echo "Server Closed"
int=0
while(($int<16))
do
    if screen -ls | grep $"Client$int" > /dev/null 2>&1; then
       screen -S Client$int -X quit
    fi
    echo "Client$int Closed"
    let "int++"
done
