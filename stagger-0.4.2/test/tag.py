#!/usr/bin/env python3
#
# tag.py
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
import os.path
import warnings

import stagger
from stagger.id3 import *



class TagTestCase(unittest.TestCase):
    def testBasic(self):
        for cls, frm in (stagger.Tag22, TT2), (stagger.Tag23, TIT2), (stagger.Tag24, TIT2):
            tag = cls()
            # New tag must be empty
            self.assertEqual(len(tag), 0)

            # Set a frame using a single string, see if it's in the tag
            tag[frm] = "Foobar"
            self.assertTrue(frm.frameid in tag)
            self.assertTrue(frm in tag)
            self.assertEqual(len(tag), 1)
            self.assertEqual(len(tag._frames[frm.frameid]), 1)
            # Compare value to hand-constructed frame
            self.assertEqual(len(tag[frm].text), 1)
            self.assertEqual(tag[frm].text[0], "Foobar")
            self.assertEqual(tag[frm], frm(encoding=None, text=["Foobar"]))

            # Override the above text frame with a multivalue text frame
            tag[frm] = ("Foo", "bar", "baz")
            self.assertEqual(len(tag), 1)
            self.assertEqual(len(tag._frames[frm.frameid]), 1)
            self.assertEqual(tag[frm], frm(encoding=None, text=["Foo", "bar", "baz"]))

            # Delete frame from tag, verify it's gone
            del tag[frm]
            self.assertEqual(len(tag), 0)
            self.assertTrue(frm not in tag)
            self.assertTrue(frm.frameid not in tag)

    def testPadding(self):
        for tagcls, frames in ((stagger.Tag22, (TT2, TP1)), 
                               (stagger.Tag23, (TIT2, TPE1)), 
                               (stagger.Tag24, (TIT2, TPE1))):
            # Create a simple tag
            tag = tagcls()
            for frame in frames:
                tag[frame] = frame.frameid.lower()
        
            # Try encoding tag with various padding options
            tag.padding_max = 0
            tag.padding_default = 0
            data_nopadding_nohint = tag.encode()
            data_nopadding_hint = tag.encode(size_hint=500)
            length = len(data_nopadding_nohint)
            self.assertEqual(len(data_nopadding_nohint), len(data_nopadding_hint))
            self.assertTrue(data_nopadding_nohint == data_nopadding_hint)

            tag.padding_max = 1000
            data_max_nohint = tag.encode()
            data_max_hint = tag.encode(size_hint=500)
            data_max_largehint = tag.encode(size_hint=5000)
            self.assertEqual(len(data_max_nohint), length)
            self.assertEqual(len(data_max_hint), 500)
            self.assertEqual(len(data_max_largehint), length)
            self.assertTrue(data_max_nohint[10:] == data_max_hint[10:length])

            tag.padding_default = 250
            data_default_nohint = tag.encode()
            data_default_okhint = tag.encode(size_hint=500)
            data_default_largehint = tag.encode(size_hint=2000)
            data_default_smallhint = tag.encode(size_hint=20)
            self.assertEqual(len(data_default_nohint), length + 250)
            self.assertEqual(len(data_default_okhint), 500)
            self.assertEqual(len(data_default_largehint), length + 250)
            self.assertEqual(len(data_default_smallhint), length + 250)

    def testFrameEncoding(self):
        for tagcls, frm in ((stagger.Tag22, TT2), 
                            (stagger.Tag23, TIT2), 
                            (stagger.Tag24, TIT2)):
            tag = tagcls()
            value = frm.frameid.lower()
            tag[frm] = value
            tag.padding_max = 0
            
            # By default, tag should use Latin-1 to encode value (it contains only ASCII).
            data = tag.encode()
            self.assertNotEqual(data.find(value.encode("latin-1") + b"\x00"), -1)

            # Now override encoding, see that frame is encoded accordingly.
            old_encodings = tag.encodings
            tag.encodings = ("utf-16",)
            data = tag.encode()
            self.assertEqual(data.find(value.encode("latin-1") + b"\x00"), -1)
            self.assertNotEqual(data.find(value.encode("utf-16") + b"\x00\x00"), -1)
            tag.encodings = old_encodings
            
            # Now change value to contain non-Latin-1 chars
            value = "Lőrentey Károly"
            tag[frm] = value
            data = tag.encode()
            if tagcls is stagger.Tag24: 
                # Stagger falls back to utf-8 for 2.4 frames.
                self.assertNotEqual(data.find(value.encode("utf-8") + b"\x00"), -1)
            else: 
                # Other versions fall back to utf-16.
                self.assertNotEqual(data.find(value.encode("utf-16") + b"\x00\x00"), -1)
            
            # Force UTF-16-BE encoding.
            tag.encodings = ("utf-16-be",)
            data = tag.encode()
            self.assertNotEqual(data.find(value.encode("utf-16-be") + b"\x00\x00"), -1)

            
    def testFrameOrder(self):
        # 24.stagger.sample-01.id3 contains a simple test tag that has file frames
        # in the following order:
        #
        # TIT2("TIT2"), TPE1("TPE1"), TALB("TALB"), TRCK("TRCK"), TPE2("TPE2")
        
        testfile = os.path.join(os.path.dirname(__file__), "samples", 
                                "24.stagger.sample-01.id3")
        framelist = [TRCK, TPE2, TALB, TIT2, TPE1]

        # Read tag, verify frame ordering is preserved
        tag = stagger.read_tag(testfile)
        self.assertEqual(len(tag), 5) 
        self.assertEqual(set(tag.keys()), set(frame.frameid for frame in framelist))
        self.assertEqual([frame.frameid for frame in tag.frames(orig_order=True)], 
                         [frame.frameid for frame in framelist])

        # Test frame contents
        for framecls in framelist:
            # tag[TIT2] == tag["TIT2"]
            self.assertTrue(framecls in tag)
            self.assertTrue(framecls.frameid in tag)
            self.assertEqual(tag[framecls], tag[framecls.frameid])

            # type(tag[TIT2]) == TIT2
            self.assertTrue(isinstance(tag[framecls], framecls))

            # Each frame contains a single string, which is the frame id in lowercase.
            self.assertEqual(len(tag[framecls].text), 1)
            self.assertEqual(tag[framecls].text[0], framecls.frameid.lower())

        # Encode tag with default frame ordering, verify result is different.

        with open(testfile, "rb") as file:
            filedata = file.read()

        tag.padding_max = 0

        # Default sorting order is different.
        tagdata = tag.encode()
        self.assertEqual(len(tagdata), len(filedata))
        self.assertFalse(tagdata == filedata)

        # Override the sort order with an empty list, 
        # verify resulting order is the same as in the original file.

        tag.frame_order = stagger.tags.FrameOrder()
        tagdata = tag.encode()
        self.assertTrue(tagdata == filedata)

        tag2 = stagger.decode_tag(tagdata)
        self.assertTrue(tag == tag2)

    def testMultipleStrings(self):
        for cls in (stagger.Tag23, stagger.Tag24):
            # Versions 2.3 and 2.4 have support for multiple values in text frames.
            tag = cls()
            tag.padding_max = 0
            tag[TIT2] = ("Foo", "Bar", "Baz")
            self.assertEqual(len(tag[TIT2].text), 3)
            data = tag.encode()
            dtag = stagger.decode_tag(data)
            self.assertEqual(len(dtag[TIT2].text), 3)
            self.assertEqual(dtag[TIT2].text, tag[TIT2].text)

        # Version 2.2 has no such support, so stagger merges multiple strings.
        tag = stagger.Tag22()
        tag.padding_max = 0
        tag[TT2] = ("Foo", "Bar", "Baz")
        self.assertEqual(len(tag[TT2].text), 3)
        with warnings.catch_warnings(record=True) as ws:
            data = tag.encode()
            self.assertEqual(len(ws), 1)
            self.assertEqual(ws[0].category, stagger.FrameWarning)
        dtag = stagger.decode_tag(data)
        self.assertEqual(len(dtag[TT2].text), 1)
        self.assertEqual(dtag[TT2].text, ["Foo / Bar / Baz"])

    def testEmptyTag(self):
        for cls in (stagger.Tag22, stagger.Tag23, stagger.Tag24):
            tag = cls()
            # Empty tags should encode as an empty byte sequence
            # (i.e., no tag header or padding).
            self.assertEqual(len(tag.encode()), 0)

    def testEmptyStrings(self):
        # 24.stagger.empty-strings.id3 consists of a TIT2 frame with 13 extra
        # NUL characters at the end.
        testfile = os.path.join(os.path.dirname(__file__), "samples", 
                                "24.stagger.empty-strings.id3")
        with warnings.catch_warnings(record=True) as ws:
            tag = stagger.read_tag(testfile)
            self.assertEqual(tag[TIT2].text, ["Foobar"])
            self.assertEqual(len(ws), 1)
            self.assertEqual(ws[0].category, stagger.FrameWarning)    
            self.assertEqual(ws[0].message.args, ("TIT2: Stripped 13 empty strings "
                             "from end of frame",))

suite = unittest.TestLoader().loadTestsFromTestCase(TagTestCase)

if __name__ == "__main__":
    warnings.simplefilter("always", stagger.Warning)
    unittest.main(defaultTest="suite")
