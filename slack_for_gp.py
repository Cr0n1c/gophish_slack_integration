import slack

from json import loads
from time import sleep
from pprint import pformat

from sqlalchemy import Column, create_engine, desc
from sqlalchemy import BigInteger, DateTime, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# HARD CODED VARIABLES
SLEEP_CYCLE_IN_SECS = 1
RETRY_ATTEMPT_IN_SECS = 5
SQLITE_PATH = "/root/go/src/github.com/gophish/gophish/gophish.db"

SLACK_API_TOKEN = "xoxp-1111111111-111111111-111111111-111111111111111111111"
SLACK_CHANNEL = "#your_channel"

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(BigInteger)
    email = Column(String)
    time = Column(DateTime)
    message = Column(String)
    details = Column(Text)

    def __repr__(self):
        return '<Event %r>' % self.id

def send_to_slack(row):
    if row.message in ["Clicked Link", "Submitted Data"]:
        client = slack.WebClient(token=SLACK_API_TOKEN)

        slack_message = f"`{row.time}`: New `{row.message}` hit from GoPhish for campaign_id `{row.campaign_id}`\n"
        slack_message += f"```\n{pformat(loads(row.details))}```\n"

        while True:
            try:
                response = client.chat_postMessage(
                    channel=SLACK_CHANNEL,
                    text=slack_message
                )
            except slack.errors.SlackApiError:
                sleep(RETRY_ATTEMPT_IN_SECS)
            else:
                break

if __name__ == "__main__":
    engine = create_engine(f"sqlite:///{SQLITE_PATH}")
    session = sessionmaker()
    session.configure(bind=engine)
    Base.metadata.create_all(engine)
    s = session()

    try:
        most_recent_event_id = s.query(Event.id).order_by(desc(Event.id)).first()[0]
    except IndexError:
        most_recent_event_id = 0

    while True:
        results = s.query(Event).filter(Event.id > most_recent_event_id)
        if results.count() > 0:
            for row in results:
                send_to_slack(row)
                most_recent_event_id = row.id

        sleep(SLEEP_CYCLE_IN_SECS)
