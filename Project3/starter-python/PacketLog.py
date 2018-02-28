#!/usr/bin/python -u

from Packet import Packet
import time

class PacketLog(object):

    # TODO add comments
    # sending window size
    sws = 5
    # timeout value
    timeout = 2
    # map of seq# -> (packet, time_sent)
    packets_timers = {}
    dup_acks = 0
    last_ack = 0
    # the alpha used for Karn/Partridge algo to update timeout
    alpha = 0.8

    def __init_(self):
        self.dup_acks = 0
        self.last_ack = 0

    def add_to_log(self, packet, time):
        """ Adds a packet to self.packets_timers
        :param packet: the packet to add
        :param time: the sent time for the packet
        :return: None
        """
        if self.sws > 0:
            self.packets_timers[packet.get_seq_num()] = (packet, time)

    def retransmit_table(self):
        """ A timeout has occurred so it goes through self.packets_timers and 
        checks which packet or packets have timed out.
        It compiles a list of timed out packets.
        :return: a list of timed out packets
        """
        out = []
        for packet in self.packets_timers:
            if time.time() - self.packets_timers[packet][1] > self.timeout:
                out.append(self.packets_timers[packet][0])
        # exponential backoff on timeout
        self.augment_timeout(0, True)
        return out

    def get_timeout(self):
        """ Getting for timeout.
        :return: self.timeout
        """
        return self.timeout

    def get_sws(self):
        """ Getting for sws.
        :return: self.sws
        """
        return self.sws

    def update_sws(self, offset):
        """ Update the sending window size
        :param offset: integer by which to change sws
        :return: None
        """
        self.sws += offset

    def update_unacked_packets(self, ack, receival_time):
        """ Remove all the acked packets from the packets_timers table.
        Also updates the lask_ack and dup_acks
        :param ack: the ack we just received
        :param receival_time: the time in microseconds when the packet was 
        received
        :return: the packet that needs to retransmitted or None
        """
        out = {}

        # this is a duplicate ACK
        if self.last_ack == ack:
            self.dup_acks += 1
            if self.dup_acks >= 3 :
                return self.packets_timers[ack + 1][0]

        for key in self.packets_timers:
            # this packet is not being ACKed
            if key > int(ack):
                out[key] = self.packets_timers[key]
            # this packet is being ACKed
            else:
                self.last_ack = ack
                self.dup_acks = 0
                self.sws += 1
                sampleRTT = receival_time - self.packets_timers[key][1]
                self.augment_timeout(sampleRTT)
        return None

    def augment_timeout(self, sampleRTT, exp_back_off=False):
        """It updates the timeout value using the given sampleRTT in seconds
        according to the Karn/Partridge algorithm.
        
        :param sampleRTT: a sample RTT in seconds
        :return: None
        """
        if exp_back_off:
            self.timeout += self.timeout
        else:
            self.timeout = self.alpha*self.timeout + (1-self.alpha)*sampleRTT