import pickle
import numpy as np
import pandas as pd
from os import path
from datetime import date, datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


DATEFORMAT = '%Y-%m-%d'
TIMEZONE = 'Asia/Tokyo'
SCOPES = ['https://www.googleapis.com/auth/calendar']
DATAFILE = 'data.csv'
PWD = path.dirname(path.abspath(__file__))


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
    today = date.today()


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


    def create_event(self):
        self.if_loop = self.date <= self.today
        event = { 'summary': self.get_summary(),
                  'colorId': '7',
                  'start': { 'date': str(self.today) },
                  'end': { 'date': str(self.today) } }
        insert_dict = { 'calendarId': self.cal_id, 'body': event }
        event = self.service.events().insert(**insert_dict).execute()
        self.event_id = event['id']
        return self.to_csv()


    def update_event(self):
        query_dict = { 'calendarId': self.cal_id, 'eventId': self.event_id }
        event = self.service.events().get(**query_dict).execute()
        event['summary'] = self.get_summary()
        event['start']['date'] = str(self.today)
        event['end']['date'] = str(self.today)
        query_dict['body'] = event
        self.service.events().update(**query_dict).execute()
        return self.to_csv()


    def get_summary(self):
        if self.if_loop:
            days_passed = (self.today - self.date).days
            target_date = self.date.replace(year=self.today.year)
            if target_date < self.today:
                target_date = self.date.replace(year=(self.today.year+1))
            days_left = (target_date - self.today).days
            summary = '{}: {} days passed; {} days until next anniv.'.format(
                self.content, days_passed, days_left)
            return summary
        else:
            days_left = (self.date - self.today).days
            return '{}: {} days left'.format(self.content, days_left)


    def strpdate(self, date_str=None):
        if date_str is None:
            return None
        else:
            return datetime.strptime(date_str, DATEFORMAT).date()



def load_data(file_name=DATAFILE):
    return pd.read_csv(path.join(PWD, file_name), header=None).to_numpy()
