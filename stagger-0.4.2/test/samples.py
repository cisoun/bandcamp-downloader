#!/usr/bin/env python3
#
# samples.py
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
import os
import os.path
import warnings

import stagger
from stagger.id3 import *

def list_id3(path):
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for file in sorted(files):
            if file.endswith(".id3"):
                yield os.path.join(root, file)

def generate_test(file):
    def test(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", stagger.Warning)
            tag = stagger.read_tag(file)

            prefix_to_class = {
                "22.": stagger.Tag22,
                "23.": stagger.Tag23,
                "24.": stagger.Tag24
                }

            # Check tag version based on filename prefix
            basename = os.path.basename(file)
            self.assertTrue(any(basename.startswith(prefix) for prefix in prefix_to_class))
            for prefix in prefix_to_class:
                if basename.startswith(prefix):
                    self.assertEqual(type(tag), prefix_to_class[prefix])
                    self.assertEqual(tag.version, int(prefix[1]))

            if basename.endswith(".lossy.id3"):
                # Don't try to match generated tag to original when stagger is 
                # explicitly expected to modify the tag.
                return


            # Scrub known invalid frames.
            # Stagger won't save these, so they would result in a tag mismatch below.
            for key in list(tag.keys()):
                if key.endswith(" "): # iTunes
                    del tag[key]
                if tag.version == 4 and key == "XSOP": # MusicBrainz
                    del tag[key]

            tag.padding_max = 0
            data = tag.encode()
            tag2 = stagger.decode_tag(data)
            tag.padding_max = 0
            data2 = tag.encode()

            self.assertEqual(data, data2, "data mismatch in file {0}".format(file))
            self.assertEqual(tag, tag2, "tag mismatch in file{0}".format(file))
    return test

class SamplesTestCase(unittest.TestCase):
    def tearDown(self):
        # Clean warning registries, allowing warnings to be recorded again.
        for module in stagger.tags, stagger.frames, stagger.id3, stagger.specs:
            if hasattr(module, "__warningregistry__"):
                del module.__warningregistry__

    def testID3v2ExtendedHeader(self):
        # First sample simply includes an empty extended header.
        tag1 = stagger.read_tag(os.path.join(sample_dir, 
                                             "23.synthetic.empty-extended-header.lossy.id3"))
        self.assertEqual(tag1.title, "The Millionaire's Holiday")
        self.assertEqual(tag1.album, "Best Of Combustible Edison")
        self.assertEqual(tag1.date, "1997")
        self.assertEqual(tag1.track, 1)
        self.assertEqual(tag1.genre, "Foobar")
        self.assertEqual(tag1.artist, "Combustible Edison")
        self.assertEqual(tag1.comment, " 0000132D 0000132D 00002FF0")
        self.assertEqual(tag1.flags, { "extended_header" })

        # Second sample file has an (invalid) CRC32 number in its extended header.
        tag2 = stagger.read_tag(os.path.join(sample_dir, 
                                             "23.synthetic.extended-header-bad-crc.lossy.id3"))
        self.assertEqual(tag2.title, "The Millionaire's Holiday")
        self.assertEqual(tag2.album, "Best Of Combustible Edison")
        self.assertEqual(tag2.date, "1997")
        self.assertEqual(tag2.track, 1)
        self.assertEqual(tag2.genre, "Foobar")
        self.assertEqual(tag2.artist, "Combustible Edison")
        self.assertEqual(tag2.comment, " 0000132D 0000132D 00002FF0")
        self.assertEqual(tag2.flags, { "ext:crc_present", "extended_header" })
        self.assertEqual(tag2.crc32, 0x20202020)

    def testIssue37(self):
        # Check that duplicate frames are handled OK.

        # The sample file contains two TALB frames ("quux" and "Foo").
        # This is invalid according to the spec.

        tag = stagger.read_tag(os.path.join(sample_dir, 
                                            "24.issue37.stagger.duplicate-talb.id3"))
        
        # The friendly API should just concatenate the frames, as if they were
        # a single multivalued text frame.
        self.assertEqual(tag.album, "quux / Foo")

        # Ditto for the magical dictionary API.
        self.assertEqual(tag[TALB], TALB(encoding=0, text=["quux", "Foo"]))

        # However, both getframes() and frames() should show two separate frames.
        self.assertEqual(tag.frames(TALB), [TALB(encoding=0, text="quux"), 
                                            TALB(encoding=0, text="Foo")])
        self.assertEqual(tag.frames(orig_order=True), 
                         [TIT2(encoding=0, text="Foobar"),
                          TALB(encoding=0, text="quux"),
                          TALB(encoding=0, text="Foo")])

sample_dir = os.path.join(os.path.dirname(__file__), "samples")

for file in list_id3(sample_dir):
    method = "test_" + os.path.basename(file).replace(".", "_")
    setattr(SamplesTestCase, method, generate_test(file))

suite = unittest.TestLoader().loadTestsFromTestCase(SamplesTestCase)

if __name__ == "__main__":
    warnings.simplefilter("always", stagger.Warning)
    unittest.main(defaultTest="suite")

