from textblob_de import TextBlobDE
from nltk.corpus import stopwords
import sys
import os
import dearpygui.dearpygui as dpg
import re
import requests
from bs4 import BeautifulSoup
import textwrap
import re
import datetime


def scrape():      
    
    lg_page = requests.get("https://orf.at/")
    lg_soup = BeautifulSoup(lg_page.content, 'html.parser')
    lg_links = lg_soup.find_all('a',{'href': re.compile('^.*\d{2}.')})

    lg_li = []
    parent_li = []
    count = 0

    for a in lg_links:

        try:

            title = a.find_previous("h2", {"class" : "ticker-ressort-title"}).text
            articleHeading = re.sub(r"\s{2,}", "",a.text)
            headingFormatted = re.sub(r"\s", "_", articleHeading)
            dt =  str(datetime.datetime.now().date())
            titt = re.sub(r"-|\s","_", f"{dt}_{title}_{headingFormatted}")
            lg_li.append((titt,a['href']))
            print(titt)
        except:
            print("weird title")


    for title, link in lg_li:
        print(title, " - ", link)


    #print(lg_li)

"""
    for x in lg_li:
        count += 1/(len(lg_li) -1)
        page = requests.get(x)
        scraping(page, count)

"""


scrape()