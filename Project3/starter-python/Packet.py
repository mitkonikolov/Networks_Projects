#!/usr/bin/python -u

import random
import zlib
from Logger import Logger


class Packet(object):
    logger = Logger()
    # the packet represented as string would be at most 1500 bytes
    MSG_SIZE = 1500


    def __init__(self, data, flag, ack_num, error_checking, prev_seq_num=None):
        '''If prev_seq_num is not passed, the constructor is used for creating 
        the first packet to ever be sent.
        
        If prev_seq_num is passed, the constructor is used for creating any 
        subsequent packets. 
        This constructor would be used both by the sender and receiver.
        Therefore, when data is being sent, the sequence number will be 
        automatically be incremented. However, if only an ACK is being 
        transferred, then prev_seq_num, self.seq_num and ack_num 
        must always be the same.
        
        :param prev_seq_num: an int sequence number of the previous sent 
        packet or the sequence number of the packet that is being acknowledged
        :param data: a string data message
        :param flag: a string indicating whether data, ack or both is being 
        sent. It is a string that can take the following values:
            data - the packet only sends data
            ack - the packet only acknowledges data
            dack - the packet sends and acknowledges data in the same time
        :param ack_num: an int sequence number of the packet being ACKed
        :param error_checking: a number for cyclic redundancy check
        :return: None
        :param prev_seq_num: an int sequence number of the previous sent 
        packet or the sequence number of the packet that is being acknowledged
        :return: None
        '''
        # this is the first packet to be sent
        if prev_seq_num is None:
            self.seq_num = 0
            self.gen_random_seq_num()
        # this is a subsequent packet
        else:
            self.seq_num = prev_seq_num
            if flag == "data":
                self.increment_seq_num()
            elif flag == "ack" and prev_seq_num != ack_num:
                self.logger.log(
                    "[error] prev_seq_num and ack_num must be the same")
                raise RuntimeError("prev_seq_num and ack_num must be the same")
        self.data = data
        self.flag = flag
        self.ack_num = ack_num
        self.error_checking = error_checking


    def gen_random_seq_num(self):
        ''' Generates a random integer different from 0 and sets the seq_num
        field to it.
        
        :return: None
        '''
        while True:
            random_num = random.choice('0123456789') + random.choice(
                '0123456789') + random.choice('0123456789') + \
                   random.choice('0123456789')
            if random_num != 0:
                break
        self.seq_num = int(random_num)


    def get_seq_num(self):
        ''' Return the current value of seq_num.
        
        :return: self.seq_num
        '''
        return self.seq_num


    def increment_seq_num(self):
        '''Increments the sequence number of the message and sets it to a new
        random value if it has wrapped around.
        
        :return: None 
        '''
        old_seq_num = self.seq_num
        self.seq_num += 1
        print(old_seq_num)
        print(self.seq_num)
        # a wraparound has occured so a new random sequence number is generated
        # TODO the receiver should somehow be notified about this
        if old_seq_num > self.seq_num:
            self.gen_random_seq_num()

    def __calculate_checksum(self):
        hex(zlib.crc32(self.data) & 0xffffffff)
