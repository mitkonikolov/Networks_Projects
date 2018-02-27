#!/usr/bin/python -u

from Packet import Packet
import time

class PacketLog(object):

    def __init_(self, sws = 5, timeout =  2):
        # map of seq# -> (packet, time_sent)
        self.packets_timers = {}

        # sending window size
        self.sws = sws

        # timeout of a packet
        self.timeout = timeout

        self.dup_acks = 0
        self.last_ack = 0

    def add_to_log(self, packet, time):
        if self.sws > 0:
            self.packets_timers[packet.get_seq_num()] = (packet, time)

    def retransmit_table(self):
        out = []
        for packet in self.packets_timers:
            if time.time() - self.packets_timers[packet][1] > self.timeout:
                out.append(self.packets_timers[packet][0])
        return out

    def get_timeout(self):
        return self.timeout

    def get_sws(self):
        return self.sws

    def update_sws(self, offset):
        self.sws += offset

    def update_unacked_packets(self, ack):
        out = {}

        if self.last_ack == ack:
            self.dup_acks += 1
            if self.dup_acks >=3 :
                return self.packets_timers[ack + 1][0]

        for key in self.packets_timers:
            if key > int(ack):
                out[key] = self.packets_timers[key]
            else:
                self.last_ack = ack
                self.dup_acks = 0
                self.sws += 1
        return None