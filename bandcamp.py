#!/usr/bin/python

# Bandcamp MP3 Downloader
# Copyright (c) 2012-2014 cisoun
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
#
# Contributors:
#	JamieMellway
#	jtripper


VERSION = "0.1.12-1"


import sys
import urllib.request
import re
import json
import math
from datetime import datetime, date, time
try:
	import stagger
	from stagger.id3 import *
	canTag = True
except:
	print("[Error] Can't import stagger, will skip mp3 tagging.")
	canTag = False

# Download a file and show its progress.
# Taken from http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def download(sourceUrl, destPath, indicatorMessage):
	# Check if the file is available otherwise, skip.
	if not re.match("^https?://(\w+)\.(\w+)\.([\w\?\/\=\-\&\.])*$", str(sourceUrl)):
		return(False)
	# Let's do this !
	httpResponse = urllib.request.urlopen(sourceUrl)
	file = open(destPath, "wb")
	meta = httpResponse.info()
	totalFileSize = int(meta["Content-Length"])
	downloadedSize = 0
	blockSize = 8192
	progressBarString = indicatorMessage + " (" + "{:d}".format(int(totalFileSize / 1024)) + " ko) : "
	progressBarSize = 25
	spaceLength = 80 - progressBarSize - len(progressBarString) - 2
	while True:
		buffer = httpResponse.read(blockSize)
		if not buffer:
			break
		downloadedSize += len(buffer)
		file.write(buffer)
		progress = math.ceil(downloadedSize * progressBarSize / totalFileSize)
		status =  progressBarString + (" " * spaceLength) + "[" + ("#" * progress) + (" " * (progressBarSize - progress)) + "]"
		status = status + chr(8) * (len(status))
		sys.stdout.write(status)
		sys.stdout.flush()
	file.close()
	print()
	return(True)

# Return some JSON things...
def getDataFromProperty(property, bracket = False):
	try:
		if bracket:
			return(json.loads("[{" + (re.findall(property + "[ ]?: \[?\{(.+)\}\]?,", pageContent, re.MULTILINE)[0] + "}]")))
		return(re.findall(property + "[ ]?: ([^,]+)", pageContent, re.DOTALL)[0])
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
	print("\n\tBandcamp MP3 Downloader " + VERSION)
	print("\t----")
	print("\tRemember, piracy isn't good for the artists,")
	print("\tuse this script carefully, buy their albums and support them !\n")
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
	if not re.match("^https?://(\w+)\.bandcamp\.com([-\w]|/)*$", sys.argv[1]):
		print("[Error] This url doesn't seem to be a valid Bandcamp url.")
		print("\nIt should look something like this :\n" + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah\n")
		if input("Look for albums anyway ? [y/n] : ") != "y": sys.exit(0)
		print()


#===============================================================================
#
#	2. Find some informations.
#
#===============================================================================


	# Load the web page content.
	try:
		albumPage = urllib.request.urlopen(sys.argv[1])
		pageContent = albumPage.read().decode('utf-8')
		albumPage.close()
	except:
		print("[Error] Can't reach the page.")
		print("Aborting...")
		sys.exit(0)

	# We only load the essential datas.
	tracks = getDataFromProperty("trackinfo", True)
	if tracks == 0 :
		print("[Error] No tracks found.")
		print("Aborting...")
		sys.exit(0)
	album = getDataFromProperty("current", True)[0]
	artist = getDataFromProperty("artist").replace('"', '').replace('\\', '')
	artworkUrl = getDataFromProperty("artThumbURL").replace('"', '').replace('\\', '')
	artworkLargeUrl = getDataFromProperty("artFullsizeUrl").replace('"', '').replace('\\', '')
	if album == 0 : print("[Warning] Album information not found.")
	if artist == 0 : print("[Warning] Artist information not found.")
	if artworkUrl == 0  : print("[Warning] Cover not found.")
	if artworkLargeUrl == 0  : print("[Warning] Full size cover not found.")
	try:
		release_date = datetime.strptime(album["release_date"], "%d %b %Y %H:%M:%S GMT")
	except:
		print("[Warning] Cannot find release date.")


#===============================================================================
#
#	3. Download tracks & tag.
#
#===============================================================================

	
	# List the tracks.
	print("\nTracks found :\n----")
	for i in range(0, len(tracks)):
		# Track number available ?
		trackNumber = str(tracks[i]["track_num"]) + ". " if tracks[i]["track_num"] != None else ""
		print(trackNumber + str(tracks[i]["title"]))
	exit
	# Artwork.
	print()
	artworkName = artworkUrl.split('/')[-1]
	artworkLargeName = artworkLargeUrl.split('/')[-1]
	download(artworkUrl, artworkName, "Cover")
	download(artworkLargeUrl, artworkLargeName, "Fullsize cover")

	# Tracks.
	print()
	isError = False
	for track in tracks:
		# Skip track number if missing.
		if track["track_num"] != None:
			albumPage = "%02d. %s.mp3" % (track["track_num"], track["title"].replace("\\", "").replace("/", ""))
		else:
			albumPage = "%s.mp3" % track["title"].replace("\\", "").replace("/", "")
		# Skip if file unavailable. Can happens with some albums.
		message = "Track " + str(tracks.index(track) + 1) + "/" + str(len(tracks))
		try:
			isDownloaded = download(track["file"]["mp3-128"], albumPage, message)
			if not isDownloaded:
				raise Exception
		except Exception:
			isError = True
			print(message + " : File unavailable. Skipping...")
			continue

		# Tag.
		if canTag == False : continue # Skip the tagging operation if stagger cannot be loaded.
		# Try to load the mp3 in stagger.
		try:
			t = stagger.read_tag(albumPage)
		except:
			# Try to add an empty ID3 header.
			# As long stagger crashes when there's no header, use this hack.
			# ID3v2 infos : http://id3.org/id3v2-00
			trackFile = open(albumPage, 'r+b')
			oldContent = trackFile.read()
			trackFile.seek(0)
			trackFile.write(b"\x49\x44\x33\x02\x00\x00\x00\x00\x00\x00" + oldContent) # Meh...
			trackFile.close()
		# Let's try again...
		try:
			t = stagger.read_tag(albumPage)
			t.album = album["title"]
			t.artist = artist
			if release_date.strftime("%H:%M:%S") == "00:00:00":
				t.date = release_date.strftime("%Y-%m-%d")
			else:
				t.date = release_date.strftime("%Y-%m-%d %H:%M:%S")
			t.title = track["title"]
			t.track = track["track_num"]
			t.picture = artworkLargeName
			t.write()
		except:
			print("[Warning] Can't add tags, skipped.")
	if isError:
		print()
		print(80 * "=")
		print("OOPS !")
		print("Looks like some tracks can't be downloaded.")
		print("Some albums don't allow you to listen to every track. Sorry :(")
		print(80 * "=")


#===============================================================================
#
#	4. Add album's informations.
#
#===============================================================================

	
	print("\nAdding additional infos...")
	albumPage = open("INFOS", "w+")
	albumPage.write("Artist : " + artist)
	if album["title"] != None : albumPage.write("\nAlbum : " + album["title"])
	if release_date != None : albumPage.write("\nRelease date : " + release_date.strftime("%Y-%m-%d %H:%M:%S"))
	if album["credits"] != None : albumPage.write("\n\nCredits :\n----\n" + album["credits"])
	if album["about"] != None : albumPage.write("\n\nAbout :\n----\n" + album["about"])
	albumPage.close()

	# Done.
	print("\nFinished !\n")
