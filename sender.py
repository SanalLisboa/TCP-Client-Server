import sys
import socket
import time
import timeit
from socket import *
import os
import struct
import hashlib
import pickle
import random
from threading import Thread
import time
import timeit
from operator import xor
import io
import threading

class Sender:
    def __init__(self):
        ack = 0
        flag = 0
        mss = int(sys.argv[5])
        self.mass = mss
        self.cd = float(sys.argv[9])
        self.dp = float(sys.argv[7])
        self.pdl = float(sys.argv[12])
        window_1 = int(sys.argv[4])
        self.window_size = window_1//mss
        filename = str(sys.argv[3])
        f = io.open(filename,"rb")
        self.data = []
        a = f.read(mss)
        size_store = []
        temp = 0
        cs = 0
        temp += len(a)
        size_store.append(temp)
        while a:
            self.data.append(a)
            a = f.read(mss)
            if a:
                temp += len(a)
                size_store.append(temp)
        self.size = size_store
        n = 0
        self.i = 0
        self.entire_data = { i : {'SEQ':0,'len':0,'CHECKSUM':'','DATA':'','SYN':0,'DATA_SIZE':len(self.data)+2} for i in range(0,len(self.data)+2)}
        count = 0
        self.entire_data1 = { i : {'SEQ':0,'len':0,'CHECKSUM':'','DATA':'', 'SYN':0,'DATA_SIZE':len(self.data)+2} for i in range(0,len(self.data)+2)}
        for i in range(0,2):
            self.entire_data[i]['SEQ'] = count
            self.entire_data1[i]['SEQ'] = count
            self.entire_data[i]['SYN'] = 1
            self.entire_data1[i]['SYN'] = 1
            self.entire_data[count]['len'] = i
            self.entire_data1[count]['len'] = i
            count+=1
        for l in self.data:
            self.entire_data[count]['SEQ'] = count
            m = hashlib.md5(l)
            self.entire_data[count]['len'] = size_store[count-2]
            self.entire_data1[count]['len'] = size_store[count-2]
            self.entire_data[count]['CHECKSUM'] = m.hexdigest()
            self.entire_data[count]['DATA'] = l
            self.entire_data1[count]['SEQ'] = count
            m = hashlib.md5(l)
            self.entire_data1[count]['CHECKSUM'] = m.hexdigest()
            self.entire_data1[count]['DATA'] = l
            count += 1
        self.count1 = 0
        i = 0
        self.ack_count = 0
        self.ack_window = {i : '' for i in range(0,len(self.data)+2)}
        self.window = self.window_size
        self.t0 = timeit.default_timer()
        self.log = open("sender_log.txt","w+")
        self.round_trip = {i : {'sent_time': 0, 'recive_time': 0} for i in range(0,len(self.data)+3)}
        self.delayed_packet = {'SEQ':0,'len':0,'CHECKSUM':'','DATA':'', 'SYN':0,'DATA_SIZE':len(self.data)+2}
        self.packet_delayed = 0
        self.delayed_packet_timer = 0
        self.maxDelay = int(sys.argv[13])
        self.temp_timer = 0
        self.pdup = float(sys.argv[8])
        self.preorder = float(sys.argv[10])
        self.is_reordered = 0
        self.reorder_count = 0
        self.maxOrder = int(sys.argv[11])
        self.reorder_packet = {}
        self.seed = int(sys.argv[14])
        self.real_count = 0
        self.segments_droped = 0
        self.segments_corrupted = 0
        self.segments_reordered = 0
        self.segments_duplicated = 0
        self.segments_delayed = 0
        self.ToutRetransmission = 0
        self.FTransmission = 0
        self.DupAcks = 0
        self.Segments = 0
        self.pld_segments = 0
        self.gamma = int(sys.argv[6])
        self.EstimatedRTT = 0.5
        self.DevRTT = 0.25
        random.seed(self.seed)
        self.TimeoutInterval = self.EstimatedRTT + 4 * self.DevRTT
        self.recently_sent = 0
        self.rev = 0

    def corupt_data(self,cd):
        rn = random.random()
        if cd > rn:
            return True
        return False

    def drop_packet(self,dp):
        rn = random.random()
        if dp > rn:
            return True
        return False

    def delay_packet(self,pdl):
        rn = random.random()
        if pdl > rn:
            return True
        return False

    def duplicate_packet(self, pdup):
        rn = random.random()
        if pdup > rn:
            return True
        return False

    def packet_reorder(self, preorder):
        rn = random.random()
        if preorder > rn:
            return True
        return False

    def delay_time(self):
        rn = random.randint(0,self.maxDelay)
        return rn/1000

    def calculate_TimeoutIntervel(self, SampleRTT):
        self.EstimatedRTT = 0.875 * self.EstimatedRTT + 0.125 * SampleRTT
        self.DevRTT = 0.75 * self.DevRTT + 0.25 * abs(SampleRTT - self.EstimatedRTT)
        TimeoutInterval = self.EstimatedRTT * self.gamma * self.DevRTT
        if TimeoutInterval < 0.5:
            self.TimeoutInterval = 0.5
            return
        if TimeoutInterval > 1.0:
            self.TimeoutInterval = 1.0
            return
        self.TimeoutInterval = TimeoutInterval
        


    def send_data(self, clientSocket, packet_no):
        self.Segments += 1
        if self.drop_packet(self.dp) and packet_no > 1:
            self.pld_segments += 1
            self.segments_droped += 1
            t1 = timeit.default_timer()
            self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("RXT/drop","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            return
        if self.duplicate_packet(self.pdup) and packet_no > 1:
            self.pld_segments += 1
            self.segments_duplicated += 1
            t1 = timeit.default_timer()
            if self.count1 > 1:
                self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/RXT/dup","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            sending_data = pickle.dumps(self.entire_data1[packet_no])
            clientSocket.send(sending_data)
        if self.corupt_data(self.cd) and packet_no > 1:
            self.pld_segments += 1
            self.segments_corrupted += 1
            t1 = timeit.default_timer()
            self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/RXT/corr","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            packet = self.entire_data[packet_no]
            p = list(packet['DATA'])
            p[0] = str(int(xor(bool(p[0]), bool(1))))
            packet['DATA'] = ''.join(p)
            sending_data = pickle.dumps(packet)
            t1 = timeit.default_timer()
            clientSocket.send(sending_data)
        else:
            if self.packet_reorder(self.preorder) and self.count1 > 1 and self.is_reordered == 0:
                self.pld_segments += 1
                self.segments_reordered += 1
                self.is_reordered = 1
                self.reorder_packet = self.entire_data[packet_no]
                return
            if self.delay_packet(self.pdl) and self.count1 > 1:
                self.pld_segments += 1
                self.segments_delayed += 1
                delayed_packet = self.entire_data1[packet_no]
                t = threading.Timer(self.delay_time(), self.send_delayed_packet, [clientSocket, delayed_packet])
                t.start()
                return
            sending_data = pickle.dumps(self.entire_data1[packet_no])
            t1 = timeit.default_timer()
            self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/RXT","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            clientSocket.send(sending_data)
            self.pld_segments += 1
        packet = {}
        return

    def send_data_timeout(self, clientSocket, packet_no):
        self.Segments += 1
        if self.drop_packet(self.dp) and packet_no > 1:
            self.pld_segments += 1
            self.segments_droped += 1
            t1 = timeit.default_timer()
            self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("drop","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            return
        if self.duplicate_packet(self.pdup) and packet_no > 1:
            self.pld_segments += 1
            self.segments_duplicated += 1
            t1 = timeit.default_timer()
            if self.count1 > 1:
                self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dup","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            sending_data = pickle.dumps(self.entire_data1[packet_no])
            clientSocket.send(sending_data)
        if self.corupt_data(self.cd) and packet_no > 1:
            self.pld_segments += 1
            self.segments_corrupted += 1
            t1 = timeit.default_timer()
            self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/corr","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            packet = self.entire_data[packet_no]
            p = list(packet['DATA'])
            p[0] = str(int(xor(bool(p[0]), bool(1))))
            packet['DATA'] = ''.join(p)
            sending_data = pickle.dumps(packet)
            t1 = timeit.default_timer()
            clientSocket.send(sending_data)
        else:
            if self.packet_reorder(self.preorder) and self.count1 > 1 and self.is_reordered == 0:
                self.pld_segments += 1
                self.segments_reordered += 1
                self.is_reordered = 1
                self.reorder_packet = self.entire_data[packet_no]
                return
            if self.delay_packet(self.pdl) and self.count1 > 1:
                self.pld_segments += 1
                self.segments_delayed += 1
                delayed_packet = self.entire_data1[packet_no]
                t = threading.Timer(self.delay_time(), self.send_delayed_packet, [clientSocket, delayed_packet])
                t.start()
                return
            sending_data = pickle.dumps(self.entire_data1[packet_no])
            t1 = timeit.default_timer()
            self.pld_segments += 1
            self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[packet_no]['len']+1),str(len(self.entire_data1[packet_no]['DATA'])),str(1)))
            clientSocket.send(sending_data)
        packet = {}
        return
                                        
    def send(self, clientSocket):
        print 'Sending'
        while self.ack_window[len(self.ack_window)-1] == '':
            self.temp_timer = timeit.default_timer()
            if self.count1 <= self.window and self.real_count <= self.window and self.count1 < len(self.data)+2 and self.real_count < len(self.data)+2:
                self.recently_sent = self.count1
                self.Segments += 1
                if self.is_reordered == 1 and self.reorder_count == self.maxOrder:
                    t1 = timeit.default_timer()
                    if self.count1 > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/rord","{0:.3f}".format(t1-self.t0),"D",str(self.reorder_packet['len']+1),str(len(self.reorder_packet['DATA'])),str(1)))
                    sending_data = pickle.dumps(self.reorder_packet)
                    clientSocket.send(sending_data)
                    self.is_reordered = 0
                    self.reorder_count = 0
                    continue
                if self.is_reordered == 1 and self.reorder_count < self.maxOrder:
                    self.reorder_count += 1
                if self.drop_packet(self.dp) and self.count1 > 1:
                    self.pld_segments += 1
                    t1 = timeit.default_timer()
                    self.round_trip[self.count1]['sent_time'] = t1-self.t0
                    self.segments_droped += 1
                    t1 = timeit.default_timer()
                    if self.count1 > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("drop","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[self.count1]['len']+1),str(len(self.entire_data[self.count1]['DATA'])),str(1)))
                    self.count1 += 1
                    self.real_count += 1
                    continue
                if self.duplicate_packet(self.pdup) and self.count1 > 1:
                    self.pld_segments += 1
                    self.segments_duplicated += 1
                    t1 = timeit.default_timer()
                    if self.count1 > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dup","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[self.count1]['len']+1),str(len(self.entire_data[self.count1]['DATA'])),str(1)))
                    sending_data = pickle.dumps(self.entire_data[self.count1])
                    clientSocket.send(sending_data)
                    self.real_count += 1
                if self.corupt_data(self.cd) and self.count1 > 1:
                    self.pld_segments += 1
                    t1 = timeit.default_timer()
                    self.round_trip[self.count1]['sent_time'] = t1-self.t0
                    self.segments_corrupted += 1
                    t1 = timeit.default_timer()
                    if self.count1 > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/corr","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[self.count1]['len']+1),str(len(self.entire_data[self.count1]['DATA'])),str(1)))
                    packet = self.entire_data[self.count1]
                    p = list(packet['DATA'])
                    p[0] = str(int(xor(bool(p[0]), bool(1))))
                    packet['DATA'] = ''.join(p)
                    sending_data = pickle.dumps(packet)
                    t1 = timeit.default_timer()
                else:
                    if self.packet_reorder(self.preorder) and self.count1 > 1 and self.is_reordered == 0:
                        self.pld_segments += 1
                        t1 = timeit.default_timer()
                        self.round_trip[self.count1]['sent_time'] = t1-self.t0
                        self.segments_reordered += 1
                        self.is_reordered = 1
                        self.reorder_packet = self.entire_data[self.count1]
                        self.count1 += 1
                        self.real_count += 1
                        continue
                    if self.delay_packet(self.pdl) and self.count1 > 1:
                        self.pld_segments += 1
                        self.segments_delayed += 1
                        t1 = timeit.default_timer()
                        delayed_packet = self.entire_data[self.count1]
                        self.round_trip[delayed_packet['SEQ']]['sent_time'] = t1-self.t0
                        t = threading.Timer(self.delay_time(), self.send_delayed_packet, [clientSocket, delayed_packet])
                        t.start()
                        self.count1 += 1
                        self.real_count += 1
                        continue
                    t1 = timeit.default_timer()
                    if self.count1 == 0:
                        t1 = timeit.default_timer()
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-self.t0),"S",str(0),str(0),str(0)))
                    if self.count1 == 1:
                        t1 = timeit.default_timer()
                        while self.rev == 0:
                            sanal = 0
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-self.t0),"SA",str(0),str(0),str(1)))
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-self.t0),"A",str(1),str(0),str(1)))
                    if self.count1 > 1:
                        self.pld_segments += 1
                        self.round_trip[self.count1]['sent_time'] = t1-self.t0
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[self.count1]['len']+1),str(len(self.entire_data[self.count1]['DATA'])),str(1)))
                    sending_data = pickle.dumps(self.entire_data[self.count1])
                clientSocket.send(sending_data)
                self.count1 += 1
                self.real_count += 1

            
    def recive(self,clientSocket):
        ack_recived = 0
        while 1:
            clientSocket.settimeout(self.TimeoutInterval)
            try:
                ack_recived = int(clientSocket.recv(1024))
                print 'ACK = ',self.entire_data1[ack_recived]['len']
                self.rev = 1
                if self.ack_window[ack_recived] == '' and self.round_trip[ack_recived]['sent_time']:
                    t1 = timeit.default_timer()
                    self.round_trip[ack_recived]['recive_time'] = t1-self.t0
                    sampleRTT = self.round_trip[ack_recived]['recive_time'] - self.round_trip[ack_recived]['sent_time']
                    self.calculate_TimeoutIntervel(sampleRTT)
                if self.ack_window[ack_recived] == 'a':
                    self.DupAcks += 1
                    t1 = timeit.default_timer()
                    if ack_recived > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv/DA","{0:.3f}".format(t1-self.t0),"A","1", "0",str(self.entire_data1[ack_recived]['len']+1)))
                    else:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv/DA","{0:.3f}".format(t1-self.t0),"A","1", "0",str(1)))
                    self.ack_window[ack_recived] = 'accessed'
                    continue
                if self.ack_window[ack_recived] == 'accessed':
                    self.DupAcks += 1
                    t1 = timeit.default_timer()
                    if ack_recived > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv/DA","{0:.3f}".format(t1-self.t0),"A","1", "0",str(self.entire_data1[ack_recived]['len']+1)))
                    else:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv/DA","{0:.3f}".format(t1-self.t0),"A","1", "0",str(1)))
                    self.ack_window[ack_recived] = 'retransmit'
                    continue
                if self.ack_window[ack_recived] == 'retransmit':
                    self.DupAcks += 1
                    self.FTransmission += 1
                    t1 = timeit.default_timer()
                    if ack_recived > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv/DA","{0:.3f}".format(t1-self.t0),"A","1", "0",str(self.entire_data1[ack_recived]['len']+1)))
                    else:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv/DA","{0:.3f}".format(t1-self.t0),"A","1", "0",str(1)))
                    self.ack_window[ack_recived] = 'a'
                    self.send_data(clientSocket, int(ack_recived)+1)
                    continue
                if self.ack_window[ack_recived] == '':
                    t1 = timeit.default_timer()
                    for keys in self.ack_window:
                        if keys <= ack_recived and self.ack_window[ack_recived] == '' and self.ack_window[keys] == '':
                            if self.count1 < len(self.data) + 2:
                                self.window += 1
                            self.ack_window[keys] = 'accesssed'
                        if keys > ack_recived:
                            break
                    self.ack_window[ack_recived] = 'accessed'
                    if ack_recived > 1:
                        self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-self.t0),"A","1", "0",str(self.entire_data1[ack_recived]['len']+1)))
                if int(ack_recived) >= len(self.data)+1:
                    clientSocket.settimeout(10)
                    packet = {'SEQ':0,'CHECKSUM':'','DATA':'','SYN':0,'DATA_SIZE':0}
                    packet['SEQ']= self.entire_data[len(self.entire_data)-1]['SEQ']+1
                    packet['DATA'] = "DONE"
                    packet['SYN'] = 3
                    sending_data = pickle.dumps(packet)
                    t1 = timeit.default_timer()
                    self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-self.t0),"F",str(self.entire_data[len(self.entire_data)-1]['len']+1),str(0),str(1)))
                    clientSocket.send(sending_data)
                    rec = clientSocket.recv(1024)
                    rec = ''
                    while rec != '':
                        rec = clientSocket.recv(1024)
                    t1 = timeit.default_timer()
                    self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-self.t0),"A",str(1),str(0),str(self.entire_data[len(self.entire_data)-1]['len']+2)))
                    while rec == '':
                        rec = clientSocket.recv(1024)
                    t1 = timeit.default_timer()
                    self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("rcv","{0:.3f}".format(t1-self.t0),"F",str(1),str(0),str(self.entire_data[len(self.entire_data)-1]['len']+2)))
                    clientSocket.send('A')
                    t1 = timeit.default_timer()
                    self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd","{0:.3f}".format(t1-self.t0),"A",str(self.entire_data[len(self.entire_data)-1]['len']+2),str(0),str(2)))
                    clientSocket.close()
                    self.log.write("=============================================================\n")
                    self.log.write("Size of the file (in Bytes)                      "+str(self.size[-1])+"\n")
                    self.log.write("Segments transmitted (including drop & RXT)      "+str(self.Segments+2)+"\n")
                    self.log.write("Number of Segments handled by PLD                "+str(self.pld_segments)+"\n")
                    self.log.write("Number of Segments dropped                       "+str(self.segments_droped)+"\n")
                    self.log.write("Number of Segments Corrupted                     "+str(self.segments_corrupted)+"\n")
                    self.log.write("Number of Segments Re-ordered                    "+str(self.segments_reordered)+"\n")
                    self.log.write("Number of Segments Duplicated                    "+str(self.segments_duplicated)+"\n")
                    self.log.write("Number of Segments Delayed                       "+str(self.segments_delayed)+"\n")
                    self.log.write("Number of Retransmissions due to TIMEOUT         "+str(self.ToutRetransmission)+"\n")
                    self.log.write("Number of FAST RETRANSMISSION                    "+str(self.FTransmission)+"\n")
                    self.log.write("Number of DUP ACKS received                      "+str(self.DupAcks)+"\n")
                    self.log.write("=============================================================")
                    self.log.close()
                    break
            except timeout:
                self.ToutRetransmission += 1
                self.send_data_timeout(clientSocket, ack_recived + 1)
                if self.count1 > len(self.data)+1 and int(ack_recived) >= len(self.data)+1:
                    break
                
            
    def send_delayed_packet(self, clientSocket, delayed_packet):
        try:
            t1 = timeit.default_timer()
            self.log.write("{0:20}{1:10}{2:10}{3:10}{4:10}{5:10}\n".format("snd/dely","{0:.3f}".format(t1-self.t0),"D",str(self.entire_data[delayed_packet['SEQ']]['len']+1),str(self.mass),str(1)))
            sending_data = pickle.dumps(delayed_packet)
            clientSocket.send(sending_data)
        except:
            send_data = 0
        
    
clientSocket = socket(AF_INET, SOCK_DGRAM)
reciver_IP = str(sys.argv[1])
reciver_port = int(sys.argv[2])
clientSocket.connect((reciver_IP, reciver_port))
instance_of_sender = Sender()
thread1 = Thread(target = instance_of_sender.send, args = (clientSocket,))
thread2 = Thread(target = instance_of_sender.recive, args = (clientSocket,))
thread1.start()
thread2.start()
while thread2.isAlive():
    continue
