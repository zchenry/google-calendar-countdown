from utils import *


def update_records():
    csv_content = ''

    for row in load_data():
        record = Record(row[0], row[1], row[2], row[3])
        if not record.is_over():
            csv_content += record.update_event()

    with open(path.join(PWD, DATAFILE), 'w') as file:
        file.write(csv_content)


if __name__ == '__main__':
    update_records()
