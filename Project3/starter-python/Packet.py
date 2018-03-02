#!/usr/bin/python -u

import random
import zlib
from Logger import Logger
import time
import json


class Packet(object):
    logger = Logger()
    # the packet represented as string would be at most 1500 bytes
    MSG_SIZE = 1500


    def __init__(self, data, flag, ack_num, prev_seq_num = None, base = None):
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
            dack - the packet sends and acknowledges data in the same time
        :param ack_num: an int sequence number of the packet being ACKed
        :return: None
        :param prev_seq_num: an int sequence number of the previous sent 
        packet or the sequence number of the packet that is being acknowledged
        :return: None
        '''

        # this is the first packet to be sent
        if prev_seq_num is None and flag != "ack":
            self.seq_num = 0
            self.gen_random_seq_num()
            self.base = self.get_seq_num()
        # this is a subsequent packet
        else:
            self.seq_num = prev_seq_num
            if flag == "data" and base is not None:
                self.increment_seq_num()
                self.base = base
            elif flag == "ack" and prev_seq_num != ack_num:
                self.logger.log("[error] prev_seq_num and ack_num must be the same")
                raise RuntimeError("prev_seq_num and ack_num must be the same")
        self.data = data
        self.flag = flag
        self.ack_num = ack_num
        self.crc32 = self.__calculate_checksum(data)


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
        # a wraparound has occured so a new random sequence number is generated
        # TODO the receiver should somehow be notified about this
        if old_seq_num > self.seq_num:
            self.gen_random_seq_num()

    def __calculate_checksum(self, data):
        """Calculates the checksum on the given data. Because it works with
        binary data, the string (which is unicode by default) needs to be turned
        into binary.
        
        :param data: the str for which to calculate checksum 
        :return: None
        """
        return hex(zlib.crc32(data.encode()) & 0xffffffff)

    def get_checksum(self):
        """ Getter for crc32.
        
        :return: self.crc32
        """
        return self.crc32

    def generateData(self, eof = False):
        if self.flag == "ack":
            return json.dumps({
                "sequence": self.seq_num,
                "data": self.data,
                "crc32": self.crc32,
                "ack": self.ack_num,
                "eof": eof,
                "flag": self.flag,
                "base": -1
            })
        else:
            return json.dumps({
                "sequence": self.seq_num,
                "data": self.data,
                "crc32": self.crc32,
                "ack": self.ack_num,
                "eof": eof,
                "flag": self.flag,
                "base": self.base
            })

    def send_packet(self, sock, dest, eof = False):
        """ Sends this packet (self) using the given sock to the given dest.
        :param sock: the socket to use
        :param dest: the address is a pair (hostaddr, port)
        :return: the time it sends the packet
        """
        msg = self.generateData(eof)

        self.logger.log("sending {}\n".format(msg))

        if sock.sendto(msg, dest) < len(msg):
            self.logger.log("[error] unable to fully send packet")
            return -1
        else:
            self.logger.log("[send data] " + str(self.seq_num) + " (" +
                            str(len(self.data)) +
                            ")")
        return time.time()

    def check_ack(self, raw_data):
        try:
            self.logger.log("raw data {}\n".format(raw_data))
            decoded = json.loads(raw_data)

            if (decoded['flag'] == "ack") and (decoded['ack'] == decoded[
                'sequence']):
                self.logger.log("[recv ack] {}".format(decoded['sequence']))
                return decoded['ack']
        except:
            self.logger.log("an exception occured")

        self.logger.log("[recv corrupt packet]")
        return False

    def is_good_crc(self, decoded_crc, decoded_data):
        """Calculates whether the decoded_crc matches the given decoded_data.
        
        :param decoded_crc: a string representing a CRC
        :param decoded_data: a string representing the data that has arrived
        :return: a bool based on whether the decoded_crc matches decoded_data
        """
        calculated_crc = self.__calculate_checksum(str(decoded_data))
        out = decoded_crc == calculated_crc
        if not out:
            self.logger.log("invalid crc for ack, received {} but calculated {}"
                            .format(decoded_crc, calculated_crc))
        return out

    def set_ack_num(self, ack_num):
        """ Sets the ack_num and seq_num of this packet to the given ack_num.
        
        :param ack_num: an int to which to set both self.ack_num and 
        self.seq_num
        :return: None 
        """
        self.ack_num = ack_num
        self.seq_num = ack_num

    def get_msg_size(self):
        """ Get the message size for this packet.
        
        :return: self.MSG_SIZE
        """
        return self.MSG_SIZE

    # def set_base(self, new_base):
    #     self.logger.log("setting base from {} to a new base {}".format(self.base, new_base))
    #     self.base = new_base

    def get_base(self):
        return self.base