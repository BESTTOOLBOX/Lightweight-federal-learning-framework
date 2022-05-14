import warnings
warnings.filterwarnings("ignore")
import tensorflow as tf
from tqdm import tqdm
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import time
import socket
import threading
import json
import numpy as np
from collections import namedtuple
import math
import dill
import pickle
import os
import csv
import sys
import random
from tensorflow.python.keras import backend as K
import math



epoch = int(sys.argv[9])       #最多大循环次数
LEARNING_RATE_START=0.0002
LEARNING_RATE=LEARNING_RATE_START
M=1.5
V=1.3
NUM_INPUT_X=32
NUM_INPUT_Y=32
NUM_INPUT_CHANNEL=3
NUM_CLASSES=10
client_epoch =int(sys.argv[8])   #小循环
batchsize=600
test_batchsize=-1
drop_rate=0.5

client_vars_sum = None
global_vars = None
total_data_size= None
detect_client_cnt= 0
detect_client_recv_bool = False
now_epoch= None


##########网络部署###########
Client_nums =int(sys.argv[4])
chosen_client_nums = int(sys.argv[7])
Server_HOST=sys.argv[1]
Server_PORT=int(sys.argv[2])
Server_PORT_TCP = int(sys.argv[3])
Target_HOST=[sys.argv[6] for i in range(Client_nums)]
Target_PORT=[int(sys.argv[5])+i*2 for i in range(Client_nums)]
Target_ID=[i for i in range(1,Client_nums+1)]
Target=[i for i in zip(Target_HOST,Target_PORT)]
global_loss=0
state_of_client={}
for i in range(1,Client_nums+1):
    state_of_client[str(i)]=0
state_of_client_train={}
for i in range(1,Client_nums+1):
    state_of_client_train[str(i)]=0
state_of_client_test={}
for i in range(1,Client_nums+1):
    state_of_client_test[str(i)]=0
chosen_client={}
for i in range(1,Client_nums+1):
    chosen_client[str(i)]=0


s= socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind((Server_HOST,Server_PORT))
tcp_tunnel_s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
tcp_tunnel_s.bind((Server_HOST, Server_PORT_TCP))
tcp_tunnel_s.listen(5)

symbol=str(time.time())+"record_epoch="+str(epoch)+"_clientepoch="+str(client_epoch)+"_batchsize="+str(batchsize)+"_testbatchsize="+str(test_batchsize)+"_Clientnums="+str(Client_nums)+".csv"

f = open(symbol,"w",encoding="UTF-8",newline="")
csvwriter = csv.writer(f)
csvwriter.writerow(["client_id", "client_epoch", "server_epoch", "acc", "loss", "local_time", "time_slot", "operation"])
f.close()

lr_f=open("lr.csv","w",encoding="UTF-8",newline="")
lr_csvwriter = csv.writer(lr_f)
lr_csvwriter.writerow(["epoch","lr"])
lr_f.close()

mytxt=open(str(time.time())+"args.txt", "w", encoding="UTF-8")
mytxt.write("chosen_client_nums ="+str(chosen_client_nums )+"\n")
mytxt.write("epoch ="+str(epoch )+"\n")
mytxt.write("LEARNING_RATE="+str(LEARNING_RATE)+"\n")
mytxt.write("NUM_INPUT_X="+str(NUM_INPUT_X)+"\n")
mytxt.write("NUM_INPUT_Y="+str(NUM_INPUT_Y)+"\n")
mytxt.write("NUM_INPUT_CHANNEL="+str(NUM_INPUT_CHANNEL)+"\n")
mytxt.write("NUM_CLASSES="+str(NUM_CLASSES)+"\n")
mytxt.write("client_epoch ="+str(client_epoch )+"\n")
mytxt.write("batchsize="+str(batchsize)+"\n")
mytxt.write("test_batchsize="+str(test_batchsize)+"\n")
mytxt.write("drop_rate="+str(drop_rate)+"\n")
mytxt.write("Server_HOST="+str(Server_HOST)+"\n")
mytxt.write("Server_PORT="+str(Server_PORT)+"\n")
mytxt.write("Target_HOST="+str(Target_HOST)+"\n")
mytxt.write("Target_PORT="+str(Target_PORT)+"\n")
mytxt.write("Target_ID="+str(Target_ID)+"\n")
mytxt.write("Client_nums="+str(Client_nums)+"\n")
mytxt.close()




def sendmsg(mysocket,serverdata,HOST,PORT):
    serverdata = dill.dumps(serverdata)
    for each_target_HOST, each_target_PORT in zip(HOST,PORT):
        mysocket.sendto(serverdata,(each_target_HOST,each_target_PORT))
        print(each_target_HOST, each_target_PORT)
    return 0


def recvmsg(mysocket):
    while 1:
        try:
            clientdata,addr = mysocket.recvfrom(4096)
            clientdata=dill.loads(clientdata)
            print("get:",clientdata,"from:",addr)
            deal_recv(clientdata, addr)
        except:
            pass
    return 0


def tcp_tunnel_send(data,HOST,PORT):
    global now_epoch, symbol
    while 1:
        try:
            tcp_start_time=time.time()
            senddata = dill.dumps(data)
            print(sys.getsizeof(senddata))
            tcp_tunnel_ss=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_tunnel_ss.connect((HOST, PORT))
            tcp_tunnel_ss.sendall(senddata)
            print("TCP 传输完成")
            tcp_tunnel_ss.close()
            tcp_end_time=time.time()
            f = open(symbol, "a", encoding="UTF-8", newline="")
            csvwriter = csv.writer(f)
            csvwriter.writerow([str(HOST)+'_'+str(PORT), "",now_epoch, "", "", time.time(), tcp_end_time-tcp_start_time, "tcp_send"])
            f.close()
            return 0
        except:
            print("TCP传输失败，等待5s后重新尝试传输"+str(HOST)+"//"+str(PORT))
            time.sleep(5)
    return 0


def tcp_tunnel_recv(tcp_tunnel_s):
    global now_epoch, Target_PORT, Target_HOST, symbol
    while 1:
        try:
            tcp_start_time_recv=time.time()
            sock, addr = tcp_tunnel_s.accept()
            print("获取TCP传输，来自" + str(addr))
            total_data = b''
            data = sock.recv(1024)
            total_data += data
            num = len(data)
            # 如果没有数据了，读出来的data长度为0，len(data)==0
            with tqdm(total=np.ceil(18500)) as bar:
                while len(data) > 0:
                    data = sock.recv(1024)
                    num += len(data)
                    total_data += data
                    bar.update(1)
            clientdata=total_data
            clientdata=dill.loads(clientdata)
            print(clientdata["msg"])
            tcp_end_time_recv=time.time()
            client_id = clientdata["ID"]
            f = open(symbol, "a", encoding="UTF-8", newline="")
            csvwriter = csv.writer(f)
            csvwriter.writerow([str(Target_HOST[int(client_id) - 1]) + '_' + str(Target_PORT[int(client_id) - 1]), clientdata["epoch"] ,now_epoch, "", "", time.time(), tcp_end_time_recv-tcp_start_time_recv, "tcp_recv"])
            f.close()
            deal_recv(clientdata, addr)
        except:
            pass
    return 0


thread_recvmsg=threading.Thread(target=recvmsg, args=(s,))
thread_recvmsg.start()
thread_recvmsg_tcp=threading.Thread(target=tcp_tunnel_recv, args=(tcp_tunnel_s,))
thread_recvmsg_tcp.start()

def deal_recv(clientdata, addr):
    if clientdata["msg"]=="get_client_vars":
        get_client_vars(clientdata)
    if clientdata["msg"]=="test_client":
        test_client(clientdata)
    if clientdata["msg"]=="detect_client_recv":
        detect_client_recv(clientdata)
    return 0
################网络部署########################


def build_clients(HOST, PORT):
    global NUM_INPUT_X, NUM_INPUT_Y, NUM_INPUT_CHANNEL, NUM_CLASSES, LEARNING_RATE, s
    client_init_data={"msg": "client_init_data",
                      "input_shape": [None, NUM_INPUT_X, NUM_INPUT_Y, NUM_INPUT_CHANNEL],
                      "num_classes": NUM_CLASSES,
                      "learning_rate": LEARNING_RATE}
    sendmsg(s, client_init_data, HOST, PORT)
    return 0


def send_global_vars(global_vars):
    global s, Target_PORT, Target_HOST, LEARNING_RATE
    set_global_vars={"msg":"set_global_vars",
                     "global_vars":global_vars,
                     "learning_rate":LEARNING_RATE}
    tempcnt=0
    for each_HOST,each_PORT in zip(Target_HOST,Target_PORT):
        tempcnt=tempcnt+1
        if chosen_client[str(tempcnt)]==1:
            tcp_tunnel_send(set_global_vars, each_HOST, each_PORT+1) #规定：客户端的tcp_port为其udp_port+1
    return 0


def get_client_vars(clientdata):
    global client_vars_sum, tate_of_client_train, now_epoch
    if clientdata["epoch"]!=now_epoch:
        return 1
    data_size = clientdata["datasize"]
    current_client_vars = clientdata["client_vars"]
    client_id=clientdata["ID"]
    state_of_client_train[str(client_id)]=1
    weight = 1 / chosen_client_nums
    if client_vars_sum is None:
        client_vars_sum = [weight * x for x in current_client_vars]
    else:
        for index in range(len(current_client_vars)):
            client_vars_sum[index]=client_vars_sum[index]+weight*current_client_vars[index]
    return 0


def test_client(clientdata):
    global now_epoch, Target_HOST, Target_PORT, symbol, state_of_client_test, global_loss
    acc=clientdata["acc"]
    loss=clientdata["loss"]
    client_id=clientdata["ID"]
    global_loss=global_loss+loss
    client_epoch=clientdata["epoch"]
    test_batchsize=clientdata["test_batchsize"]
    time_slot=clientdata["time_slot"]
    print("[epoch {}, {} inst] Testing ACC: {:.4f}, Loss: {:.4f}".format(
        client_epoch, test_batchsize, acc, loss))
    f = open(symbol, "a", encoding="UTF-8", newline="")
    csvwriter = csv.writer(f)
    csvwriter.writerow([str(Target_HOST[int(client_id)-1])+'_'+str(Target_PORT[int(client_id)-1]), client_epoch, now_epoch, acc, loss, time.time(), time_slot, "test_message"])
    f.close()
    if client_epoch==-1:
        state_of_client_test[str(client_id)]=1
    return 0


def distribute_dataset(HOST, PORT, ID):
    global Client_nums, s, total_data_size
    (x_train, y_train), (x_test, y_test)=tf.keras.datasets.cifar10.load_data()
    print("Dataset: train-%d, test-%d" % (len(x_train), len(x_test)))
    total_data_size=len(x_train)
    eachtrain=len(x_train)/Client_nums
    eachtest=len(x_test)/Client_nums
    for i,client_id in enumerate(ID):
        temptrain=eachtrain*client_id
        temptest=eachtest*client_id
        client_dataset = {"msg": "client_dataset",
                       "client_dataset_train_a": int(temptrain-len(x_train)/Client_nums),
                       "client_dataset_train_b": int(temptrain-1),
                       "client_dataset_test_a" : int(temptest-len(x_test)/Client_nums),
                       "client_dataset_test_b": int(temptest)}
        print(client_dataset)
        sendmsg(s, client_dataset, [HOST[i]], [PORT[i]])
    return 0


def distribute_model(HOST, PORT):
    global s, client_epoch, batchsize, NUM_INPUT_X, NUM_INPUT_Y, NUM_INPUT_CHANNEL, NUM_CLASSES, LEARNING_RATE, test_batchsize, drop_rate, epoch
    build_clients(HOST, PORT)
    client_model={"msg": "distribute_model",
                  "client_epoch": client_epoch,
                  "batchsize": batchsize,
                  "test_batchsize": test_batchsize,
                  "drop_rate": drop_rate,
                  "epoch":epoch}
    sendmsg(s,client_model, HOST, PORT)
    return 0


def detect_client(target_HOST=Target_HOST, target_PORT=Target_PORT):
    global s, Target_HOST, Target_PORT, Target
    for HOST,PORT in zip(target_HOST,target_PORT):
        temp=[i for i in zip([HOST],[PORT])]
        detect_client_msg={
              "msg":"detect_client",
              "ID": Target.index(temp[0])+1
        }
        sendmsg(s, detect_client_msg, [HOST], [PORT])
    return 0


def start_client():
    global s, Target_HOST, Target_PORT
    start_client_msg={
        "msg":"start"
    }
    sendmsg(s, start_client_msg, Target_HOST, Target_PORT)
    return 0

def stop_client():
    global s, Target_HOST, Target_PORT
    stop_client_msg={
        "msg":"stop"
    }
    sendmsg(s, stop_client_msg, Target_HOST, Target_PORT)

def get_ready():
    global state_of_client
    for key in state_of_client:
        if state_of_client[key] != 3:
            return int(key)
    return 0


def detect_client_recv(clientdata):
    global state_of_client, detect_client_recv_bool
    state_of_client[str(clientdata["ID"])]=clientdata["client_state"]  #0初始状态，1已获得数据，2已获得模型，3准备训练
    detect_client_recv_bool=True


def check_state_of_client_train():
    global state_of_client_train, chosen_client
    tempcnt=0
    for key in state_of_client_train:
        if state_of_client_train[key]==0 and chosen_client[str(key)]==1:
            tempcnt=tempcnt+1
    return tempcnt


def check_state_of_client_test():
    global state_of_client_test, chosen_client
    tempcnt=0
    for key in state_of_client_test:
        if state_of_client_test[key]==0:
            tempcnt=tempcnt+1
    return tempcnt


def refresh_state_of_client_train():
    global state_of_client_train
    for key in state_of_client_train:
        state_of_client_train[key]=0
    return 0

def chose_client():
    global chosen_client, chosen_client_nums, Client_nums
    for key in chosen_client:
        chosen_client[key]=0
    tempcnt=0
    while tempcnt<chosen_client_nums:
        chosen=random.randint(1, Client_nums)
        if chosen_client[str(chosen)]==0:
            chosen_client[str(chosen)]=1
            tempcnt=tempcnt+1
    return 0

def send_server_now_epoch():
    global now_epoch, Target_PORT, Target_HOST, s
    server_now_epoch_msg={
        "msg": "server_now_epoch",
        "server_now_epoch": now_epoch
    }
    sendmsg(s ,server_now_epoch_msg ,Target_HOST,  Target_PORT)
    return 0

def get_lr(loss,t):
    global LEARNING_RATE, LEARNING_RATE_START, M, V
    if t<=10:
        LEARNING_RATE=LEARNING_RATE*M
    if t>10:
        LEARNING_RATE=LEARNING_RATE/V
    lr_f=open("lr.csv","a",encoding="UTF-8",newline="")
    lr_csvwriter = csv.writer(lr_f)
    lr_csvwriter.writerow([t,LEARNING_RATE])
    lr_f.close()
    return 0



def main_server(epoch):
    global state_of_client, client_vars_sum, detect_client_recv_bool, now_epoch, chosen_client, global_vars, global_loss, chosen_client_nums
    detect_client()
    distribute_dataset(Target_HOST, Target_PORT, Target_ID)
    distribute_model(Target_HOST, Target_PORT)
    detect_client_recv_bool = False
    detect_client()
    temp_ready=get_ready()
    while temp_ready>0:
        time.sleep(10)
        if detect_client_recv_bool is False:
            print("Client " + str(temp_ready) + "无响应")
        print("Client "+str(temp_ready)+" is not ready")
        if state_of_client[str(temp_ready)]==0:
            print("未获得数据和模型")
            distribute_dataset([Target_HOST[temp_ready-1]], [Target_PORT[temp_ready-1]], [temp_ready])
            distribute_model([Target_HOST[temp_ready-1]], [Target_PORT[temp_ready-1]])
            print("10s后重传...")
        if state_of_client[str(temp_ready)]==1:
            print("已获得数据，未获得模型")
            distribute_model([Target_HOST[temp_ready - 1]], [Target_PORT[temp_ready - 1]])
            print("10s后重传...")
        if state_of_client[str(temp_ready)]==2:
            print("已获得模型，未获得数据")
            distribute_dataset([Target_HOST[temp_ready - 1]], [Target_PORT[temp_ready - 1]], [temp_ready])
            print("10s后重传...")
        detect_client_recv_bool = False
        detect_client([Target_HOST[temp_ready - 1]], [Target_PORT[temp_ready - 1]])
        temp_ready = get_ready()
        print(state_of_client)
    print("所有client已经准备完毕")
    for each_epoch in range(0, epoch):
        chose_client()
        now_epoch= each_epoch
        refresh_state_of_client_train()
        client_vars_sum = None
        start_client()
        send_server_now_epoch()
        send_global_vars(global_vars)
        print("开始训练")
        print("正在训练第"+str(each_epoch)+"轮，等待客户端数据回传",end="")
        while check_state_of_client_train()>0:
            print(".",end="")
            time.sleep(1)
        global_vars=client_vars_sum
        global_loss=global_loss/chosen_client_nums
        get_lr(global_loss,each_epoch+1)
        print("")
        print("所有数据已接受完毕，第"+str(each_epoch)+"轮训练完毕")
    stop_client()
    for key in chosen_client:
        chosen_client[key]=1
    send_global_vars(global_vars)
    while check_state_of_client_test() > 0:
        print(".", end="")
        time.sleep(1)
    print("终轮测试已结束")


main_server(epoch)

f.close()
tcp_tunnel_s.close()
print("测试数据文件已保存")


with open('finalmodel.pkl', 'wb') as finalmodel:
    pickle.dump(global_vars, finalmodel)
print("模型已保存")

print("程序执行完毕")

