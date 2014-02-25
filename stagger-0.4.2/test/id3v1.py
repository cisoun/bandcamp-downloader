#!/usr/bin/env python3
#
# id3v1.py
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

######################################################################

# This test automatically downloads the ID3v1 test suite by Martin Nilsson,
# and runs stagger's id3v1 decoder on all 274 test cases, comparing
# decoded field values to expected values listed in the test suite's 
# generation.log file.
#
# Nilsson's tests are rather strict -- stagger intentionally accepts broken
# id3v1 tags, so it only complains on test case 3 (bad tag header).
#
# Test cases 7 and 8 (junk after string terminator) include NUL characters
# in field values in the log file, which is likely a mistake.  Their
# description prescribes that the NULs and the data after them should
# not show up for the user, so I override the test case's field values to check that.
#
# Test case 12 has leading spaces in the year field which are intentionally
# stripped by stagger.
#
# In two test cases, Nilsson uses genre names that differ from most other
# sources/implementations:
# 
#     Test case    Genre #   Genre in test    Genre elsewhere
#     151          136       Christian        Christian Gangsta Rap
#     155          140       Contemporary     Contemporary Christian
#
# Stagger follows the de facto ID3v1 standard and resolves 136 and 140 to
# the insane genres on the right.

import unittest
import os
import os.path
import re
import string
import urllib.request
import tarfile
import random
import io
import warnings

from stagger.errors import *
import stagger.id3v1

testsuite_url = r"http://www.id3.org/Developer_Information?action=AttachFile&do=get&target=id3v1_test_suite.tar.gz"
testsuite_file = os.path.join(os.path.dirname(__file__), "id3v1_test_suite.tar.gz")

testsuite_log = "id3v1/generation.log"

def download_testsuite():
    try:
        with open(testsuite_file, "rb") as file:
            pass
    except IOError:
        urllib.request.urlretrieve(testsuite_url, testsuite_file)
        
class ID3v1TestCase(unittest.TestCase):
    def parse_log(self):
        log = self.tar.extractfile(testsuite_log)
        try: 
            tests = []
            tag = {}
            for bline in log:
                line = bline.decode('iso-8859-1')
                m = re.match(r'^Test case ([0-9]+)$', line)
                if m is not None:
                    tag["id"] = int(m.group(1))
                    continue
                m = re.match(r'^Generated test file "([a-zA-Z0-9_.]+)"$', line)
                if m is not None:
                    tag["filename"] = m.group(1)
                    continue
                m = re.match(r'^([a-z]+) *: "([^"]*)"$', line)
                if m is not None:
                    tag[m.group(1)] = m.group(2)
                    continue
                m = re.match(r'^version: (1\.[01])$', line)
                if m is not None:
                    tag["version"] = m.group(1)
                    continue
                m = re.match(r'^genre  : ([0-9]+ \(.*\))$', line)
                if m is not None:
                    tag["genre"] = m.group(1)
                    continue
                m = re.match(r'^$', line)
                if m is not None and tag:
                    tests.append(tag)
                    tag = {}
            return tests
        finally:
            log.close()
    
    def setUp(self):
        download_testsuite()
        self.tar = tarfile.open(testsuite_file)

    def tearDown(self):
        self.tar.close()

    def testID3v1Conformance(self):
        for test in self.parse_log():
            # Fix expected values in test cases 7-8 (junk after string terminator).
            if test["id"] in [7, 8]:
                for field in ["title", "artist", "album", "comment"]:
                    test[field] = "12345"

            # Fix expected value in test case 12 (strip year field).
            if test["id"] == 12:
                test["year"] = test["year"].strip(string.whitespace)

            # Fix expected genre names in test cases 151 and 155 to de-facto standard values.
            if test["id"] == 151:
                test["genre"] = '136 (Christian Gangsta Rap)'
            if test["id"] == 155:
                test["genre"] = '140 (Contemporary Christian)'
            
            filename = 'id3v1/' + test["filename"]
            file = self.tar.extractfile(filename)
            try:
                # Test case 3 contains no valid ID3v1 tag.
                if test["id"] == 3:
                    self.assertRaises(NoTagError, stagger.id3v1.Tag1.read, file)
                    continue

                tag = stagger.id3v1.Tag1.read(file)
                for field in ["title", "artist", "album", 
                              "year", "comment", "track", "genre"]:
                    if field in test:
                        self.assertEqual(test[field], getattr(tag, field), 
                                         "Value mismatch in field " + field 
                                         + " of testcase " + str(test["id"]) 
                                         + ": '" + test[field] + "' vs '" 
                                         + getattr(tag, field) + "'")

                # Try encoding the tag and comparing binary data
                if test["id"] not in [7, 8, 12]:
                    data = tag.encode()
                    file.seek(-128, 2)
                    data2 = file.read(128)
                    self.assertEqual(data, data2, "Data mismatch in testcase " + str(test["id"]))
            finally:
                file.close()

suite = unittest.TestLoader().loadTestsFromTestCase(ID3v1TestCase)

if __name__ == "__main__":
    warnings.simplefilter("always", stagger.Warning)
    unittest.main(defaultTest="suite")


