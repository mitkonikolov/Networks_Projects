import unittest
from Packet import Packet

class TestPacket(unittest.TestCase):
    p = ""

    def __init(self):
        self.p = Packet("some data", "data", 0)

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

    def test__calculate_checksum(self):
        self.p = Packet("test data", "data", 0)
        checksum = self.p.get_checksum()
        self.assertTrue(checksum!="")
        self.assertTrue(self.p.is_good_crc(checksum, "test data"))
        self.assertFalse(self.p.is_good_crc(checksum, "some other message"))
        self.assertFalse(self.p.is_good_crc(checksum, ""))
        self.assertFalse(self.p.is_good_crc(checksum, 989832))


