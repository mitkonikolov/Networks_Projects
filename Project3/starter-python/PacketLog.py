#!/usr/bin/python -u

from Packet import Packet
import time
from Logger import Logger


class PacketLog(object):

    logger = Logger()

    # TODO add comments
    # sending window size
    sws = 30
    # timeout value
    timeout = 2
    # map of seq# -> (packet, time_sent)
    packets_timers = {}
    dup_acks = 0
    last_ack = 0
    # the alpha used for Karn/Partridge algo to update timeout
    alpha = 0.4

    # For the receiver:
    last_received = -1
    # map of seq# -> packet's data
    buffered_packets = {}

    prev_buffered = -0.1

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

    def update_log_time(self, packet, new_time):
        self.logger.log("[debug] set time to {}".format(new_time
        ))
        # self.logger.log("[debug] updating time, time before {}".format(
        #     self.packets_timers[packet.get_seq_num()][1]
        # ))
        self.packets_timers[packet.get_seq_num()] = (packet, new_time)
        self.logger.log("new time {}".format(
            self.packets_timers[packet.get_seq_num()][1]
        ))

    def retransmit_table(self, timeout_occurred=False):
        """ It goes through self.packets_timers and checks which packet or 
        packets have timed out. It compiles a list of timed out packets.
        This might be because a timeout has occured or simply because we want
        to check whether one has occured.
        :return: a list of timed out packets
        """
        out = []
        for packet in self.packets_timers:
            if time.time() - self.packets_timers[packet][1] > self.timeout:
                out.append(self.packets_timers[packet][0])
                timeout_occurred = True
        # exponential backoff on timeout
        if timeout_occurred:
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

    def update_unacked_packets(self, ack, receival_time, base, buffered_packet):
        """ Remove all the acked packets from the packets_timers table.
        Also updates the lask_ack and dup_acks
        :param ack: the ack we just received (the sequence number)
        :param receival_time: the time in microseconds when the packet was 
        received
        :return: the packet that needs to retransmitted or None
        """
        out = {}

        if ack < self.last_ack:
            return None

        result = None

        # this is a duplicate ACK
        if self.last_ack == ack or base - 1 == ack:
            self.dup_acks += 1
            # this might resubmit one last_ack earlier if we get base-1 3 times
            # but that's how I think is better
            if self.dup_acks >= 3:
                result = self.packets_timers[ack + 1][0]

        # this is not a duplicate ack
        if ack>self.last_ack and ack>=base and ack in self.packets_timers:
            sampleRTT = receival_time - self.packets_timers[ack][1]
        # a default value for sampleRTT
        else:
            sampleRTT = 0

        for key in self.packets_timers:
            # this is the packet that led to a dup ack - take its sample RTT
            # and remove it from the table because it is being acked through
            # buffered_packet
            if buffered_packet == key:
                sampleRTT = receival_time - self.packets_timers[key][1]
                if sampleRTT>0:
                    self.augment_timeout(sampleRTT)
                continue
            # this packet is not being ACKed
            if key > int(ack):
                out[key] = self.packets_timers[key]
            # this packet is being ACKed
            else:
                self.last_ack = ack
                self.dup_acks = 0
                self.sws += 1
                # if key == ack:
                #     sampleRTT = receival_time - self.packets_timers[key][1]
                if sampleRTT>0:
                    self.augment_timeout(sampleRTT)

        # keep only the unACKed packets in the dictionary
        self.packets_timers = out
        # check if any packets have expired
        return result

    def augment_timeout(self, sampleRTT, exp_back_off=False):
        """It updates the timeout value using the given sampleRTT in seconds
        according to the Karn/Partridge algorithm.
        
        :param sampleRTT: a sample RTT in seconds
        :return: None
        """
        self.logger.log("timeout was {}".format(self.timeout))
        # TODO: something wrong here, fix it
        if exp_back_off:
            # self.timeout += self.timeout
            self.timeout = self.timeout * 1.5
            # self.logger.log("[timeout change] timed out")
            # self.timeout = self.timeout
        else:
            self.logger.log("[timeout change] sampleRTT {}".format(sampleRTT))
            self.timeout = self.alpha*self.timeout + (1-self.alpha)*sampleRTT
        self.logger.log("new timeout is {}".format(self.timeout))

    def still_waiting_acks(self):
        """ Returns True if there are still ACKs that are being waited on.
        
        :return: bool indicating whether there are ACKs that are still being
        waited on
        """
        return len(self.get_packet_timers()) != 0

    def get_packet_timers(self):
        return self.packets_timers

    def get_dup_acks(self):
        return self.dup_acks

    # only used for receiver
    def handle_packet(self, decoded):
        seq = decoded["sequence"]
        base = decoded["base"]

        # if this is the first data packet received
        if self.last_received == -1:
            if seq == base:
                self.logger.log("### Logging {} to STDOUT. and base: {}".format(seq, base))
                self.logger.log_data(decoded["data"])
                self.last_received = self.update_buffer_packets(seq)
                return (self.last_received, -0.1)
            else:
                self.buffered_packets[seq] = decoded["data"]
                self.prev_buffered = seq
                return (base - 1, self.prev_buffered)
        else:
            if seq == self.last_received + 1:
                self.logger.log("### Logging {} to STDOUT".format(seq))
                self.logger.log_data(decoded["data"])
                # if this is the next packet we expect
                self.last_received = self.update_buffer_packets(seq)
                return (self.last_received, -0.1)
            elif seq > self.last_received + 1:
                # packet comes in out of order
                self.buffered_packets[seq] = decoded["data"]
                self.prev_buffered = seq
                return (self.last_received, self.prev_buffered)
            # duplicated packet, we have already received this

    def update_buffer_packets(self, seq):
        seq += 1
        while seq in self.buffered_packets:
            self.logger.log("### Logging {} to STDOUT".format(seq))
            self.logger.log_data(self.buffered_packets[seq])
            del self.buffered_packets[seq]
            seq += 1
        return seq - 1

    def get_buffered_packet(self):
        return self.buffered_packets

    def get_last_received(self):
        return self.last_received

    def get_prev_buffered(self):
        return self.prev_buffered
