import unittest
from bitstreamer import BitStreamer

class BitStreamerTest(unittest.TestCase):
    def test_parsePacketSize(self):
        tc = BitStreamer()
        self.assertEqual(tc.parsePacketSize("cccc"), 4)
        self.assertEqual(tc.parsePacketSize("hhh"), 6)
        self.assertEqual(tc.parsePacketSize("ffff"), 16)

def main():
    unittest.main()

if __name__ == '__main__':
    main()


