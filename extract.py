import re
from urllib import request
from urllib.error import URLError
import io
from os.path import dirname, abspath, join
import gzip
import tarfile
import zipfile
from collections import namedtuple


def download_file_to_memory(url):
    with request.urlopen(url) as response:
        return io.BytesIO(response.read())


def search_compression_ext(path):
    regex = r'(\.tar\.gz|\.zip)$'
    pattern = re.compile(regex)
    result = pattern.search(path)
    if result:
        return result.group()


def extract_all(packed_format):
    base = abspath(dirname(__file__))
    downloads = join(base, 'downloads')
    packed_format.extractall(path=downloads)


def extract_tar_gz(byte_obj):
    with gzip.GzipFile(fileobj=byte_obj) as uncompressed:
        tar = tarfile.open(fileobj=uncompressed)
        extract_all(tar)


def extract_zip(byte_obj):
    with zipfile.ZipFile(byte_obj) as zip:
        extract_all(zip)


def extract_suggested_type(type_, byte_obj):
    rails = {
        '.zip': extract_zip,
        '.tar.gz': extract_tar_gz,
    }
    rails[type_](byte_obj)


def extract_with_try(byte_obj):
    if zipfile.is_zipfile(byte_obj):
        extract_zip(byte_obj)
        return
    extract_tar_gz(byte_obj)


class Actions:
    URL_MISSING = 'URL_MISSING'
    EXTRACT_STARTED = 'EXTRACT_STARTED'
    EXTRACT_FAILED = 'EXTRACT_FAILED'
    EXTRACT_SUCCESS = 'EXTRACT_SUCCESS'
    EXTRACT_FINISHED = 'EXTRACT_FINISHED'
    DOWNLOAD_STARTED = 'DOWNLOAD_STARTED'
    DOWNLOAD_SUCCESS = 'DOWNLOAD_SUCCESS'
    DOWNLOAD_ABORTED = 'DOWNLOAD_ABORTED'
    TYPE_DETECTION_STARTED = 'TYPE_DETECTION_STARTED'
    TYPE_DETECTION_FAILED = 'TYPE_DETECTION_FAILED'
    TYPE_DETECTION_SUCCESS = 'TYPE_DETECTION_SUCCESS'
    SWITCH_TO_TRY_ALL_MODE = 'SWITCH_TO_TRY_ALL_MODE'


readables = {
    Actions.URL_MISSING: 'You didn\'t provide a URL.',
    Actions.EXTRACT_STARTED: 'Extract process started.',
    Actions.EXTRACT_FAILED: 'Extract process failed.',
    Actions.EXTRACT_SUCCESS: 'Extract process success.',
    Actions.EXTRACT_FINISHED: 'Extract process finished.',
    Actions.DOWNLOAD_STARTED: 'Downloading file...',
    Actions.DOWNLOAD_SUCCESS: 'Downloaded.',
    Actions.DOWNLOAD_ABORTED: 'Download aborted...',
    Actions.TYPE_DETECTION_STARTED: 'Detecting type...',
    Actions.TYPE_DETECTION_FAILED: 'Couldn\'t identify compression type.',
    Actions.TYPE_DETECTION_SUCCESS: 'Compression detected',
    Actions.SWITCH_TO_TRY_ALL_MODE:
    'Type detection switches to try all modes.',
}

Message = namedtuple('Message', ['action', 'data'])


def _extract(url=None):
    yield Message(Actions.EXTRACT_STARTED, None)
    if not url:
        yield Message(Actions.URL_MISSING, None)
        yield Message(Actions.EXTRACT_FAILED, None)
        yield Message(Actions.EXTRACT_FINISHED, None)
        return
    yield Message(Actions.DOWNLOAD_STARTED, None)
    try:
        cached_file = download_file_to_memory(url)
        yield Message(Actions.DOWNLOAD_SUCCESS, None)
    except (ValueError, URLError):
        yield Message(Actions.DOWNLOAD_ABORTED, None)
    else:
        yield Message(Actions.TYPE_DETECTION_STARTED, None)
        suggested_type = search_compression_ext(url)
        if suggested_type:
            yield Message(Actions.TYPE_DETECTION_SUCCESS,
                          {'suggested_type': suggested_type})
            extract_suggested_type(suggested_type, cached_file)
            yield Message(Actions.EXTRACT_SUCCESS, None)
        else:
            yield Message(Actions.TYPE_DETECTION_FAILED, None)
            try:
                yield Message(Actions.SWITCH_TO_TRY_ALL_MODE, None)
                extract_with_try(cached_file)
            except (zipfile.BadZipFile, OSError):
                yield Message(Actions.EXTRACT_FAILED, None)
            else:
                yield Message(Actions.EXTRACT_SUCCESS, None)
    yield Message(Actions.EXTRACT_FINISHED, None)


def extract():
    for message in _extract(input('Please provide a URL: ')):
        if message.action == Actions.TYPE_DETECTION_SUCCESS:
            print(
                f"{readables.get(message.action, message.action)}: {message.data['suggested_type']}"
            )
        else:
            print(readables.get(message.action, message.action))


if __name__ == '__main__':
    extract()

