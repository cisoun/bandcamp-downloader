#!/usr/bin/env python3
#
# friendly.py
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

class FriendlyTestCase(unittest.TestCase):
    def testTitle22(self):
        tag = stagger.Tag22()

        tag[TT2] = "Foobar"
        self.assertEqual(tag.title, "Foobar")

        tag[TT2] = ("Foo", "Bar")
        self.assertEqual(tag.title, "Foo / Bar")
        
        tag.title = "Baz"
        self.assertEqual(tag[TT2], TT2(text=["Baz"]))
        self.assertEqual(tag.title, "Baz")
        
        tag.title = "Quux / Xyzzy"
        self.assertEqual(tag[TT2], TT2(text=["Quux", "Xyzzy"]))
        self.assertEqual(tag.title, "Quux / Xyzzy")

    def testTitle(self):
        for tagcls in stagger.Tag23, stagger.Tag24:
            tag = tagcls()

            tag[TIT2] = "Foobar"
            self.assertEqual(tag.title, "Foobar")

            tag[TIT2] = ("Foo", "Bar")
            self.assertEqual(tag.title, "Foo / Bar")

            tag.title = "Baz"
            self.assertEqual(tag[TIT2], TIT2(text=["Baz"]))
            self.assertEqual(tag.title, "Baz")

            tag.title = "Quux / Xyzzy"
            self.assertEqual(tag[TIT2], TIT2(text=["Quux", "Xyzzy"]))
            self.assertEqual(tag.title, "Quux / Xyzzy")

    def testTextFrames(self):
        for tagcls in stagger.Tag22, stagger.Tag23, stagger.Tag24:
            tag = tagcls()

            for attr, frame in (("title", TIT2),
                                ("artist", TPE1),
                                ("album_artist", TPE2),
                                ("album", TALB),
                                ("composer", TCOM),
                                ("genre", TCON),
                                ("grouping", TIT1),
                                ("sort_title", TSOT),
                                ("sort_artist", TSOP),
                                ("sort_album_artist", TSO2),
                                ("sort_album", TSOA),
                                ("sort_composer", TSOC)):
                if tagcls == stagger.Tag22:
                    frame = frame._v2_frame

                # No frame -> empty string
                self.assertEqual(getattr(tag, attr), "")

                # Set by frameid, check via friendly name
                tag[frame] = "Foobar"
                self.assertEqual(getattr(tag, attr), "Foobar")

                tag[frame] = ("Foo", "Bar")
                self.assertEqual(getattr(tag, attr), "Foo / Bar")

                # Set by friendly name, check via frame id
                setattr(tag, attr, "Baz")
                self.assertEqual(getattr(tag, attr), "Baz")
                self.assertEqual(tag[frame], frame(text=["Baz"]))

                setattr(tag, attr, "Quux / Xyzzy")
                self.assertEqual(getattr(tag, attr), "Quux / Xyzzy")
                self.assertEqual(tag[frame], frame(text=["Quux", "Xyzzy"]))

                # Set to empty string, check frame is gone
                setattr(tag, attr, "")
                self.assertTrue(frame not in tag)

                # Repeat, should not throw KeyError
                setattr(tag, attr, "")
                self.assertTrue(frame not in tag)

    def testTrackFrames(self):
        for tagcls in stagger.Tag22, stagger.Tag23, stagger.Tag24:
            tag = tagcls()
            for track, total, frame in (("track", "track_total", TRCK),
                                        ("disc", "disc_total", TPOS)):
                if tagcls == stagger.Tag22:
                    frame = frame._v2_frame
                
                # No frame -> zero values
                self.assertEqual(getattr(tag, track), 0)
                self.assertEqual(getattr(tag, total), 0)

                # Set by frameid, check via friendly name
                tag[frame] = "12"
                self.assertEqual(getattr(tag, track), 12)
                self.assertEqual(getattr(tag, total), 0)
                
                tag[frame] = "12/24"
                self.assertEqual(getattr(tag, track), 12)
                self.assertEqual(getattr(tag, total), 24)

                tag[frame] = "Foobar"
                self.assertEqual(getattr(tag, track), 0)
                self.assertEqual(getattr(tag, total), 0)

                # Set by friendly name, check via frame id
                setattr(tag, track, 7)
                self.assertEqual(getattr(tag, track), 7)
                self.assertEqual(getattr(tag, total), 0)
                self.assertEqual(tag[frame], frame(text=["7"]))

                setattr(tag, total, 21)
                self.assertEqual(getattr(tag, track), 7)
                self.assertEqual(getattr(tag, total), 21)
                self.assertEqual(tag[frame], frame(text=["7/21"]))
                
                # Set to 0/0, check frame is gone
                setattr(tag, total, 0)
                self.assertEqual(getattr(tag, track), 7)
                self.assertEqual(getattr(tag, total), 0)
                self.assertEqual(tag[frame], frame(text=["7"]))
                
                setattr(tag, track, 0) 
                self.assertEqual(getattr(tag, track), 0)
                self.assertEqual(getattr(tag, total), 0)
                self.assertTrue(frame not in tag)
               
                # Repeat, should not throw
                setattr(tag, track, 0) 
                setattr(tag, total, 0)
                self.assertTrue(frame not in tag)
                
                # Set just the total
                setattr(tag, total, 13)
                self.assertEqual(tag[frame], frame(text=["0/13"]))

    def testDate22_23(self):
        for tagcls, yearframe, dateframe, timeframe in ((stagger.Tag22, TYE, TDA, TIM),
                                                        (stagger.Tag23, TYER, TDAT, TIME)):
            tag = tagcls()

            # Check empty
            self.assertEqual(tag.date, "")

            # Set to empty
            tag.date = ""
            self.assertEqual(tag.date, "")

            # Set a year
            tag.date = "2009"
            self.assertEqual(tag.date, "2009")
            tag.date = "   2009    "
            self.assertEqual(tag.date, "2009")
            self.assertEqual(tag[yearframe], yearframe("2009"))
            self.assertTrue(dateframe not in tag)
            self.assertTrue(timeframe not in tag)

            # Partial date
            tag.date = "2009-07"
            self.assertEqual(tag.date, "2009")
            self.assertEqual(tag[yearframe], yearframe("2009"))
            self.assertTrue(dateframe not in tag)
            self.assertTrue(timeframe not in tag)

            # Full date
            tag.date = "2009-07-12"
            self.assertEqual(tag.date, "2009-07-12")
            self.assertEqual(tag[yearframe], yearframe("2009"))
            self.assertEqual(tag[dateframe], dateframe("0712"))
            self.assertTrue(timeframe not in tag)

            # Date + time
            tag.date = "2009-07-12 18:01"
            self.assertEqual(tag.date, "2009-07-12 18:01")
            self.assertEqual(tag[yearframe], yearframe("2009"))
            self.assertEqual(tag[dateframe], dateframe("0712"))
            self.assertEqual(tag[timeframe], timeframe("1801"))
            
            tag.date = "2009-07-12 18:01:23"
            self.assertEqual(tag.date, "2009-07-12 18:01")
            self.assertEqual(tag[yearframe], yearframe("2009"))
            self.assertEqual(tag[dateframe], dateframe("0712"))
            self.assertEqual(tag[timeframe], timeframe("1801"))

            tag.date = "2009-07-12T18:01:23"
            self.assertEqual(tag.date, "2009-07-12 18:01")
            self.assertEqual(tag[yearframe], yearframe("2009"))
            self.assertEqual(tag[dateframe], dateframe("0712"))
            self.assertEqual(tag[timeframe], timeframe("1801"))

            # Truncate to year only
            tag.date = "2009"
            self.assertEqual(tag[yearframe], yearframe("2009"))
            self.assertTrue(dateframe not in tag)
            self.assertTrue(timeframe not in tag)
            
    def testDate24(self):
        tag = stagger.Tag24()
            
        # Check empty
        self.assertEqual(tag.date, "")

        # Set to empty
        tag.date = ""
        self.assertEqual(tag.date, "")

        # Set a year
        tag.date = "2009"
        self.assertEqual(tag.date, "2009")
        self.assertEqual(tag[TDRC], TDRC(tag.date))
        tag.date = "   2009    "
        self.assertEqual(tag.date, "2009")
        self.assertEqual(tag[TDRC], TDRC(tag.date))
        
        tag.date = "2009-07"
        self.assertEqual(tag.date, "2009-07")
        self.assertEqual(tag[TDRC], TDRC(tag.date))
        tag.date = "2009-07-12"
        self.assertEqual(tag.date, "2009-07-12")
        self.assertEqual(tag[TDRC], TDRC(tag.date))
        
        tag.date = "2009-07-12 18:01"
        self.assertEqual(tag.date, "2009-07-12 18:01")
        self.assertEqual(tag[TDRC], TDRC(tag.date))
        
        tag.date = "2009-07-12 18:01:23"
        self.assertEqual(tag.date, "2009-07-12 18:01:23")
        self.assertEqual(tag[TDRC], TDRC(tag.date))
            
        tag.date = "2009-07-12T18:01:23"
        self.assertEqual(tag.date, "2009-07-12 18:01:23")
        self.assertEqual(tag[TDRC], TDRC(tag.date))

    def testPicture22(self): 
        tag = stagger.Tag22()
            
        # Check empty
        self.assertEqual(tag.picture, "")

        # Set to empty
        tag.picture = ""
        self.assertEqual(tag.picture, "")
        self.assertTrue(PIC not in tag)

        tag.picture = os.path.join(os.path.dirname(__file__), "samples", "cover.jpg")
        self.assertEqual(tag[PIC][0].type, 0)
        self.assertEqual(tag[PIC][0].desc, "")
        self.assertEqual(tag[PIC][0].format, "JPG")
        self.assertEqual(len(tag[PIC][0].data), 60511)
        self.assertEqual(tag.picture, "Other(0)::<60511 bytes of jpeg data>")
       
        # Set to empty
        tag.picture = ""
        self.assertEqual(tag.picture, "")
        self.assertTrue(PIC not in tag)


    def testPicture23_24(self): 
        for tagcls in stagger.Tag23, stagger.Tag24:
            tag = tagcls()
            
            # Check empty
            self.assertEqual(tag.picture, "")

            # Set to empty
            tag.picture = ""
            self.assertEqual(tag.picture, "")
            self.assertTrue(APIC not in tag)

            # Set picture.
            tag.picture = os.path.join(os.path.dirname(__file__), "samples", "cover.jpg")
            self.assertEqual(tag[APIC][0].type, 0)
            self.assertEqual(tag[APIC][0].desc, "")
            self.assertEqual(tag[APIC][0].mime, "image/jpeg")
            self.assertEqual(len(tag[APIC][0].data), 60511)
            self.assertEqual(tag.picture, "Other(0)::<60511 bytes of jpeg data>")

            # Set to empty
            tag.picture = ""
            self.assertEqual(tag.picture, "")
            self.assertTrue(APIC not in tag)

    def testComment(self):
        for tagcls, frameid in ((stagger.Tag22, COM), 
                                (stagger.Tag23, COMM), 
                                (stagger.Tag24, COMM)):
            tag = tagcls()

            # Comment should be the empty string in an empty tag.
            self.assertEqual(tag.comment, "")

            # Try to delete non-existent comment.
            tag.comment = ""
            self.assertEqual(tag.comment, "")
            self.assertTrue(frameid not in tag)

            # Set comment.
            tag.comment = "Foobar"
            self.assertEqual(tag.comment, "Foobar")
            self.assertTrue(frameid in tag)
            self.assertEqual(len(tag[frameid]), 1)
            self.assertEqual(tag[frameid][0].lang, "eng")
            self.assertEqual(tag[frameid][0].desc, "")
            self.assertEqual(tag[frameid][0].text, "Foobar")
            
            # Override comment.
            tag.comment = "Baz"
            self.assertEqual(tag.comment, "Baz")
            self.assertTrue(frameid in tag)
            self.assertEqual(len(tag[frameid]), 1)
            self.assertEqual(tag[frameid][0].lang, "eng")
            self.assertEqual(tag[frameid][0].desc, "")
            self.assertEqual(tag[frameid][0].text, "Baz")

            # Delete comment.
            tag.comment = ""
            self.assertEqual(tag.comment, "")
            self.assertTrue(frameid not in tag)

    def testCommentWithExtraFrame(self):
        "Test getting/setting the comment when other comments are present."

        for tagcls, frameid in ((stagger.Tag22, COM), 
                                (stagger.Tag23, COMM), 
                                (stagger.Tag24, COMM)):
            tag = tagcls()
            frame = frameid(lan="eng", desc="foo", text="This is a text")
            tag[frameid] = [frame]

            # Comment should be the empty string.
            self.assertEqual(tag.comment, "")

            # Try to delete non-existent comment.
            tag.comment = ""
            self.assertEqual(tag.comment, "")
            self.assertEqual(len(tag[frameid]), 1)

            # Set comment.
            tag.comment = "Foobar"
            self.assertEqual(tag.comment, "Foobar")
            self.assertEqual(len(tag[frameid]), 2)
            self.assertEqual(tag[frameid][0], frame)
            self.assertEqual(tag[frameid][1].lang, "eng")
            self.assertEqual(tag[frameid][1].desc, "")
            self.assertEqual(tag[frameid][1].text, "Foobar")
            
            # Override comment.
            tag.comment = "Baz"
            self.assertEqual(tag.comment, "Baz")
            self.assertEqual(len(tag[frameid]), 2)
            self.assertEqual(tag[frameid][0], frame)
            self.assertEqual(tag[frameid][1].lang, "eng")
            self.assertEqual(tag[frameid][1].desc, "")
            self.assertEqual(tag[frameid][1].text, "Baz")

            # Delete comment.
            tag.comment = ""
            self.assertEqual(tag.comment, "")
            self.assertEqual(len(tag[frameid]), 1)
            self.assertEqual(tag[frameid][0], frame)

        
suite = unittest.TestLoader().loadTestsFromTestCase(FriendlyTestCase)

if __name__ == "__main__":
    warnings.simplefilter("always", stagger.Warning)
    unittest.main(defaultTest="suite")
