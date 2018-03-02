import json
import unittest
import time
import zlib
from Packet import Packet
from PacketLog import PacketLog

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

    def test_compress(self):
        self.__init()
        compressed = zlib.compress(self.p.generateData())
        self.assertEqual(self.p.generateData(), zlib.decompress(compressed))

class TestPacketLog(unittest.TestCase):

    pl = ""
    p1 = ""
    p2 = ""
    p3 = ""
    p4 = ""
    p5 = ""

    def setUp(self):
        self.pl = PacketLog()
        self.p1 = Packet("some data", "data", 0)
        base = self.p1.get_base()
        self.p2 = Packet("some data", "data", 0, self.p1.get_seq_num(), base)
        self.p3 = Packet("some data", "data", 0, self.p2.get_seq_num(), base)
        self.p4 = Packet("some data", "data", 0, self.p3.get_seq_num(), base)
        self.p5 = Packet("some data", "data", 0, self.p4.get_seq_num(), base)

        self.pl.add_to_log(self.p1, time.time())
        self.pl.add_to_log(self.p2, time.time())
        self.pl.add_to_log(self.p3, time.time())
        self.pl.add_to_log(self.p4, time.time())
        self.pl.add_to_log(self.p5, time.time())

    def tearDown(self):
        self.pl = None
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.p4 = None
        self.p5 = None

    def test__update_unacked_packets(self):
        self.assertEquals(len(self.pl.get_packet_timers()), 5)
        self.pl.update_unacked_packets(self.p3.get_seq_num(), time.time() + 100, -1)
        self.assertEquals(len(self.pl.get_packet_timers()), 2)
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p4.get_seq_num()])
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p5.get_seq_num()])
        self.assertEqual(self.pl.get_dup_acks(), 0)

    def test_acking_packet_twice(self):
        self.test__update_unacked_packets()

        self.pl.update_unacked_packets(self.p3.get_seq_num(), time.time() + 100, -1)
        self.assertEquals(len(self.pl.get_packet_timers()), 2)
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p4.get_seq_num()])
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p5.get_seq_num()])
        self.assertEqual(self.pl.get_dup_acks(), 1)

    def test_acking_packet_four_times(self):
        self.test_acking_packet_twice()

        self.pl.update_unacked_packets(self.p3.get_seq_num(), time.time() + 100, -1)
        self.assertEquals(len(self.pl.get_packet_timers()), 2)
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p4.get_seq_num()])
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p5.get_seq_num()])
        self.assertEqual(self.pl.get_dup_acks(), 2)

        should_be_p4 = self.pl.update_unacked_packets(self.p3.get_seq_num(), time.time() + 100, -1)
        self.assertEquals(len(self.pl.get_packet_timers()), 2)
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p4.get_seq_num()])
        self.assertIsNotNone(self.pl.get_packet_timers()[self.p5.get_seq_num()])
        self.assertEqual(self.pl.get_dup_acks(), 3)

        self.assertEqual(should_be_p4, self.p4)
        self.assertEqual(should_be_p4.get_seq_num(), self.p4.get_seq_num())

    def test_acking_packet_until_empty(self):
        self.pl.update_unacked_packets(self.p1.get_seq_num(), time.time() + 100, -1)
        self.pl.update_unacked_packets(self.p2.get_seq_num(), time.time() + 100, -1)
        self.pl.update_unacked_packets(self.p3.get_seq_num(), time.time() + 100, -1)
        self.pl.update_unacked_packets(self.p4.get_seq_num(), time.time() + 100, -1)
        self.pl.update_unacked_packets(self.p5.get_seq_num(), time.time() + 100, -1)

        self.assertEqual(len(self.pl.get_packet_timers()), 0)

    def test_handle_packet_with_first_packet_same_as_base(self):
        p1_decoded = json.loads(self.p1.generateData())
        should_be_p1_seq = self.pl.handle_packet(p1_decoded)
        self.assertEqual(should_be_p1_seq, self.p1.get_seq_num())

    def test_handle_packet_with_first_packet_not_base(self):
        decoded = json.loads(self.p2.generateData())

        should_be_p1_minus_1 = self.pl.handle_packet(decoded)
        self.assertEqual(should_be_p1_minus_1, self.p1.get_seq_num() - 1)

    def test_handle_packet_second_packet_lost(self):
        p1_decoded = json.loads(self.p1.generateData())
        # assume p2 is dropped
        p3_decoded = json.loads(self.p3.generateData())
        self.pl.handle_packet(p1_decoded)
        should_be_ack_for_p1 = self.pl.handle_packet(p3_decoded)
        self.assertEqual(should_be_ack_for_p1, self.p1.get_seq_num())

    def test_handle_packet_second_packet_delivered_late(self):
        p1_decoded = json.loads(self.p1.generateData())
        p2_decoded = json.loads(self.p2.generateData())
        p3_decoded = json.loads(self.p3.generateData())
        p4_decoded = json.loads(self.p4.generateData())
        p5_decoded = json.loads(self.p5.generateData())

        self.pl.handle_packet(p1_decoded)
        self.pl.handle_packet(p3_decoded)
        should_be_ack_for_p1 = self.pl.handle_packet(p5_decoded)

        self.assertEqual(should_be_ack_for_p1, self.p1.get_seq_num())

        should_be_ack_for_p1 = self.pl.handle_packet(p4_decoded)

        self.assertEqual(should_be_ack_for_p1, self.p1.get_seq_num())

        should_be_ack_for_p5 = self.pl.handle_packet(p2_decoded)

        self.assertEqual(should_be_ack_for_p5, self.p5.get_seq_num())

    def test_update_buffer_packets(self):
        p1_decoded = json.loads(self.p1.generateData())
        p2_decoded = json.loads(self.p2.generateData())
        p3_decoded = json.loads(self.p3.generateData())
        p4_decoded = json.loads(self.p4.generateData())
        p5_decoded = json.loads(self.p5.generateData())

        self.pl.handle_packet(p1_decoded)

        self.assertEqual(0, len(self.pl.get_buffered_packet()))

        self.pl.handle_packet(p3_decoded)

        self.assertEqual(1, len(self.pl.get_buffered_packet()))

        should_be_ack_for_p1 = self.pl.handle_packet(p5_decoded)

        self.assertEqual(2, len(self.pl.get_buffered_packet()))
        self.assertEqual(should_be_ack_for_p1, self.p1.get_seq_num())

        should_be_ack_for_p1 = self.pl.handle_packet(p4_decoded)

        self.assertEqual(3, len(self.pl.get_buffered_packet()))
        self.assertEqual(should_be_ack_for_p1, self.p1.get_seq_num())

        should_be_ack_for_p5 = self.pl.handle_packet(p2_decoded)

        self.assertEqual(0, len(self.pl.get_buffered_packet()))
        self.assertEqual(should_be_ack_for_p5, self.p5.get_seq_num())







