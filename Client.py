import warnings
warnings.filterwarnings("ignore")
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import socket
import threading
import dill
import tensorflow as tf
from tqdm import tqdm
import time
import json
import numpy as np
from collections import namedtuple
#import math
from Model import AlexNet
from tensorflow.keras.utils import to_categorical
import csv
import sys

data_size = None
client_vars = None
ID = None
client_state = 0
global_vars = None
input_shape = None
num_classes = None
learning_rate = None
client_dataset_train_a = None
client_dataset_train_b = None
client_dataset_test_a = None
client_dataset_test_b = None
client_epoch = None
batch_size = None
if_to_start = 0
if_to_stop = 0
next_epoch_var = 0
next_epoch_nowepoch = 0
test_batchsize = None
drop_rate = None
now_epoch= 0

##########网络部署###########
Client_HOST=sys.argv[1]
Client_PORT=int(sys.argv[2])
Client_PORT_TCP = int(sys.argv[3])
Server_HOST=sys.argv[4]
Server_PORT=int(sys.argv[5])
Server_PORT_TCP =int(sys.argv[6])
s= socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind((Client_HOST,Client_PORT))
tcp_tunnel_s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_tunnel_s.bind((Client_HOST, Client_PORT_TCP))
tcp_tunnel_s.listen(5)

symbol=str(time.time())+"_ID="+str(ID)+"_HOST="+Client_HOST+"_PORT="+str(Client_PORT)+".csv"

def sendmsg(mysocket,senddata,HOST,PORT):
    senddata = dill.dumps(senddata)
    mysocket.sendto(senddata, (HOST, PORT))
    print(HOST, PORT)
    return 0


def recvmsg(mysocket):
    while 1:
        try:
            clientdata, addr = mysocket.recvfrom(4096)
            clientdata = dill.loads(clientdata)
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
            tcp_end_time=time.time()
            tcp_tunnel_ss.close()
            f = open(symbol,"a",encoding="UTF-8",newline="")
            csvwriter=csv.writer(f)
            csvwriter.writerow([now_epoch, "", "", time.time(), tcp_end_time-tcp_start_time, "tcp_send"])
            f.close()
            return 0
        except:
            print("TCP传输失败，等待2s后重新尝试传输"+str(HOST)+"//"+str(PORT))
            time.sleep(2)
    return 0


def tcp_tunnel_recv(tcp_tunnel_s):
    global now_epoch, symbol
    while 1:
        try:
            tcp_start_time_recv=time.time()
            sock, addr = tcp_tunnel_s.accept()
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
            print("获取TCP传输，来自" + str(addr))
            clientdata=dill.loads(clientdata)
            tcp_end_time_recv=time.time()
            f = open(symbol,"a",encoding="UTF-8",newline="")
            csvwriter=csv.writer(f)
            csvwriter.writerow([now_epoch, "", "", time.time(), tcp_end_time_recv - tcp_start_time_recv, "tcp_recv"])
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
    if clientdata["msg"]=="set_global_vars":
        set_global_vars(clientdata)
    if clientdata["msg"]=="client_init_data":
        client_init_data(clientdata)
    if clientdata["msg"]=="client_dataset":
        client_dataset(clientdata)
    if clientdata["msg"]=="distribute_model":
        distribute_model(clientdata)
    if clientdata["msg"]=="detect_client":
        detect_client(clientdata)
    if clientdata["msg"]=="start":
        client_start(clientdata)
    if clientdata["msg"]=="server_now_epoch":
        set_now_epoch(clientdata)
    if clientdata["msg"]=="stop":
        client_stop(clientdata)
    return 0
################网络部署########################

def set_global_vars(clientdata):
    global global_vars, next_epoch_var, learning_rate
    global_vars=clientdata["global_vars"]
    learning_rate=clientdata["learning_rate"]
    next_epoch_var=1
    print("执行：set_global_vars，已设置：global_vars")
    return 0

def client_init_data(clientdata):
    global input_shape, num_classes, learning_rate
    input_shape=clientdata["input_shape"]
    num_classes=clientdata["num_classes"]
    learning_rate=clientdata["learning_rate"]
    print("执行：client_init_data，已设置：input_shape num_classes learning_rate")
    return 0

def client_dataset(clientdata):
    global client_dataset_train_a, client_dataset_train_b, client_dataset_test_a, client_dataset_test_b, client_state
    client_dataset_train_a=clientdata["client_dataset_train_a"]
    client_dataset_train_b=clientdata["client_dataset_train_b"]
    client_dataset_test_a=clientdata["client_dataset_test_a"]
    client_dataset_test_b=clientdata["client_dataset_test_b"]
    print("执行：client_dataset，已设置：dataset")
    if client_state==0:
        client_state=1
        return 0
    if client_state==1:
        return 0
    if client_state==2:
        client_state=3
        return 0
    return 0

def distribute_model(clientdata):
    global client_epoch, batch_size, test_batchsize, drop_rate
    client_epoch=clientdata["client_epoch"]
    batch_size=clientdata["batchsize"]
    test_batchsize = clientdata["test_batchsize"]
    drop_rate = clientdata["drop_rate"]
    print("执行：distribute_model，已设置：client_epoch batchsize")
    check_client_state()
    return 0

def detect_client(clientdata):
    global ID, client_state, s, Server_HOST, Server_PORT
    ID=clientdata["ID"]
    print("已被Server发现，本Client的ID为"+str(ID))
    detect_client_recv={
        "msg": "detect_client_recv",
        "ID": ID,
        "client_state": client_state
    }
    print("已响应Server的呼唤...当前client_state="+str(client_state))
    sendmsg(s, detect_client_recv, Server_HOST, Server_PORT)
    return 0

def client_start(clientdata):
    global if_to_start
    if_to_start = 1
    print("服务器已下达开始命令")
    return 0

def client_stop(clientdata):
    global if_to_stop
    if_to_stop = 1
    print("服务器已通知，训练结束")
    return 0


def set_now_epoch(clientdata):
    global now_epoch, next_epoch_nowepoch
    now_epoch=clientdata["server_now_epoch"]
    print("大循环已进行到第"+str(now_epoch)+"轮")
    next_epoch_nowepoch=1
    return 0

def check_client_state():
    global client_state, ID, input_shape, num_classes, learning_rate, client_epoch, batch_size, test_batchsize, drop_rate
    if ID is None:
        print("ID is None")
    if input_shape is None:
        print("input_shape is None")
    if num_classes is None:
        print("num_classes is None")
    if learning_rate is None:
        print("learning_rate is None")
    if client_epoch is None:
        print("client_epoch is None")
    if batch_size is None:
        print("batch_size is None")
    if test_batchsize is None:
        print("test_batchsize is None")
    if drop_rate is None:
        print("drop_rate is None")
    if (ID is not None) and (input_shape is not None) and (num_classes is not None) and (learning_rate is not None) and (client_epoch is not None) and (batch_size is not None) and (test_batchsize is not None) and (drop_rate is not None):
        if client_state==0:
            client_state=2
            return 0
        if client_state==1:
            client_state=3
            return 0
        if client_state==2:
            return 0
    return 0


def get_client_vars(mysocket, epoch):
    global Server_HOST, Server_PORT, ID, data_size, client_vars
    msg={
        "msg":"get_client_vars",
        "datasize": data_size,
        "client_vars": client_vars,
        "epoch": epoch,
        "ID": ID
    }
    tcp_tunnel_send(msg,Server_HOST,Server_PORT_TCP)


def test_client(mysocket, epoch, acc, loss, time_slot):
    global ID, Server_PORT, Server_HOST, test_batchsize, client_vars
    msg={
        "msg":"test_client",
        "acc":acc,
        "loss":loss,
        "ID": ID,
        "epoch": epoch,
        "test_batchsize": test_batchsize,
        "time_slot": time_slot
    }
    sendmsg(mysocket,msg,Server_HOST,Server_PORT)




FedModel = namedtuple('FedModel', 'X Y DROP_RATE train_op loss_op acc_op')


class Clients:
    def __init__(self, input_shape, num_classes, learning_rate, client_dataset_train_a, client_dataset_train_b, client_dataset_test_a, client_dataset_test_b):
        global data_size
        self.graph = tf.Graph()
        self.sess = tf.Session(graph=self.graph)

        # Call the create function to build the computational graph of AlexNet
        net = AlexNet(input_shape, num_classes, learning_rate, self.graph)
        self.model = FedModel(*net)

        # initialize
        with self.graph.as_default():
            self.sess.run(tf.global_variables_initializer())

        # Load Cifar-10 dataset
        # NOTE: len(self.dataset.train) == clients_num
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
        y_train = to_categorical(y_train, 10)
        y_test = to_categorical(y_test, 10)
        x_train = x_train.astype('float32') / 255
        x_test = x_test.astype('float32') / 255
        self.dataset_x_train = x_train[client_dataset_train_a:client_dataset_train_b]
        self.dataset_y_train = y_train[client_dataset_train_a:client_dataset_train_b]
        self.dataset_x_test = x_test[client_dataset_test_a:client_dataset_test_b]
        self.dataset_y_test = y_test[client_dataset_test_a:client_dataset_test_b]
        self.dataset_train_size = client_dataset_train_b - client_dataset_train_a + 1
        self.dataset_test_size = client_dataset_test_b - client_dataset_test_a + 1
        data_size = self.dataset_train_size

    def run_test(self, test_batchsize):
        with self.graph.as_default():
            if (test_batchsize<1) or (test_batchsize>self.dataset_test_size):
                test_batchsize=self.dataset_test_size
            batch_x = self.dataset_x_test[0:test_batchsize]
            batch_y = self.dataset_y_test[0:test_batchsize]
            feed_dict = {
                self.model.X: batch_x,
                self.model.Y: batch_y,
                self.model.DROP_RATE: 0
            }
        return self.sess.run([self.model.acc_op, self.model.loss_op],
                             feed_dict=feed_dict)

    def train_epoch(self, batch_size=32, dropout_rate=0.5):
        """
            Train one client with its own data for one epoch
            cid: Client id
        """
        datasize = self.dataset_train_size
        temp = 0
        print("start_train_epoch")################################################################################
        with self.graph.as_default():
            with tqdm(total=np.ceil(datasize/batch_size)) as bar:
                while temp < (datasize-batch_size):
                    batch_x = self.dataset_x_train[temp:temp+batch_size]
                    batch_y = self.dataset_y_train[temp:temp+batch_size]
                    feed_dict = {
                        self.model.X: batch_x,
                        self.model.Y: batch_y,
                        self.model.DROP_RATE: dropout_rate
                    }
                    self.sess.run(self.model.train_op, feed_dict=feed_dict)
                    temp=temp+batch_size
                    bar.update(1)

        return datasize

    def get_client_vars_class(self):
        """ Return all of the variables list """
        with self.graph.as_default():
            client_vars = self.sess.run(tf.trainable_variables())
        return client_vars

    def set_global_vars_class(self, global_vars):
        """ Assign all of the variables with global vars """
        with self.graph.as_default():
            all_vars = tf.trainable_variables()
            for variable, value in zip(all_vars, global_vars):
                variable.load(value, self.sess)


print("已运行")
while if_to_start == 0:
    time.sleep(1)
f = open(symbol,"w",encoding="UTF-8",newline="")
csvwriter=csv.writer(f)
csvwriter.writerow(["epoch","acc","loss","local_time","time_slot","operation"])
f.close()
Client = Clients(input_shape, num_classes, learning_rate, client_dataset_train_a, client_dataset_train_b, client_dataset_test_a, client_dataset_test_b)
while if_to_stop==0:
    while next_epoch_nowepoch==0 or next_epoch_var==0:
        print(".",end = "")
        if if_to_stop==1:
            break
        time.sleep(1)
    if if_to_stop==1:
        break
    next_epoch_nowepoch=0
    next_epoch_var=0
    if global_vars is not None:
        Client.set_global_vars_class(global_vars)
    print("开始训练")
    train_start_time=time.time()
    for ii_client_epoch in tqdm(range(0,client_epoch), desc='Client_Epoch'):
        Client.train_epoch(batch_size,drop_rate)
    train_end_time=time.time()
    print("当前轮训练完毕，回传数据到服务器，epoch="+str(now_epoch))
    acc, loss = Client.run_test(test_batchsize)
    print("epoch="+str(now_epoch)+" acc="+str(acc)+" loss="+str(loss))
    client_vars = Client.get_client_vars_class()
    test_client(s, now_epoch, acc, loss, train_end_time-train_start_time)
    get_client_vars(s, now_epoch)
    print("等待下一轮训练指令",end = "")
    f = open(symbol,"a",encoding="UTF-8",newline="")
    csvwriter=csv.writer(f)
    csvwriter.writerow([now_epoch, acc, loss, time.time(), train_end_time-train_start_time, "test_message"])
    f.close()
print("")
print("全部训练完成！")
print("等待最终模型分发！")
while next_epoch_var==0:
    print(".",end="")
    time.sleep(1)
if global_vars is not None:
    Client.set_global_vars_class(global_vars)
final_acc, final_loss=Client.run_test(Client.dataset_test_size)
print("Final!!! "+" acc="+str(final_acc)+" loss="+str(final_loss))
test_client(s, -1, final_acc, final_loss,-1)
f = open(symbol,"a",encoding="UTF-8",newline="")
csvwriter=csv.writer(f)
csvwriter.writerow([-1, final_acc, final_loss,time.time(),"","final_test"])
f.close()
tcp_tunnel_s.close()
print("程序执行完毕")

