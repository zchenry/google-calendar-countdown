from os import path
from utils import *


def add_record():
    content = input('Event Content: ')
    date = input('Event Date: ')

    record = Record(content, date)
    row = record.create_event()

    mode = 'a' if path.exists(DATAFILE) else 'w'
    with open(DATAFILE, mode) as file:
        file.write(row)


if __name__ == '__main__':
    add_record()
