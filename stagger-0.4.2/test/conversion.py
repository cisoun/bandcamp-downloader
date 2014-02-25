#!/usr/bin/env python3
#
# conversion.py
# From the stagger project: http://code.google.com/p/stagger/
#
# Copyright (c) 2009-2011 Karoly Lorentey  <karoly@lorentey.hu>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# 
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import unittest
import random
import io
import warnings

from stagger.errors import *
from stagger.conversion import *

class ConversionTestCase(unittest.TestCase):
    def random_data(self, length=100):
        for i in range(length):
            r = random.randint(0, 10)
            if r < 3:
                yield 255
            elif r < 6:
                yield 0
            else:
                yield random.randint(0, 255)

    def testUnsync(self):
        def contains_sync(data):
            for i in range(len(data) - 1):
                if data[i] == 255 and data[i+1] & 0xE0:
                    return True

        self.assertEqual(Unsync.encode(b"\x00\xFF\x00\xFF\xD0\xFF"),
                         b"\x00\xFF\x00\x00\xFF\x00\xD0\xFF\x00")
        self.assertEqual(Unsync.decode(b"\x00\xFF\x00\x00\xFF\x00\xD0\xFF\x00"),
                         b"\x00\xFF\x00\xFF\xD0\xFF")

        for i in range(20):
            r = bytes(self.random_data(100))
            e = Unsync.encode(r)
            self.assertFalse(contains_sync(e))
            self.assertTrue(Unsync.decode(e) == r)

    def testUnsyncReader(self): 
        for i in range(20):
            r = bytes(self.random_data(100))
            e = Unsync.encode(r)
            file = UnsyncReader(io.BytesIO(e))
            self.assertTrue(file.read(len(r)) == r)

    def testSyncsafe(self):
        self.assertEqual(Syncsafe.encode(1, width=1), b"\x01")
        self.assertEqual(Syncsafe.encode(127, width=1), b"\x7F")
        self.assertRaises(ValueError, Syncsafe.encode, 128, width=1)
        self.assertRaises(ValueError, Syncsafe.encode, -1, width=4)
        self.assertEqual(Syncsafe.encode(1, width=2), b"\x00\x01")
        self.assertEqual(Syncsafe.encode(128, width=2), b"\x01\x00")
        self.assertEqual(Syncsafe.encode(130, width=2), b"\x01\x02")
        
        self.assertEqual(Syncsafe.decode(b"\x01"), 1)
        self.assertEqual(Syncsafe.decode(b"\x7F"), 127)
        self.assertRaises(ValueError, Syncsafe.decode, b"\xFF")
        self.assertEqual(Syncsafe.decode(b"\x00\x01"), 1)
        self.assertEqual(Syncsafe.decode(b"\x01\x00"), 128)
        self.assertEqual(Syncsafe.decode(b"\x01\x02"), 130)

        for i in range(100):
            r = random.randint(0, 1 << 35)
            e = Syncsafe.encode(r, width=5)
            d = Syncsafe.decode(e)
            self.assertEqual(r, d)
            self.assertTrue(all(not b & 0x80 for b in e))

    def testInt8(self):
        self.assertEqual(Int8.encode(1, width=1), b"\x01")
        self.assertEqual(Int8.encode(1, width=2), b"\x00\x01")
        self.assertEqual(Int8.encode(127, width=1), b"\x7F")
        self.assertEqual(Int8.encode(128, width=1), b"\x80")
        self.assertRaises(ValueError, Int8.encode, -1, width=4)
        self.assertEqual(Int8.encode(1, width=2), b"\x00\x01")
        self.assertEqual(Int8.encode(128, width=2), b"\x00\x80")
        self.assertEqual(Int8.encode(258, width=2), b"\x01\x02")
        
        self.assertEqual(Int8.decode(b"\x01"), 1)
        self.assertEqual(Int8.decode(b"\x00\x01"), 1)
        self.assertEqual(Int8.decode(b"\x7F"), 127)
        self.assertEqual(Int8.decode(b"\x80"), 128)
        self.assertEqual(Int8.decode(b"\xFF"), 255)
        self.assertEqual(Int8.decode(b"\x00\x01"), 1)
        self.assertEqual(Int8.decode(b"\x01\x00"), 256)
        self.assertEqual(Int8.decode(b"\x01\x02"), 258)

        for i in range(100):
            r = random.randint(0, 1 << 35)
            e = Int8.encode(r, width=5)
            d = Int8.decode(e)
            self.assertEqual(r, d)

suite = unittest.TestLoader().loadTestsFromTestCase(ConversionTestCase)

if __name__ == "__main__":
    warnings.simplefilter("always", stagger.Warning)
    unittest.main(defaultTest="suite")
