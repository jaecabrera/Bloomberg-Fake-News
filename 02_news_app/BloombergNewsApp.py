# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Optional, List
import PySimpleGUI as sg
from newsapi import NewsApiClient
from pydantic import BaseModel
from newsapi.newsapi_exception import NewsAPIException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError


def get_news(source: str, **kwargs) -> List[dict]:
    """
    Returns a list of top headline news from the given source.
    
    :param source: The news source to get the headline.

    :**kwargs: Additional options that you can add
        for get_top_headlines function.

    :returns: A list of dictionary.
    """

    # NewsApiClient API Key
    api = NewsApiClient(api_key='cbcd311fe22e427e9207a7b95d1b34da')

    # Gather News
    news = api.get_everything(
        sources=source, **kwargs)

    # Select Articles
    articles = news['articles']

    return articles


@dataclass
class DataInsert:

    source: list
    result = None

    def insert_field(self, field: str, content: int):
        """
        :param field: Field to access in dictionary.
        :param content: Index location of the news content
            from list.
        :return: 
        """
        if field == 'publishedAt':
            date = self.source[content].get(field)
            self.result = date[:10]

        elif field == 'source':
            src = self.source[content].get(field)
            src = src['name']
            self.result = src

        else:
            self.result = self.source[content].get(field)

        return self.result 
    
    def __repr__(self):
        return f"""{self.source}"""


engine = create_engine('sqlite:///bloomberg_news.db')
Session = sessionmaker(engine)
Base = declarative_base()


# News SQL MetaData
class NewsModel(Base):
    __tablename__ = 'news'

    author = Column(String(100), nullable=True)
    content = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    publishedAt = Column(String(255), nullable=True)
    source = Column(String(200), nullable=True)
    title = Column(String(100), nullable=True)
    url = Column(String(255), nullable=False, primary_key=True)
    urlToImage = Column(String(100), nullable=True)


# News Base Model
class News(BaseModel):

    author: Optional[str]
    content: Optional[str]
    description: Optional[str]
    publishedAt: str
    source: str
    title: str
    url: str
    urlToImage: Optional[str]

    class Config:
        orm_mode = True


# create database
Base.metadata.create_all(engine)


#  Windows User Interface
sg.theme('DarkBlue15')
layout = [
    [sg.Image('Bloomberg_News_logo.png')],
    [sg.Text('Type any news topic:')],
    [sg.InputText(size=(25, 1), justification='left'), sg.Button('Get News')],
]

# Window Layout
window = sg.Window(
    'News Stream API - Pirple Project', layout,
    icon='app_ico.ico',
    size=(445, 330))


# SQLite Insert Function
def bulk_insert_news(max_entries) -> None:
    """
    :param max_entries: The number of entries to add in the
        sqlite database.
    :return: None
    """
    for entry in range(0, max_entries):
        news_data_fit = NewsModel(
            author=data.insert_field('author', entry),
            description=data.insert_field('description', entry),
            publishedAt=data.insert_field('publishedAt', entry),
            source=data.insert_field('source', entry),
            title=data.insert_field('title', entry),
            url=data.insert_field('url', entry),
            urlToImage=data.insert_field('urlToImage', entry))

        with engine.connect() as connection:
            with Session(bind=connection) as session:
                ic(session.add(news_data_fit))
                session.commit()
                session.close()

# Event, Values, Interaction Loop
while True:

    # Read events and values
    event, values = window.read()

    # GET NEWS Interaction
    if event == 'Get News':

        # News Subject / Topic
        if values is None:
            sg.popup_error("Input Topic")

        else:
            try:
                user_news = get_news(q=str(values), source='bloomberg')
                data = DataInsert(user_news)
                MAX_CONTENT = len(user_news)
                bulk_insert_news(MAX_CONTENT)
                sg.popup_auto_close(f'Data Inserted topic: {values}')
                break

            except TypeError:
                sg.popup_error("No News Found")
                continue

            except NewsAPIException:
                input_invalid = sg.popup_error("Please enter a topic for news")
                continue

            except IntegrityError:
                sg.popup_error("The news topic has duplicated articles please choose a different topic")

    if event == sg.WIN_CLOSED:
        break
