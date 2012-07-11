#!/usr/bin/python

# Bandcamp Mp3 Downloader 0.1.1
# Copyright (c) 2012 cisoun, Cyriaque Skrapits <cysoun[at]gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


VERSION = "0.1.1"


import sys
import urllib.request
import re
import json
try:
	import stagger
	from stagger.id3 import *
except:
	print("Error : can't import stagger, will skip mp3 tagging.")


# Download a file and show its progress.
# Taken from http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def Download(url, out, message):
	u = urllib.request.urlopen(url)
	f = open(out, "wb")
	meta = u.info()

	file_size = int(meta["Content-Length"])
	
	file_size_dl = 0
	block_sz = 8192
	while True:
		buffer = u.read(block_sz)
		if not buffer:
			break
		file_size_dl += len(buffer)
		f.write(buffer)
		#status = "%d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
		#status = "[" + ("=" * int(file_size_dl * 78. / file_size)) + (" " * int(78 - (file_size_dl * 78. / file_size))) + "]"
		t = message + " (" + "{:d}".format(int(file_size / 1024)) + " ko) : "
		status =  t + (" " * int(58 - len(t))) + "[" + ("#" * int(file_size_dl * 20. / file_size)) + (" " * int(20 - (file_size_dl * 20. / file_size))) + "]"
		status = status + chr(8) * (len(status) + 1)
		sys.stdout.write(status)
		sys.stdout.flush()
	f.close()
	print()

# Return some JSON things...
def GetDataFromPropertie(p, bracket = False):
	if bracket:
		return(json.loads("[{" + (re.findall( p + "[ ]?: \[?\{(.+)\}\]?,", s, re.MULTILINE)[0] + "}]")))
		#return(json.loads("[{" + (re.findall(p + "[ ]?: \[?\{([^\}\]?]+)", s, re.DOTALL)[0] + "}]")))
	return(re.findall(p + "[ ]?: ([^,]+)", s, re.DOTALL)[0])

def LoadBinaryFile(f):
	t = open(f, "rb")
	d = t.read()
	t.close()
	return d

# Print a JSON data.
def PrintData(d):
	print(json.dumps(d, sort_keys = True, indent = 2))


if __name__ == "__main__":
#===============================================================================
#
#	0. Welcome.
#
#===============================================================================


	print("=" * 80)
	print("\n\tBandcamp Mp3 Downloader " + VERSION)
	print("\t----")
	print("\tRemember, piracy isn't good for the artists,")
	print("\tuse this script carefuly, buy their albums and support them !\n")
	print("=" * 80)
	print()


#===============================================================================
#
#	1. Let's get the bandcamp url in the parameters.
#
#===============================================================================


	# URL given ?
	if len(sys.argv) == 1:
		print("Please, add an url at the end of the command !")
		print("eg: " + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah")
		sys.exit(0)

	# Valid URL ?
	if not re.match("^http://(\w+)\.bandcamp\.com([-\w]|/)*$", sys.argv[1]):
		print("This url doesn't seems to be a valid bandcamp url.")
		sys.exit(0)


#===============================================================================
#
#	2. Find some informations.
#
#===============================================================================


	# Load the code.
	try:
		f = urllib.request.urlopen(sys.argv[1])
		s = f.read().decode('utf-8')
	except:
		print("[Error] Can't reach the page.")
		print("Aborting...")
		sys.exit(0)

	# We only load the essential datas.
	try:
		album = GetDataFromPropertie("current", True)[0]
		artwork = GetDataFromPropertie("artThumbURL").replace('"', '').replace('\\', '')
		artwork_full = GetDataFromPropertie("artFullsizeUrl").replace('"', '').replace('\\', '')
		tracks = GetDataFromPropertie("trackinfo", True)
	except:
		print("[Error] Can't find album's datas.")
		print("Aborting...")
		sys.exit(0)

	f.close()


#===============================================================================
#
#	3. Download & tag.
#
#===============================================================================

	
	# List the tracks.
	print("Tracks found :\n----")
	for i in range(0, len(tracks) - 1):
		print(str(tracks[i]["track_num"]) + ". " + str(tracks[i]["title"]))

	# Artwork.
	print()
	artwork_name = artwork.split('/')[-1]
	artwork_full_name = artwork_full.split('/')[-1]
	Download(artwork, artwork_name, "Cover")
	Download(artwork_full, artwork_full_name, "Fullsize cover")

	# Tracks.
	print()
	for track in tracks:
		f = "%s. %s.mp3" % (track["track_num"], track["title"])
		Download(track["file"], f, "Track " + str(track["track_num"]) + "/" + str(len(tracks)))
		# Tag.
		try:
			t = stagger.read_tag(f)
			t.album = album["title"]
			t.artist = album["artist"]
			t.date = album["release_date"]
			t.track = track["track_num"]
			t.picture = LoadBinaryFile(artwork_full_name)
			t.write()
		except:
			print("[Warning] Can't add tags, skipped.")

	
	print("\nFinished !\n")
