import re
from urllib import request
from urllib.error import URLError
import io
from os.path import dirname, abspath, join
import gzip
import tarfile
import zipfile


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


# TODO:
# 1. Refactor extract to a generator or iterator.
# 2. Iterate business logic with next()
# 3. Yield messages.
# 4. UI logic to work as a reducer:
#    processes messages or runs side-effects.

# 
# OSError (gz)

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

