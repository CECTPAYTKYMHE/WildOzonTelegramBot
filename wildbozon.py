import re
from webbrowser import get
import requests
from bs4 import BeautifulSoup as BS
import csv
import time
import json
from urllib.parse import urlparse
import ast

from urllib3 import Retry
wildberries = 'www.wildberries.ru'
ozon = 'www.ozon.ru'

HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56',
}
def get_page_url(url,params=''):
        r = requests.get(url, headers=HEADERS, params=params, timeout=40)
        return r

def get_content(url):
        soup = BS(get_page_url(url).text, 'html.parser')
        cards = []
        if urlparse(url).netloc == wildberries:
                try:
                    data = soup.find('div', itemtype="http://schema.org/Product")
                    price = data.find('meta', itemprop="price")['content'].split('.')[0]
                    title = data.find('meta', itemprop="name")['content']
                    availability = soup.find('div', itemtype="http://schema.org/Offer")
                    avail = availability.find('link')['href']
                    if avail != 'http://schema.org/InStock':
                            price = 999999998
                    return (title, price)
                except:
                    title = 'EmptyWild'
                    price = 99999999
                    return (title,price)
        elif urlparse(url).netloc == ozon:
                try:
                    data = soup.find('script', type='application/ld+json') 
                    data = str(data) 
                    data = data.replace('<script type="application/ld+json">','').replace('/script','').replace('<>','') 
                    data = ast.literal_eval(data)
                    if data['offers']['availability'] == 'http://schema.org/InStock':
                            price = data['offers']['price']
                    elif data['offers']['availability'] == 'http://schema.org/OutOfStock':
                            price = 999999998
                    title = data['name']
                    cards.append(title)
                    cards.append(int(price))
                    return (cards[0],cards[1])
                except:
                    title = 'EmptyOzon'
                    price = 99999999
                    return (title,price)