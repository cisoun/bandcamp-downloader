#!/usr/bin/python

# Bandcamp Mp3 Downloader 0.1.4
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


VERSION = "0.1.4"


import sys
import urllib.request
import re
import json
from datetime import datetime, date, time
try:
	import stagger
	from stagger.id3 import *
	can_tag = True
except:
	print("[Error] Can't import stagger, will skip mp3 tagging.")
	can_tag = False


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
		t = message + " (" + "{:d}".format(int(file_size / 1024)) + " ko) : "
		status =  t + (" " * int(48 - len(t))) + "[" + ("#" * int(file_size_dl * 30 / file_size)) + (" " * int(30 - (file_size_dl * 30 / file_size))) + "]"
		status = status + chr(8) * (len(status) + 1)
		sys.stdout.write(status)
		sys.stdout.flush()
	f.close()
	print()

# Return some JSON things...
def GetDataFromProperty(p, bracket = False):
	try:
		if bracket:
			return(json.loads("[{" + (re.findall(p + "[ ]?: \[?\{(.+)\}\]?,", s, re.MULTILINE)[0] + "}]")))
		return(re.findall(p + "[ ]?: ([^,]+)", s, re.DOTALL)[0])
	except:
		return(0)

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
		print("e.g: " + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah\n")
		sys.exit(0)

	# Valid URL ?
	if not re.match("^http://(\w+)\.bandcamp\.com([-\w]|/)*$", sys.argv[1]):
		print("[Error] This url doesn't seems to be a valid bandcamp url.")
		print("\nIt should be something like this :\n" + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah\n")
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
		f.close()
	except:
		print("[Error] Can't reach the page.")
		print("Aborting...")
		sys.exit(0)

	# We only load the essential datas.
	album = GetDataFromProperty("current", True)[0]
	artist = GetDataFromProperty("artist").replace('"', '').replace('\\', '')
	artwork = GetDataFromProperty("artThumbURL").replace('"', '').replace('\\', '')
	artwork_full = GetDataFromProperty("artFullsizeUrl").replace('"', '').replace('\\', '')
	tracks = GetDataFromProperty("trackinfo", True)
	if album == 0 : print("[Warning] Album informations not found.")
	if artist == 0 : print("[Warning] Artist informations not found.")
	if artwork == 0  : print("[Warning] Cover not found.")
	if artwork_full == 0  : print("[Warning] Full size cover not found.")
	try:
		release_date = datetime.strptime(album["release_date"], "%d %b %Y %H:%M:%S GMT")
	except:
		print("[Warning] Cannot find release date.")
	if tracks == 0 :
		print("[Error] Tracks not found. This is unecessary to continue.")
		print("Aborting...")
		sys.exit(0)


#===============================================================================
#
#	3. Download & tag.
#
#===============================================================================

	
	# List the tracks.
	print("\nTracks found :\n----")
	for i in range(0, len(tracks)):
		print(str(tracks[i]["track_num"]) + ". " + str(tracks[i]["title"]))
	exit
	# Artwork.
	print()
	artwork_name = artwork.split('/')[-1]
	artwork_full_name = artwork_full.split('/')[-1]
	Download(artwork, artwork_name, "Cover")
	Download(artwork_full, artwork_full_name, "Fullsize cover")

	# Tracks.
	print()
	for track in tracks:
		f = "%02d. %s.mp3" % (track["track_num"], track["title"])
		Download(track["file"], f, "Track " + str(track["track_num"]) + "/" + str(len(tracks)))
		# Tag.
		if can_tag == False : continue # Skip the tagging operation if stagger cannot be loaded.
		# Try to load the mp3 in stagger.
		try:
			t = stagger.read_tag(f)
		except:
			# Try to add an empty ID3 header.
			# As long stagger crashes when there's no header, use this hack.
			# ID3v2 infos : http://id3.org/id3v2-00
			m = open(f, 'r+b')
			old = m.read()
			m.seek(0)
			m.write(b"\x49\x44\x33\x02\x00\x00\x00\x00\x00\x00" + old) # Meh...
			m.close
		# Let's try again...
		try:
			t = stagger.read_tag(f)
			t.album = album["title"]
			t.artist = artist
			t.date = release_date.strftime("%Y-%m-%d %H:%M:%S")
			t.title = track["title"]
			t.track = track["track_num"]
			t.picture = artwork_full_name
			t.write()
		except:
			print("[Warning] Can't add tags, skipped.")


#===============================================================================
#
#	4. Add album's informations.
#
#===============================================================================

	
	print("\nAdding additional infos...")
	f = open("INFOS", "w+")
	f.write("Artist : " + artist)
	if album["title"] != None : f.write("\nAlbum : " + album["title"])
	if release_date != None : f.write("\nRelease date : " + release_date.strftime("%Y-%m-%d %H:%M:%S"))
	if album["credits"] != None : f.write("\n\nCredits :\n----\n" + album["credits"])
	if album["about"] != None : f.write("\n\nAbout :\n----\n" + album["about"])
	f.close()

	# Done.
	print("\nFinished !\n")
