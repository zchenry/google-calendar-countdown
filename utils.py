import pickle
from datetime import date, datetime, timedelta
from os import path

import pandas as pd
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DATEFORMAT = '%Y-%m-%d'
TIMEZONE = 'Asia/Tokyo'
SCOPES = ['https://www.googleapis.com/auth/calendar']
PWD = path.dirname(path.abspath(__file__))
DATAFILE = path.join(PWD, 'data.csv')


def get_service():
    creds = None
    token_path = path.join(PWD, 'token.pickle')
    cred_path = path.join(PWD, 'credentials.json')

    if path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


class Record:
    service = get_service()
    cal_id = 'primary'
    color_id = '9'
    today = date.today()
    suffix = 'T00:00:00+09:00'
    today_time = str(today) + suffix
    tomorrow_time = str(today + timedelta(days=1)) + suffix
    time_zone = 'Asia/Tokyo'
    transparency = 'opaque'

    def __init__(self, content, date_str, if_loop=None, event_id=None):
        self.content = content
        self.date = self.strpdate(date_str)
        self.if_loop = if_loop
        self.event_id = event_id

    def to_csv(self):
        strs = [self.content, str(self.date), str(self.if_loop), self.event_id]
        return ','.join(strs) + '\n'

    def is_over(self):
        return (not self.if_loop) and (self.date <= self.today)

    def get_event(self):
        event = {'summary': self.get_summary(),
                 'colorId': self.color_id,
                 'start': {'date': None, 'dateTime': self.today_time,
                           'timeZone': self.time_zone},
                 'end': {'date': None, 'dateTime': self.tomorrow_time,
                         'timeZone': self.time_zone},
                 'transparency': self.transparency}
        return event

    def create_event(self):
        self.if_loop = self.date <= self.today
        insert_dict = {'calendarId': self.cal_id, 'body': self.get_event()}
        event = self.service.events().insert(**insert_dict).execute()
        self.event_id = event['id']
        return self.to_csv()

    def update_event(self):
        query_dict = {'calendarId': self.cal_id, 'eventId': self.event_id}
        event = self.service.events().get(**query_dict).execute()
        event.update(self.get_event())
        query_dict['body'] = event
        self.service.events().update(**query_dict).execute()
        return self.to_csv()

    def get_summary(self):
        if self.if_loop:
            days_passed = (self.today - self.date).days
            target_date = self.date.replace(year=self.today.year)
            if target_date <= self.today:
                target_date = self.date.replace(year=(self.today.year + 1))
            days_left = (target_date - self.today).days
            summary = '{}: {} days passed; {} days until {} anniv.'.format(
                self.content, days_passed, days_left,
                self.ordinal_expression(days_passed))
            return summary
        else:
            days_left = (self.date - self.today).days
            return '{}: {} days left'.format(self.content, days_left)

    def ordinal_expression(self, days):
        year = int(days / 365) + 1
        return str(year) + ['st', 'nd', 'rd', 'th'][min(year % 10 - 1, 3)]

    def strpdate(self, date_str=None):
        if date_str is None:
            return None
        else:
            return datetime.strptime(date_str, DATEFORMAT).date()


def load_data(file_path=DATAFILE):
    return pd.read_csv(file_path, header=None).to_numpy()
