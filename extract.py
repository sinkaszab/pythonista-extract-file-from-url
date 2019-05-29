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
    EXTRACT_STARTED = 'EXTRACT_STARTED'


Message = namedtuple('Message', ['action', 'data'])


def _extract(url=None):
    yield Message(Actions.EXTRACT_STARTED, None)
    if not url:
        yield Message('URL_MISSING', None)
        yield Message('EXTRACT_FAILED', None)
        yield Message('EXTRACT_FINISHED', None)
        return
    yield Message('DOWNLOAD_STARTED', None)
    try:
        cached_file = download_file_to_memory(url)
        yield Message('DOWNLOAD_SUCCESS', None)
    except (ValueError, URLError):
        yield Message('DOWNLOAD_ABORTED', None)
    else:
        yield Message('TYPE_DETECTION_STARTED', None)
        suggested_type = search_compression_ext(url)
        if suggested_type:
            yield Message('TYPE_DETECTION_SUCCESS',
                          {'suggested_type': suggested_type})
            extract_suggested_type(suggested_type, cached_file)
            yield Message('EXTRACT_SUCCESS', None)
        else:
            yield Message('TYPE_DETECTION_FAILED', None)
            try:
                yield Message('SWITCH_TO_TRY_ALL_MODE', None)
                extract_with_try(cached_file)
            except (zipfile.BadZipFile, OSError):
                yield Message('EXTRACT_FAILED', None)
            else:
                yield Message('EXTRACT_SUCCESS', None)
    yield Message('EXTRACT_FINISHED', None)


def extract(url):
    if not url:
        print('No url provided.')
        return
    try:
        print('Start download & guess type.')
        cached_file = download_file_to_memory(url)
        suggested_type = search_compression_ext(url)
    except (ValueError, URLError):
        print('Process aborted: Invalid URL.')
    else:
        if suggested_type:
            print(f'Suggested type is: "{suggested_type}", process...')
            extract_suggested_type(suggested_type, cached_file)
            print('Successfully extracted.')
        else:
            print('Could not suggest type from URL.')
            try:
                print('Trying known formats.')
                extract_with_try(cached_file)
            except (zipfile.BadZipFile, OSError):
                print('Extract process failed.')
            else:
                print('Successfully extracted.')


if __name__ == '__main__':
    extract(input('Please provide a URL: '))

