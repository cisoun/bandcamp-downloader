"""Bandcamp-downloader."""

__version__ = '1.1.2'

import argparse
import html
import json
import os
import re
import requests
import sys

from collections import namedtuple


URL_PATTERN = r'^(?:https?://)?((?:[^./]+)\.bandcamp.com(?:/album(?:/[^\s/]+)?)?)/?$'

Album = namedtuple('Album', 'artist title cover release_date tracks')
Track = namedtuple('Track', 'number title url duration unreleased')


def decode(content):
    """Decode the content of a Bandcamp page.

    Args:
        content (str): HTML content.

    """
    # Search the cover.
    matches = re.search('<a class="popupImage" href="([^\"]*)', content)
    cover   = matches.group(1)

    # Search album data.
    matches = re.search('data-tralbum=\"([^\"]*)\"', content)

    if not matches:
        sys.exit('error: could not find any tracks.')

    # Get album data.
    data = matches.group(1)
    # Decode HTML.
    data = html.unescape(data)
    # Decode to JSON.
    data = json.loads(data)

    tracks = (
        Track(
            number     = track['track_num'],
            title      = track['title'],
            url        = track.get('file', {}).get('mp3-128'),
            duration   = track['duration'],
            unreleased = track['unreleased_track']
        ) for track in data['trackinfo']
    )

    album = Album(
        artist       = data['artist'],
        title        = data['current']['title'],
        cover        = cover,
        release_date = data['current']['release_date'],
        tracks       = tuple(tracks)
    )

    return album


def download(album, destination, cover=True):
    """Download an album.

    Args:
        album (Album):     Album data.
        destination (str): Destination of the files.
        cover (bool):      Allow cover downloading (default: True).

    """
    # Create folder.
    os.makedirs(destination, exist_ok=True)

    print('Downloading album into %s' % destination)

    # Notify for unreleased tracks.
    if (any((track.unreleased for track in album.tracks))):
        print('\nWARNING: some tracks are not released yet! '
              'I will ignore them.\n')

    # Download tracks.
    for track in album.tracks:
        if track.unreleased:
            continue
        title = re.sub(r'[\:\/\\]', '', track.title)  # Strip unwanted chars.
        file  = '%s. %s.mp3' % (track.number, title)
        path  = os.path.join(destination, file)
        download_file(track.url, path, file)

    # Download album cover.
    if cover:
        path = os.path.join(destination, 'cover.jpg')
        download_file(album.cover, path, 'Album cover')


def download_file(url, target, name):
    """Download a file.

    Adapted from https://stackoverflow.com/q/15644964/9322103.

    Args:
        url (str):    URL of the file.
        target (str): Target path.
        name (str):   Title of the download.

    """
    with open(target, 'wb') as f:
        response = requests.get(url, stream=True)
        size     = response.headers.get('content-length')

        if size is None:
            print('%s (unavailable)' % name)
            return

        downloaded = 0
        size = int(size)
        for data in response.iter_content(chunk_size=4096):
            downloaded += len(data)
            f.write(data)
            progress = int(20 * downloaded / size)
            sys.stdout.write(
                '\r[%s%s] %s' % ('#' * progress, ' ' * (20 - progress), name))
            sys.stdout.flush()
        sys.stdout.write('\n')


def validate_url(url):
    matches = re.search(URL_PATTERN, url)
    return 'https://' + matches.group(0)


def parse():
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description='Download an album from a Bandcamp page URL.')
    parser.add_argument('url', type=str, help='URL of the page')
    parser.add_argument(
        '-d', '--destination',
        default=os.getcwd(),
        dest='destination',
        help='destination of the files (current folder by default)')
    parser.add_argument(
        '-c', '--no-cover',
        action='store_false',
        dest='cover',
        help='ignore album cover')
    return parser.parse_args()


def main():
    """Run the main routine."""
    args = parse()

    try:
        url   = validate_url(args.url)
        page  = requests.get(url)
        album = decode(page.text)
        download(album, destination=args.destination, cover=args.cover)
    except Exception as e:
        sys.exit('error: could not parse this page.')

main()
