#!/usr/bin/env python3
#
# id3v1_fileop.py
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

import stagger
from stagger.errors import *

class ID3v1FileOpTestCase(unittest.TestCase):
    def testAddDeleteTag(self):
        """Add/delete random tags to a file, verify integrity."""
        origdata = bytearray(random.randint(0, 255) for i in range(512))
        origdata[-128:-125] = b'\xFF\xFF\xFF'
        data = bytearray(origdata)
        file = io.BytesIO(data)
        try:
            self.assertRaises(NoTagError, stagger.id3v1.Tag1.read, file)
            tag = stagger.id3v1.Tag1()
            tag.title = "Title"
            tag.artist = "Artist"
            tag.album = "Album"
            tag.year = "2009"
            tag.comment = "Comment"
            tag.track = 13
            tag.genre = "Salsa"
            tag.write(file)
            tag.write(file)
            tag2 = stagger.id3v1.Tag1.read(file)
            self.assertEqual(tag, tag2)
            stagger.id3v1.Tag1.delete(file)
            self.assertEqual(file.getvalue(), origdata)
        finally:
            file.close()

suite = unittest.TestLoader().loadTestsFromTestCase(ID3v1FileOpTestCase)

if __name__ == "__main__":
    warnings.simplefilter("always", stagger.Warning)
    unittest.main(defaultTest="suite")
