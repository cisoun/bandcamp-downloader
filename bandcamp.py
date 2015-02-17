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
#   * JamieMellway
#	* jtripper
#   * Stefan Haan


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


def main():
    printInfoMessage()
    checkArguments()

    print("Fetching page contents...")
    pageContent = loadPageContents()

    #get information about every track in the album and show a list to the user
    tracksInfo = getInfoFromPageContent(pageContent, "trackinfo", True)
    if tracksInfo == 0:
        print("[Error] No tracks found.")
        print("Aborting...")
        sys.exit(0)
    printTrackList(tracksInfo)

    #get tag infos
    artworkLargeFileName = downloadArtwork(pageContent)
    albumInfo = getAlbumInfo(pageContent)
    artistName = getArtistName(pageContent)
    releaseDateString = getReleaseDateString(albumInfo);

    isError = False
    for trackInfo in tracksInfo:
        trackFileName = getTrackFileName(trackInfo)
        progressMessage = "Track " + str(tracksInfo.index(trackInfo) + 1) + "/" + str(len(tracksInfo))
        try:
            isDownloaded = downloadFile(trackInfo["file"]["mp3-128"], trackFileName, progressMessage)
            if not isDownloaded:
                raise Exception
        except Exception:
            isError = True
            print(progressMessage + " : File unavailable. Skipping...")
            continue

        if canTag:
            trackNumber = 1
            if ("track_num" in trackInfo):
                trackNumber = trackInfo["track_num"]
            doTag(trackFileName,
                  albumInfo["title"],
                  artistName,
                  releaseDateString,
                  trackInfo["title"],
                  trackNumber,
                  artworkLargeFileName)

    if isError:
        printSorryMessage()

    print("\nAdding additional infos...")
    writeAlbumInformation(artistName, albumInfo, releaseDateString)
    print("\nFinished !\n")

# Download a file and show its progress.
# Taken from http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def downloadFile(sourceUrl, destPath, indicatorMessage):
    # Check if the file is available otherwise, skip.
    if not re.match("^https?://(\w+)\.(\w+)\.([\w\?\/\=\-\&\.])*$", str(sourceUrl)):
        return (False)

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
        status = progressBarString + (" " * spaceLength) + "[" + ("#" * progress) + (
        " " * (progressBarSize - progress)) + "]"
        status = status + chr(8) * (len(status))
        sys.stdout.write(status)
        sys.stdout.flush()
    file.close()
    print()
    return (True)


def getInfoFromPageContent(pageContent, property, bracket=False):
    try:
        if bracket:
            return json.loads("[{" + (re.findall(property + "[ ]?: \[?\{(.+)\}\]?,", pageContent, re.MULTILINE)[0] + "}]"))
        return (re.findall(property + "[ ]?: ([^,]+)", pageContent, re.DOTALL)[0])
    except:
        return (0)

def printInfoMessage():
    print("=" * 80)
    print("\n\tBandcamp MP3 Downloader " + VERSION)
    print("\t----")
    print("\tRemember, piracy isn't good for the artists,")
    print("\tuse this script carefully, buy their albums and support them !\n")
    print("=" * 80)
    print()


def checkArguments():
    # URL given ?
    if len(sys.argv) == 1:
        print("Please, add an url at the end of the command !")
        print("e.g: " + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah\n")
        sys.exit(0)

    # Valid URL ?
    if not re.match("^https?://(\w+)\.bandcamp\.com([-\w]|/)*$", sys.argv[1]):
        print("[Error] This url doesn't seem to be a valid Bandcamp url.")
        print("\nIt should look something like this :\n" + sys.argv[
            0] + " http://artist.bandcamp.com/album/blahblahblah\n")
        if input("Look for albums anyway ? [y/n] : ") != "y": sys.exit(0)
        print()


def loadPageContents():
    try:
        albumPage = urllib.request.urlopen(sys.argv[1])
        pageContent = albumPage.read().decode('utf-8')
        albumPage.close()
        return pageContent
    except:
        print("[Error] Can't reach the page.")
        print("Aborting...")
        sys.exit(0)


def getReleaseDateString(albumInfo):
    try:
        return datetime.strptime(albumInfo["release_date"], "%d %b %Y")
    except:
        return ""

def printTrackList(trackInfo):
    print("\nTracks found :\n----")
    for i in range(0, len(trackInfo)):
        # Track number available ?
        trackNumber = str(trackInfo[i]["track_num"]) + ". " if trackInfo[i]["track_num"] != None else ""
        print(trackNumber + str(trackInfo[i]["title"]))
    print()

def removeInvalidPathCharacters(str):
    return str.replace('"', '').replace('\\', '') #TODO: use built-in function if possible

def getFileName(url):
    return url.split('/')[-1] #TODO: use built-in function if possible

def downloadArtwork(pageContent):
    artworkUrl = removeInvalidPathCharacters(getInfoFromPageContent(pageContent, "artThumbURL"))
    artworkLargeUrl = removeInvalidPathCharacters(getInfoFromPageContent(pageContent, "artFullsizeUrl"))

    artworkFileName = getFileName(artworkUrl)
    artworkLargeFileName = getFileName(artworkLargeUrl)

    downloadFile(artworkUrl, artworkFileName, "Artwork")
    downloadFile(artworkLargeUrl, artworkLargeFileName, "Larger artwork")
    return artworkLargeFileName


def getTrackFileName(trackInfo):
    # Skip track number in file name if it's missing.
    if "track_num" in trackInfo:
        trackFileName = "%02d. %s.mp3" % (trackInfo["track_num"], removeInvalidPathCharacters(trackInfo["title"]).replace("/", ""))
    else:
        trackFileName = "%s.mp3" % removeInvalidPathCharacters(trackInfo["title"]).replace("/", "");
    return trackFileName


def addID3Header(trackFileName):
    # Try to add an empty ID3 header.
    # As long stagger crashes when there's no header, use this hack.
    # ID3v2 infos : http://id3.org/id3v2-00
    trackFile = open(trackFileName, 'r+b')
    oldContent = trackFile.read()
    trackFile.seek(0)
    trackFile.write(b"\x49\x44\x33\x02\x00\x00\x00\x00\x00\x00" + oldContent)  # Meh...
    trackFile.close()


def doTag(trackFileName, albumTitle="", artistName="", trackReleaseDate="", trackTitle="", trackNumber="",
          artworkFileName=""):
    try:
        stagger.read_tag(trackFileName)
    except:
        addID3Header(trackFileName)
    try:
        tags = stagger.read_tag(trackFileName)
        tags.album = albumTitle
        tags.artist = artistName
        tags.date = trackReleaseDate
        tags.title = trackTitle
        tags.track = trackNumber
        tags.picture = artworkFileName
        tags.write()
    except:
        print("[Warning] Can't add tags, skipped.")


def printSorryMessage():
    print()
    print(80 * "=")
    print("OOPS !")
    print("Looks like some tracks can't be downloaded.")
    print("Some albums don't allow you to listen to every track. Sorry :(")
    print(80 * "=")


def getAlbumInfo(pageContent):
    return getInfoFromPageContent(pageContent, "current", True)[0]


def getArtistName(pageContent):
    return getInfoFromPageContent(pageContent, "artist")


def writeAlbumInformation(artistName="", albumInfo={}, releaseDateString=""):
    infoFile = open("INFOS", "w+")
    infoFile.write("Artist : " + artistName)
    if "title" in albumInfo:
        infoFile.write("\nAlbum : " + albumInfo["title"])
    if releaseDateString:
        infoFile.write("\nRelease date : " + releaseDateString.strftime("%Y-%m-%d %H:%M:%S"))
    if "credits" in albumInfo:
        infoFile.write("\n\nCredits :\n----\n" + albumInfo["credits"])
    if "about" in albumInfo:
        infoFile.write("\n\nAbout :\n----\n" + albumInfo["about"])
    infoFile.close()

if __name__ == "__main__":
    main()