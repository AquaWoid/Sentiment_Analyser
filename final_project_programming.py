from textblob_de import TextBlobDE
from nltk.corpus import stopwords
import sys
import os
import dearpygui.dearpygui as dpg
import re
import requests
from bs4 import BeautifulSoup
import textwrap
import pandas as pd
import datetime
from matplotlib import pyplot as plt



dpg.create_context()
dpg.create_viewport(title='Article Sentiment Analyser', width=1200, height=800)



def getFiles():

    text = ""
    path = os.path.join(sys.path[0], "articles")
    files = sorted(os.listdir(path))


    with open(os.path.join(path, dpg.get_value("cbo_article")) , 'r', encoding='UTF-8') as fh:
        text = fh.read().lower()

    #print(text)
    return text


def textBlobInit(text):

    tb = TextBlobDE(text)
    stop = stopwords.words("german")
    wordlist = list(tb.words)

    for word in wordlist:
        if word in stop:
            wordlist.remove(word)
            print("removed:", word)

    filtered_string = " ".join(wordlist)
    second_layer_filter = re.sub(r"\.", ". ", filtered_string)

    tb_filtered = TextBlobDE(second_layer_filter)
    tb_filtered.sentences

    dpg.set_value("sentence_number",  f"Sentences: {len(tb_filtered.sentences)}")
    sentence_group = []

    for sentence in tb_filtered.sentences:
        sentence_group.append(sentence.sentiment.polarity)

    return sentence_group


def sentimentCalculation(sentence_group):

    negative = 0
    positive = 0
    neutral = 0

    for polarity in sentence_group:
        if polarity == 0:
            neutral += 1
        if polarity > 0:
            positive +=1
        if polarity < 0:
            negative +=1

    try:
        sentiment_score = (positive - negative) / (positive + negative)
    except ZeroDivisionError:
        sentiment_score = 0

    dpg.set_value("polarity_text", f"Sentence Polarity: Neutral: {neutral} Negative: {negative} Positive: {positive}")
    dpg.set_value("overall_sentiment_text", sentiment_score)
    dpg.set_value("bar_neutral", ([-1.5], [neutral]))
    dpg.set_value("bar_negative", ([0], [negative]))
    dpg.set_value("bar_positive", ([1.5], [positive]))

def analyise():
    
    text = getFiles()
    sentence_group = textBlobInit(text)
    sentimentCalculation(sentence_group)

    #Text fromatting using textwrap and regex
    t_formatted = textwrap.dedent(text=text)
    t_formatted = textwrap.fill(t_formatted, width=70, break_long_words=True)
    t_formatted = re.sub(r' +|^\s', ' ', t_formatted)
  
    dpg.set_value('input_text', t_formatted)

def create_csv():
        df = pd.DataFrame(columns=["title", "sentiment"])
        csv_name = dpg.get_value("csv_name")
        df.to_csv(os.path.join(sys.path[0], "csv",f"{csv_name}.csv"), mode="a",index=False)
        console_add = dpg.get_value("console_text") + f"\nCreated {csv_name}"
        dpg.set_value("console_text", console_add)

def csv_export():
    df = pd.DataFrame(columns=["title", "sentiment"])
    article = dpg.get_value("cbo_article")
    df.loc["Artikel Name"] = (dpg.get_value("cbo_article"), dpg.get_value("overall_sentiment_text"))
    csv_name = dpg.get_value("cbo_csv_import")
    df.to_csv(os.path.join(sys.path[0], "csv",f"{csv_name}"), mode="a",index=False, header=False)
    console_add = dpg.get_value("console_text") + f"\nApennded article Score to {csv_name}"
    dpg.set_value("console_text", console_add)

def load_csv():
    filename = dpg.get_value("cbo_csv_import")
    data = pd.read_csv(os.path.join(sys.path[0], "csv",f"{filename}"))
    df = pd.DataFrame(data, columns=["title", "sentiment"])
    #print(data)



    title = []
    sentiment_score =  []

    for index in df.index:
        title.append(df["title"][index])
        sentiment_score.append(df["sentiment"][index])
        print(df["title"][index], df["sentiment"][index])


    console_add = dpg.get_value("console_text") + f"\nLoaded {filename}"
    dpg.set_value("console_text", console_add)

    line2 = plt.plot(title, sentiment_score, label="Sentiment")

    plt.legend(loc="upper right")
    plt.show()    

   # print(df)

   # for sentiment in df:
    #    print(sentiment)



    



def initializeWebscraper():

    lg_page = requests.get("https://orf.at/")
    lg_soup = BeautifulSoup(lg_page.content, 'html.parser')
    lg_links = lg_soup.find_all('a',{'href': re.compile('^.*\d{2}.')})

    lg_li = []
    count = 0

    for a in lg_links:
        try:
            title = a.find_previous("h2", {"class" : "ticker-ressort-title"}).text
            articleHeading = re.sub(r"\s{2,}", "",a.text)
            headingFormatted = re.sub(r"\s", "_", articleHeading)
            dt =  str(datetime.datetime.now().date())
            filename = re.sub(r"-|\s","_", f"{dt}_{title}_{headingFormatted}")
            lg_li.append((filename,a['href']))
            print(filename)
        except:
            print("Not a categorized article")



    for title, link in lg_li:
        count += 1/(len(lg_li) -1)
        page = requests.get(link)
        scraping(page, count, title)

    dpg.set_item_label("download_progress", "Collect Articles")



def scraping(page, count, title):
  
    soup = BeautifulSoup(page.content, 'html.parser')

    try:
        h1 = soup.select('h1')[0].text.strip()
    except:
        return

    try:
        h2 = soup.select('h2')[0].text.strip()
    except:
        return

    print('\n', h1, '\n')

    h1_formatted = re.sub(r'\s|-', '_', h1)
    h1_cleaned = re.sub (r"\.|:", "", h1_formatted)

    if h1_cleaned == "JavaScript_is_not_available":
        return

    print(h1_cleaned)
 
    thetext = ""
 
    for x in soup.find_all('p'):
        thetext += ("" + x.getText())

    text_cleaned = re.sub(r"\s{2,}", "", thetext)
    
    with open(os.path.join(sys.path[0],"articles", f"{title}.txt"), 'w', encoding='UTF-8') as fh:
        fh.write(text_cleaned)

    dpg.set_value("download_progress", count)
    dpg.set_item_label("download_progress", f"Progress: {count*100} %")
    print(text_cleaned)


def reloadFolder():
    path = os.path.join(sys.path[0], "articles")
    files = sorted(os.listdir(path))
    dpg.configure_item("cbo_article", items=files)
    console_add = dpg.get_value("console_text") + "\nReloaded Folder"
    dpg.set_value("console_text", console_add)




path = os.path.join(sys.path[0], "articles")
files = sorted(os.listdir(path))


csv_patch = os.path.join(sys.path[0], "csv")
csv_files = sorted(os.listdir(csv_patch))

with dpg.window(label='Article Sentiment Analyser', width=1200, height=780):
    dpg.add_text("Use the button below to get today's articles into your articles folder")
    dpg.add_button(callback=initializeWebscraper, label='Collect articles', width=200)
    dpg.add_progress_bar(tag="download_progress", label="Article collection progress",width=570)
    dpg.add_combo(tag='cbo_article', items=files, default_value=f'{files[0]}',width=570, callback=analyise)
    dpg.add_button(label="Reload articles folder", callback=reloadFolder)
    dpg.add_text("Number of Sentences: ", tag="sentence_number")
    dpg.add_text("Polarity Values:", tag="polarity_text")
    dpg.add_text("Overall Sentiment Score:", tag="overall_sentiment_text", label="Overall Sentiment Score:")

    with dpg.plot(label='Sentiment Values', width=570, height=400):

        legend = dpg.add_plot_legend(show=True)
        dpg.show_item(legend)

        dpg.add_plot_axis(dpg.mvXAxis, label="Sentiment", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Score", tag="y_axis")
        dpg.add_bar_series([-1.5], [10], label="Neutral", weight=1, parent="y_axis", tag="bar_neutral")
        dpg.add_bar_series([0], [7], label="Negative", weight=1, parent="y_axis", tag="bar_negative")
        dpg.add_bar_series([1.5], [9], label="Positive", weight=1, parent="y_axis", tag="bar_positive")


    dpg.add_input_text(tag='input_text', multiline=True, readonly=True, width=570, height= 580, pos=[600, 30])
    dpg.add_input_text(tag='console_text', multiline=True, readonly=True, width=570, height= 130, pos=[600, 620])
    dpg.add_button(tag="csv_save", label="Append Sentiment Score to CSV", callback=csv_export)
    dpg.add_combo(tag="cbo_csv_import", items=csv_files, default_value=f"{csv_files[0]}", width=570)
    dpg.add_text("Enter the name of the current topic found in the file names create a new CSV")
    dpg.add_input_text(tag="csv_name", default_value="topic", width=570)
    dpg.add_button(tag="csv_create", label="Create new topic CSV", callback=create_csv)


    dpg.add_button(tag="csv_load", label="Create Score Plot from existing CSV", callback=load_csv)


analyise()
#Show UI
            
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

