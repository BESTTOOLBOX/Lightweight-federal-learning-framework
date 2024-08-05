import numpy as np
from matplotlib import pyplot as plt
import csv
import math
import os
from scipy.interpolate import make_interp_spline
FaFbRecord = open("FaFbRecord.csv","w",encoding="UTF-8",newline="")
record_csvwriter=csv.writer(FaFbRecord)
record_csvwriter.writerow(["Time_ID","Strategy","Fa","Fb","Ra","Rb","Ra_y","Rb_y","收敛轮次","收敛Loss","收敛Acc","收敛消耗的时间"])
total_acc=[]
total_loss=[]
total_epoch_time=[] 
cnt_file=0
strategy=[]
for file_loc in os.listdir("./csv/"):
    strategy.append(file_loc.split('.')[1].split('_')[1])
    cnt_file=cnt_file+1
    print(file_loc)
    client_ip = []
    epoch = []
    acc = []
    loss = []
    localtime = []
    timeslot = []
    operation = []
    client_id = {}
    epoch_time=[]
    Fa = 1.5
    Fb = 1.38
    total_epoch = 0
    starttime = int(file_loc.split('.')[0])
    HOST = ["127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1",
            "127.0.0.1"]
    PORT = [50001,
            50003,
            50005,
            50007,
            50009,
            50011,
            50013,
            50015,
            50017,
            50019,
            50021,
            50023,
            50025,
            50027,
            50029,
            50031]
    ID = [0,
          1,
          2,
          3,
          4,
          5,
          6,
          7,
          8,
          9,
          10,
          11,
          12,
          13,
          14,
          15]
    for i in range(len(ID)):
        client_id[str(HOST[i]) + "_" + str(PORT[i])] = ID[i]
        client_id[str(HOST[i]) + "_" + str(int(PORT[i]) + 1)] = ID[i]
    now_epoch = -1
    max_time = 0
    timeplt = plt.figure(figsize=(120, 40))
    # timeplt=plt.figure(figsize=(30,10))
    with open('./csv/'+file_loc) as f:
        f_csv = csv.reader(f)
        headers = next(f_csv)
        for row in f_csv:
            client_ip.append(row[0])
            epoch.append(row[2])
            temprow2 = int(row[2])
            if temprow2 > total_epoch:
                total_epoch = temprow2
            acc.append(row[3])
            loss.append(row[4])
            localtime.append(row[5])
            timeslot.append(row[6])
            operation.append(row[7])
            x = [float(row[5]) - starttime, float(row[5]) - starttime + float(row[6])]
            y = [client_id[row[0]], client_id[row[0]]]
            if float(row[5]) - starttime + float(row[6]) > max_time:
                max_time = float(row[5]) - starttime + float(row[6])
            if row[7] == "tcp_send":
                communication_send, = plt.plot(x, y, 'b', linewidth=10, label="communication_send")
            if row[7] == "tcp_recv":
                communication_receive, = plt.plot(x, y, 'g', linewidth=10, label="communication_receive")
            if row[7] == "test_message":
                computation, = plt.plot([float(row[5]) - starttime - float(row[6]), float(row[5]) - starttime], y, "r",
                                        linewidth=10, label="computation")
            if int(row[2]) > now_epoch:
                now_epoch = int(row[2])
                epochline, = plt.plot([float(row[5]) - starttime, float(row[5]) - starttime], [0, 15], "k")
                epoch_time.append(float(row[5]) - starttime)
    total_epoch_time.append(epoch_time)
    timeplt.legend((communication_send, communication_receive, computation),
                   ("communication_send", "communication_receive", "computation"))
    plt.yticks(ID)
    plt.title("Client_Time  " + file_loc)
    timeplt.savefig("time_" + file_loc + ".png")

    total_epoch = total_epoch + 1

    accplt = plt.figure(figsize=(120, 40))
    client_acc_epoch = []
    client_acc_acc = []

    for eachid in ID:
        for i in range(len(client_ip)):
            if client_id[client_ip[i]] == eachid:
                if operation[i] == "test_message":
                    client_acc_epoch.append(int(epoch[i]))
                    client_acc_acc.append(float(acc[i]))
        plt.plot(client_acc_epoch, client_acc_acc, label=eachid, alpha=0.2)
        client_acc_epoch = []
        client_acc_acc = []
    avg_acc_epoch = [0 for i in range(0, total_epoch)]
    avg_epoch_clientnum = [0 for i in range(0, total_epoch)]
    for i in range(len(client_ip)):
        if operation[i] == "test_message":
            avg_acc_epoch[int(epoch[i])] = avg_acc_epoch[int(epoch[i])] + float(acc[i])
            avg_epoch_clientnum[int(epoch[i])] = avg_epoch_clientnum[int(epoch[i])] + 1
    for i in range(0, total_epoch):
        avg_acc_epoch[i] = avg_acc_epoch[i] / avg_epoch_clientnum[i]
    plt.plot([i for i in range(0, total_epoch)], avg_acc_epoch, label='average', linewidth=3)
    plt.legend(loc='upper left')
    plt.title("Acc_Epoch   " + file_loc)
    accplt.savefig("acc_epoch_" + file_loc + ".png")
    total_acc.append(avg_acc_epoch)

    lossplt = plt.figure(figsize=(120, 40))
    client_loss_epoch = []
    client_loss_loss = []

    for eachid in ID:
        for i in range(len(client_ip)):
            if client_id[client_ip[i]] == eachid:
                if operation[i] == "test_message":
                    client_loss_epoch.append(int(epoch[i]))
                    client_loss_loss.append(float(loss[i]))
        plt.plot(client_loss_epoch, client_loss_loss, label=eachid, alpha=0.2)
        client_loss_epoch = []
        client_loss_loss = []
    avg_loss_epoch = [0 for i in range(0, total_epoch)]
    avg_epoch_clientnum = [0 for i in range(0, total_epoch)]
    for i in range(len(client_ip)):
        if operation[i] == "test_message":
            avg_loss_epoch[int(epoch[i])] = avg_loss_epoch[int(epoch[i])] + float(loss[i])
            avg_epoch_clientnum[int(epoch[i])] = avg_epoch_clientnum[int(epoch[i])] + 1
    for i in range(0, total_epoch):
        avg_loss_epoch[i] = avg_loss_epoch[i] / avg_epoch_clientnum[i]

    plt.plot([i for i in range(0, total_epoch)], avg_loss_epoch, label='average', linewidth=3)
    total_loss.append(avg_loss_epoch)

    Fa_x = -1
    Fa_y = -1
    Fb_x = -1
    Fb_y = -1
    min_x = -1
    min_y = 10000000
    for i in range(0, total_epoch):
        if avg_loss_epoch[i] < Fa:
            if Fa_x < 0 and Fa_y < 0:
                Fa_x = i
                Fa_y = avg_loss_epoch[i]
        if avg_loss_epoch[i] < Fb:
            if Fb_x < 0 and Fb_y < 0:
                Fb_x = i
                Fb_y = avg_loss_epoch[i]
        if avg_loss_epoch[i] < min_y:
            min_x = i
            min_y = avg_loss_epoch[i]

    if Fa_x > 0 and Fa_y > 0:
        plt.plot([Fa_x], [Fa_y], 'x')
        plt.annotate("Fa epoch=" + str(Fa_x) + " loss=" + str(Fa_y), xy=(Fa_x, Fa_y))

    if Fb_x > 0 and Fb_y > 0:
        plt.plot([Fb_x], [Fb_y], 'x')
        plt.annotate("Fb epoch=" + str(Fb_x) + " loss=" + str(Fb_y), xy=(Fb_x, Fb_y))
    plt.plot([min_x], [min_y], 'x')
    plt.annotate("Min epoch=" + str(min_x) + " loss=" + str(min_y), xy=(min_x, min_y-0.1))

    plt.legend(loc='upper left')
    plt.title("Loss_Epoch   " + file_loc)
    lossplt.savefig("loss_epoch_" + file_loc + ".png")
    record_csvwriter.writerow([file_loc.split('.')[0],file_loc.split('.')[1].split('_')[1],Fa,Fb,Fa_x,Fb_x,Fa_y,Fb_y,min_x,min_y,avg_acc_epoch[min_x],epoch_time[min_x]])
FaFbRecord.close()

limit_max_epoch=150
smooth_degree=100
x=np.array([i for i in range(0,limit_max_epoch)])
x_new = np.linspace(x.min(),x.max(),20)

epoch_time_smooth = plt.figure(figsize=(30, 10))
x=np.array([i for i in range(0,limit_max_epoch)])
x_new = np.linspace(x.min(),x.max(),20)
for i in range(0,cnt_file):
    y=np.array(total_epoch_time[i][0:limit_max_epoch])
    y_smooth = make_interp_spline(x,y)(x_new)
    for ii in range(0,smooth_degree):
        x_temp = np.linspace(x_new.min(), x_new.max(), 30)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 20)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 30)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
    x_temp=np.linspace(x_new.min(),x_new.max(),1000)
    y_temp=make_interp_spline(x_new,y_smooth)(x_temp)
    plt.plot(x_temp, y_temp,label=strategy[i])
plt.legend()
epoch_time_smooth.savefig("epoch_time_total.png")

lossplt_smooth = plt.figure(figsize=(30, 10))
for i in range(0,cnt_file):
    y=np.array(total_loss[i][0:limit_max_epoch])
    y_smooth = make_interp_spline(x,y)(x_new)
    for ii in range(0,smooth_degree):
        x_temp = np.linspace(x_new.min(), x_new.max(), 30)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 20)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 30)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
    x_temp=np.linspace(x_new.min(),x_new.max(),1000)
    y_temp=make_interp_spline(x_new,y_smooth)(x_temp)
    plt.plot(x_temp, y_temp,label=strategy[i])
plt.legend()
lossplt_smooth.savefig("loss_epoch_total.png")

x=np.array([i for i in range(0,limit_max_epoch)])
x_new = np.linspace(x.min(),x.max(),20)
accplt_smooth = plt.figure(figsize=(30, 10))
for i in range(0,cnt_file):
    y=np.array(total_acc[i][0:limit_max_epoch])
    y_smooth = make_interp_spline(x,y)(x_new)
    for ii in range(0,smooth_degree):
        x_temp = np.linspace(x_new.min(), x_new.max(), 30)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 20)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 30)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
    x_temp=np.linspace(x_new.min(),x_new.max(),1000)
    y_temp=make_interp_spline(x_new,y_smooth)(x_temp)
    plt.plot(x_temp, y_temp,label=strategy[i])
plt.legend()
accplt_smooth.savefig("acc_epoch_total.png")


limit_max_epoch=25
accplt_time_smooth = plt.figure(figsize=(30, 10))
for i in range(0,cnt_file):
    x=np.array(total_epoch_time[i][0:limit_max_epoch])
    x_new = np.linspace(x.min(), x.max(), 10)
    y=np.array(total_acc[i][0:limit_max_epoch])
    y_smooth = make_interp_spline(x,y)(x_new)
    for ii in range(0,smooth_degree):
        x_temp = np.linspace(x_new.min(), x_new.max(), 15)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 10)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 15)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
    x_temp=np.linspace(x_new.min(),x_new.max(),1000)
    y_temp=make_interp_spline(x_new,y_smooth)(x_temp)
    plt.plot(x_temp, y_temp,label=strategy[i])
plt.legend()
accplt_time_smooth.savefig("acc_time_total.png")


lossplt_time_smooth = plt.figure(figsize=(30, 10))
for i in range(0,cnt_file):
    for ii in range(0,limit_max_epoch):
        if total_epoch_time[i][ii]<10000:
            limit_time_epoch=ii
    x=np.array(total_epoch_time[i][0:limit_time_epoch])
    x_new = np.linspace(x.min(), x.max(), 10)
    y=np.array(total_loss[i][0:limit_time_epoch])
    y_smooth = make_interp_spline(x,y)(x_new)
    for ii in range(0,smooth_degree):
        x_temp = np.linspace(x_new.min(), x_new.max(), 15)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 10)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
        x_temp = np.linspace(x_new.min(), x_new.max(), 15)
        y_temp = make_interp_spline(x_new, y_smooth)(x_temp)
    x_temp=np.linspace(x_new.min(),x_new.max(),1000)
    y_temp=make_interp_spline(x_new,y_smooth)(x_temp)
    plt.plot(x_temp, y_temp,label=strategy[i])
plt.legend()
lossplt_time_smooth.savefig("loss_time_total.png")
