
""" Perform unit tests on the nano_library.py file
"""

import unittest

import nano_library

class Fake_dev:
    def __init__(self):
        self.expect = None

    def _handle(self, name):
        if self.expect != name:
            raise ValueError
        self.expect = None

    def reset(self):
        self._handle('reset')

    def write(self, addr, data, timeout):
        self._handle('write')
        self.write_addr = addr
        self.write_data = data
        self.write_timeout = timeout

    def read(self, addr, buflen, timeout):
        # TODO - this often comes after a write, so we cannot expect both
        #self._handle('write')
        self.read_addr = addr
        self.read_buflen = buflen
        self.read_timeout = timeout
        return "slartibartfast"

class TestK40_CLASS(unittest.TestCase):
    def setUp(self):
        self.object = nano_library.K40_CLASS()
        self.object.dev = Fake_dev()

    def tearDown(self):
        self.object = None

    def test_constants(self):
        hello  = "".join(map(chr, self.object.hello))
        unlock = "".join(map(chr, self.object.unlock))
        home   = "".join(map(chr, self.object.home))
        estop  = "".join(map(chr, self.object.estop))

        self.assertEqual(hello,  '\xa0')
        self.assertEqual(unlock, '\xa6\x00IS2PFFFFFFFFFFFFFFFFFFFFFFFFFF\xa6\x0f')
        self.assertEqual(home,   '\xa6\x00IPPFFFFFFFFFFFFFFFFFFFFFFFFFFF\xa6\xe4')
        self.assertEqual(estop,  '\xa6\x00IFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\xa6\x82')

    def test_say_hello(self):
        self.object.dev.expect = 'write'
        self.assertEqual(self.object.say_hello(), ['slartibartfast'])
        self.assertEqual(self.object.dev.write_data, self.object.hello)

    def test_send_array(self):
        test_data = 'aabbccdd'
        self.object.dev.expect = 'write'
        self.object.send_array(test_data)
        # TODO - why does send_array not return the read_data results?
        self.assertEqual(self.object.dev.write_data, test_data)

    # Several of these function calls have nested calls to dev functions,
    # which my dumb dev mock cannot handle:
    #   unlock_rail() calls say_hello()
    #   e_stop() calls say_hello()
    #   home_position() calls say_hello()

    def test_reset_usb(self):
        self.object.dev.expect = 'reset'
        self.object.reset_usb()

    def test_OneWireCRC(self):
        line = map(ord, 'AK0FFFFFFFFFFFFFFFFFFFFFFFFFFF')

        # Do we get the expected CRC?
        self.assertEqual( self.object.OneWireCRC(line), 0xa4 )

        # Now, are the magic arrays simply normal packets with a valid CRC?
        self.assertEqual(
            self.object.OneWireCRC(self.object.unlock[1:-2]),
            self.object.unlock[-1] 
        )
        self.assertEqual(
            self.object.OneWireCRC(self.object.home[1:-2]),
            self.object.home[-1] 
        )
        self.assertEqual(
            self.object.OneWireCRC(self.object.estop[1:-2]),
            self.object.estop[-1] 
        )

    def test_send_data(self):
        data = map(ord, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

        self.object.dev.expect = 'write'
        self.object.send_data(data, update_gui=None, stop_calc=None)

        # FIXME - confirm the data actually being sent

    def test_rapid_move(self):
        self.object.dev.expect = 'write'
        self.object.rapid_move(1000, 1000)

        # Deeper probing of this data block is done in test_egv
        data = map(ord, '\xa6\x00ILzzz235Bzzz235S1PFFFFFFFFFFFF\xa6\x8a')
        self.assertEqual(self.object.dev.write_data, data)

    def test_hex2dec(self):
        input = ["40","e7"]
        output = [64, 231]
        self.assertEqual(self.object.hex2dec(input), output)