import unittest
from Packet import Packet

class TestPacket(unittest.TestCase):
    p = ""

    def __init(self):
        self.p = Packet("some data", "data", 0, 0)

    def testGen_Random_Seq_Num(self):
        # reset p
        self.__init()
        self.p.gen_random_seq_num()
        resultant_seq_num = self.p.get_seq_num()
        self.assertTrue(isinstance(resultant_seq_num, int))
        self.assertTrue(resultant_seq_num!=0)

    def testIncrement_Seq_Num(self):
        # reset p
        self.__init()
        self.p.gen_random_seq_num()
        old_seq_num = self.p.get_seq_num()
        self.p.increment_seq_num()
        new_seq_num = self.p.get_seq_num()
        self.assertTrue((new_seq_num-1) == old_seq_num)

