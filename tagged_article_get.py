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

def initScrape():
    lg_page = requests.get("https://orf.at/")
    lg_soup = BeautifulSoup(lg_page.content, 'html.parser')

    lg_links_groups = lg_soup.find("h2", {'class' : 'ticker-ressort-title' })
    print(lg_links_groups)
    children = lg_links_groups.findChildren("a")

    for child in children:
        print(child.text)



  #  for h2 in lg_links_groups:
  #      h2.find
  #      print(h2.text)



initScrape()

"""
    lg_links = lg_soup.find_all('a',{'href': re.compile('^.*\d{2}.')})

    lg_li = []
    count = 0

    for a in lg_links:
        lg_li.append(a['href'])

    for x in lg_li:
        count += 1/(len(lg_li) -1)
        page = requests.get(x)
        scraping(page, count)

    dpg.set_item_label("download_progress", "Collect Articles")
"""
