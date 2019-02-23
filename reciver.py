from socket import *
import sys
import os
import pickle
import hashlib
import io
import time
import timeit


print("reciving data")
if os.path.exists(str(sys.argv[2])):
    os.remove(str(sys.argv[2]))
f = open(str(sys.argv[2]),"w+")
log = open("reciver_log.log","w+")
serverSocket = socket(AF_INET, SOCK_DGRAM)
server_address = ("127.0.0.1", int(sys.argv[1]))
serverSocket.bind(server_address)
store = ''
data = {'SEQ':0,'CHECKSUM':'','DATA':'','SYN':0,'DATA_SIZE':0}
entire_data = { i : {'SEQ':0,'DATA':''} for i in range(0,10000)}
ack_window = {i : 0 for i in range(0,10000)}
set = 0
data_recived = 0
total_segments = 0
data_segments = 0
data_segments_biterror = 0
duplicate_data_segments = 0
duplicate_ACKS = 0
while data['DATA'] != "DONE":
    rec, address = serverSocket.recvfrom(4096)
    data = pickle.loads(rec)
    if data["SYN"] == 3:
        break
    data_recived += len(data['DATA'])
    total_segments += 1
    if data['SYN'] == 1 and set == 0 and ack_window[data['SEQ']] == 0:
        t0 = timeit.default_timer()
        t1 = timeit.default_timer()
        log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-t0),"S",str(0),str(0),str(0)))
        entire_data = { i : {'SEQ':0,'DATA':'','LEN':0} for i in range(0,data['DATA_SIZE'])}
        ack_window = {i : 0 for i in range(0,data['DATA_SIZE'])}
        ack_count = {i : 0 for i in range(0,data['DATA_SIZE'])}
        ack_keys = {i : 0 for i in range(0,data['DATA_SIZE'])}
        set = 1
        ack_window[data['SEQ']] = 1
        log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"SA",str(0),str(0),str(1)))
        serverSocket.sendto(str(data['SEQ']), address)
    if data['SYN'] == 1 and set == 1 and ack_window[data['SEQ']] == 0:
        t1 = timeit.default_timer()
        serverSocket.sendto(str(data['SEQ']), address) 
        log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(1)))
        ack_window[data['SEQ']] = 1
    m = hashlib.md5(data['DATA'])
    if ack_window[data['SEQ']] == 0:
        data_segments += 1
        if m.hexdigest() == data['CHECKSUM']:
            t1 = timeit.default_timer()
            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-t0),"D",str(data['len']+1),str(len(data['DATA'])),str(1)))
            for keys in ack_window:
                if ack_window[keys] == 0 and keys < data['SEQ']:
                    if keys > 1:
                        if ack_keys[keys-1] == 0:
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[keys-1]['LEN']+1)))
                        else:
                            duplicate_ACKS += 1
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dup","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[keys-1]['LEN']+1)))
                        ack_keys[keys-1] += 1
                    serverSocket.sendto(str(keys - 1), address)
                    break
                if keys >= data['SEQ']:
                    if keys > 1:
                        if ack_keys[data['SEQ']] == 0:
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(data['len']+1)))
                        else:
                            duplicate_ACKS += 1
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dup","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(data['len']+1)))
                        ack_keys[data['SEQ']] += 1
                    serverSocket.sendto(str(data['SEQ']), address)
                    break
            ack_window[data['SEQ']] = 1
            entire_data[data['SEQ']]['SEQ'] = data['SEQ']
            entire_data[data['SEQ']]['DATA'] = data['DATA']
            entire_data[data['SEQ']]['LEN'] = data['len']
            continue
        else:
            data_segments_biterror += 1
            t1 = timeit.default_timer()
            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv/corr","{0:.3f}".format(t1-t0),"D",str(data['len']+1),str(len(data['DATA'])),str(1)))
            for keys in ack_window:
                if ack_window[keys] == 0 and keys > 1 and keys < data['SEQ']:
                    if keys > 1:
                        if ack_keys[keys-1] == 0:
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[keys-1]['LEN']+1)))
                        else:
                            duplicate_ACKS += 1
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dup","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[keys-1]['LEN']+1)))
                        ack_keys[keys-1] += 1
                    serverSocket.sendto(str(keys - 1), address)
                    break
                if keys >= data['SEQ']:
                    if keys > 1:
                        if ack_keys[data['SEQ']-1] == 0:
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[data['SEQ']-1]['LEN']+1)))
                        else:
                            duplicate_ACKS += 1
                            t1 = timeit.default_timer()
                            log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dup","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[data['SEQ']-1]['LEN']+1)))
                        ack_keys[data['SEQ']-1] += 1
                    serverSocket.sendto(str(data['SEQ']-1), address)
                    break
    else:
        if data['SYN'] == 0:
            data_segments += 1
            duplicate_data_segments += 1
            count = 0
            for keys in ack_window:
                if ack_window[keys] == 1:
                    count += 1
                if ack_window[keys] == 0:
                    if keys > 1:
                        duplicate_ACKS += 1
                        log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dup","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[keys-1]['LEN']+1)))
                    serverSocket.sendto(str(keys - 1), address)
                    break
                if count == len(ack_window):
                    log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[count - 1]['LEN']+1)))
                    serverSocket.sendto(str(count - 1), address)
        

t1 = timeit.default_timer()
log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-t0),"F",str(entire_data[len(entire_data)-1]['LEN']+1),str(0),str(1)))           
store = ''
t1 = timeit.default_timer()
log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"A",str(1),str(0),str(entire_data[len(entire_data)-1]['LEN']+2)))
serverSocket.sendto(str(entire_data[len(entire_data)-1]['LEN']+1), address)
rec = ''
serverSocket.sendto(str(entire_data[len(entire_data)-1]['LEN']+2), address)
log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-t0),"F",str(1),str(0),str(entire_data[len(entire_data)-1]['LEN']+2)))
while rec != 'A':
    rec, address = serverSocket.recvfrom(4096)
t1 = timeit.default_timer()
log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-t0),"A",str(entire_data[len(entire_data)-1]['LEN']+2),str(0),str(2)))
for keys in entire_data:
    store += entire_data[keys]['DATA']
    f.write(entire_data[keys]['DATA'])
log.write("==============================================\n")
log.write("Amount of data received (bytes)    "+str(data_recived+1)+"\n")
log.write("Total Segments Received            "+str(total_segments+2)+"\n")
log.write("Data segments received             "+str(data_segments)+"\n")
log.write("Data segments with Bit Errors      "+str(data_segments_biterror)+"\n")
log.write("Duplicate data segments received   "+str(duplicate_data_segments)+"\n")
log.write("Duplicate ACKs sent                "+str(duplicate_ACKS)+"\n")
log.write("==============================================\n")
log.close()
f.close()
serverSocket.close()

    
