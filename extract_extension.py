import appex
import requests
from extract import extract

def main():
    if not appex.is_running_extension():
        print('Running in Pythonista app\n')
        url = input('Archive URL: ')
    else:
        url = appex.get_url()
    if url:
        print('Input URL: %s' % (url,))
        extract(url)
        print('Extraction was successful.')
    else:
        print('No input URL found.')

if __name__ == '__main__':
    main()
