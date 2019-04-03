from urllib import request
from shutil import copyfileobj
import io
import gzip
import tarfile
import zipfile


def download_file_as(url, file_name):
    with request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        copyfileobj(response, out_file)


def download_extract_targz(url):
    with request.urlopen(url) as response:
        compressed = io.BytesIO(response.read())
        with gzip.GzipFile(fileobj=compressed) as uncompressed:
            archive = tarfile.open(fileobj=uncompressed)
            archive.list()
            archive.extractall()

def download_extract_zip(url):
    with request.urlopen(url) as response:
        compressed = io.BytesIO(response.read())
        with zipfile.ZipFile(compressed) as zip:
            print(zip.namelist())
            zip.extractall()

if __name__ == '__main__':
    iscompressed = input('Compressed file? (Y/n): ')
    
    if iscompressed == 'Y':
        funcs = {
            'zip': download_extract_zip,
            'tar.gz': download_extract_targz,
        }
        chosen = input('zip or tar.gz? ')
        url = input('URL: ')
        funcs[chosen](url)
        
    url = input('URL: ')
    name = input('Save as: ')
    download_file_as(url, name)

