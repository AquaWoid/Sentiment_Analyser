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



"""
This needs to be run once if the nltk corpus is not yet installed on your machine:

import nltk
nltk.download()
"""

#Dearpygui context and viewport creation - needs to be intialised at start
dpg.create_context()
dpg.create_viewport(title='Article Sentiment Analyser', width=1200, height=1000)


#function to reference and load the saved .txt files in the article folder, here i use a mixture of functions and variables from the 'os' and 'sys' standard modules. 
def getFiles():

    text = ""
    path = os.path.join(sys.path[0], "articles")

    with open(os.path.join(path, dpg.get_value("cbo_article")) , 'r', encoding='UTF-8') as fh:
        text = fh.read().lower()

    return text

#function to initialise the german version of TextBlob 
def textBlobInit(text):

    #textblob and stopword declaration + tokenization
    tb = TextBlobDE(text)
    stop = stopwords.words("german")
    wordlist = list(tb.words)

    #removing the stowpords from our article text
    for word in wordlist:
        if word in stop:
            wordlist.remove(word)
            print("removed:", word)

    #Combining the words to full string again using Regex to clear occurences where there is no whitespace after a dot. (this was messing with textblobs ability to detect sentences)
    filtered_string = " ".join(wordlist)
    second_layer_filter = re.sub(r"\.", ". ", filtered_string)

    #declaring a second textblob object from the filtered string
    tb_filtered = TextBlobDE(second_layer_filter)
    tb_filtered.sentences

    #setting the text of the 'sentence_number' UI text
    dpg.set_value("sentence_number",  f"Sentences: {len(tb_filtered.sentences)}")
    
    #here a list of sentiment values is created and appended with using the sentiment.polarity values of the sentence inside a for loop
    sentence_group = []
    for sentence in tb_filtered.sentences:
        sentence_group.append(sentence.sentiment.polarity)

    return sentence_group

#function that takes in our sentence_group list to add the sentiment values stored in the list to the negative, neutral and positive variables
#these will then be calculated to an overall sentiment value using the normalization calculation: score = (positive words - negative words) / (positive words + negative words) to get a value between 0.0 and 1.0
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

    #Updating the dpg Barplot
    dpg.set_value("polarity_text", f"Sentence Polarity: Neutral: {neutral} Negative: {negative} Positive: {positive}")
    dpg.set_value("overall_sentiment_text", sentiment_score)
    dpg.set_value("bar_neutral", ([-1.5], [neutral]))
    dpg.set_value("bar_negative", ([0], [negative]))
    dpg.set_value("bar_positive", ([1.5], [positive]))


#Main function of the script which will be initialised on start
def analyise():
    
    #At first the text is declared, then the text is sent through the textBlobInit function to get our sentiment value group which is then sent to the sentimentCalculation function. 
    text = getFiles()
    sentence_group = textBlobInit(text)
    sentimentCalculation(sentence_group)

    #Text fromatting for the output text in the UI using textwrap and regex
    t_formatted = textwrap.dedent(text=text)
    t_formatted = textwrap.fill(t_formatted, width=70, break_long_words=True)
    t_formatted = re.sub(r' +|^\s', ' ', t_formatted)
    dpg.set_value('input_text', t_formatted)

    #Functions to fit the data on the plot axes
    dpg.fit_axis_data("y_axis")
    dpg.fit_axis_data("x_axis")


 #function to intialise our webscraper
def initializeWebscraper():

    #At first we do a HTTP request of the main Website and extract all links using the beautifulsop function 'find_all'
    lg_page = requests.get("https://orf.at/")
    lg_soup = BeautifulSoup(lg_page.content, 'html.parser')
    lg_links = lg_soup.find_all('a',{'href': re.compile('^.*\d{2}.')})

    #Now a Link Group list (lg_li) is declared for iteration.
    lg_li = []
    count = 0
    invalidCount = 0

    #For every link in the resulting list of the 'find_all' the article name will be formatted to a filename with underlines which will then be stored together with the link in the Linkgroup List
    for a in lg_links:
        try:
            title = a.find_previous("h2", {"class" : "ticker-ressort-title"}).text
            articleHeading = re.sub(r"\s{2,}", "",a.text)
            headingFormatted = re.sub(r"\s", "_", articleHeading)
            dt =  str(datetime.datetime.now().date())
            filename = re.sub(r"-|\s","_", f"{dt}_{title}_{headingFormatted}")
            lg_li.append((filename,a['href']))
            print(filename)
        #If there is no valid article or article name the article won't be added to the list and the variable invalidCount (which i will later use to offset the progress bar for article downloading) gets +1     
        except:
            print("Not a categorized article")
            invalidCount += 1


    #Now the scraping function will be executed for every article that is currently linked on the main website. We pass in the HTTP Request of the Link, a Count for the Progress bar and the title for file writing.
    for title, link in lg_li:
        count += 1/(len(lg_li) -invalidCount)
        page = requests.get(link)
        try:
            scraping(page, count, title)
        except: 
            addConsoleText("Encountered invalid page -> skipping article")


    dpg.set_item_label("download_progress", "Collect Articles")


#function to scrape the single article links
def scraping(page, count, title):
  
    #Beautifulsoup object declaration
    soup = BeautifulSoup(page.content, 'html.parser')

    #Heading 1 extraction
    try:
        h1 = soup.select('h1')[0].text.strip()
    except:
        return

    #Heading 2 extraction
    try:
        h2 = soup.select('h2')[0].text.strip()
    except:
        return


    #Using Regex to format the article names for later use a file names
    h1_formatted = re.sub(r'\s|-', '_', h1)
    h1_cleaned = re.sub (r"\.|:", "", h1_formatted)

    #this filters out articles or links that are Javascript based and need a proper browser (or simulator) to display their data
    if h1_cleaned == "JavaScript_is_not_available":
        return

    print(h1_cleaned)
 
    #Text initialisation and setting through phrases extracted using Beautifulsoup's 'find_all' function.
    thetext = ""
 
    for x in soup.find_all('p'):
        thetext += ("" + x.getText())

    #Final regex clean filtering out duplicate whitespaces
    text_cleaned = re.sub(r"\s{2,}", "", thetext)
    
    #Writing a new file to the "articles" folder with the input file name we got passed in from the "initialiceWebscraper" function
    with open(os.path.join(sys.path[0],"articles", f"{title}.txt"), 'w', encoding='UTF-8') as fh:
        fh.write(text_cleaned)

    #Setting the visual UI progress bar
    dpg.set_value("download_progress", count)
    dpg.set_item_label("download_progress", f"Progress: {count*100} %")

    print(text_cleaned)


#CSV section

#function to create a new csv file transfering a Pandas dataframe using the dataframe.to_csv function. 
def create_csv():
    df = pd.DataFrame(columns=["title", "sentiment"])
    csv_name = dpg.get_value("csv_name")
    df.to_csv(os.path.join(sys.path[0], "csv",f"{csv_name}.csv"), mode="a",index=False)
    addConsoleText(f"Created {csv_name}.csv")


#function to append the overall sentiment score of the currently opened text to the selected csv file
def csv_export():
    df = pd.DataFrame(columns=["title", "sentiment"])
    df.loc["Artikel Name"] = (dpg.get_value("cbo_article"), dpg.get_value("overall_sentiment_text"))
    csv_name = dpg.get_value("cbo_csv_import")
    df.to_csv(os.path.join(sys.path[0], "csv",f"{csv_name}"), mode="a",index=False, header=False)
    addConsoleText(f"Apennded article score to {csv_name}.csv")

#function to load the previously saved csv file to be displayed in the line plot below
def load_csv():
    filename = dpg.get_value("cbo_csv_import")
    data = pd.read_csv(os.path.join(sys.path[0], "csv",f"{filename}"))
    df = pd.DataFrame(data, columns=["title", "sentiment"])

    sentiment_score =  []
    articlecount = []
    count = 0

    #List filling for proper display in the plot
    for index in df.index:
        articlecount.append(count)
        sentiment_score.append(df["sentiment"][index])
        print(df["title"][index], df["sentiment"][index])
        count +=1

    #Plot seting and axes fit
    dpg.set_value("sen_score", [articlecount, sentiment_score])
    dpg.fit_axis_data("y_axis_s")
    dpg.fit_axis_data("x_axis_s")

    addConsoleText(f"Loaded {filename}")

#function to update the combobox entries to the file that lie in the 'articles' fikder
def reloadFolder():
    path = os.path.join(sys.path[0], "articles")
    files = sorted(os.listdir(path))
    dpg.configure_item("cbo_article", items=files)
    addConsoleText("Reloaded Folder")

#Function to add text to the console window on the bottom right
def addConsoleText(text):
        console_add = dpg.get_value("console_text") + f"\n{text}"
        dpg.set_value("console_text", console_add)


#UI SETUP | I have a detailed description of these element in my documentation that shows what all of this is coresponding to the final program.
#Due to the documentation i won't comment all of this here, also the parameters are quite self explaining

files = sorted(os.listdir(os.path.join(sys.path[0], "articles")))
csv_files = sorted(os.listdir(os.path.join(sys.path[0], "csv")))

#Main Window
with dpg.window(tag="main_window", label='Article Sentiment Analyser', width=1200, height=1000):

    #Section before the first plot
    dpg.add_text("Use the button below to get today's articles into your articles folder")
    dpg.add_button(callback=initializeWebscraper, label='Collect articles', width=200)
    dpg.add_progress_bar(tag="download_progress", label="Article collection progress",width=570)
    dpg.add_combo(tag='cbo_article', items=files, default_value=f'{files[0]}',width=570, callback=analyise)
    dpg.add_button(label="Reload articles folder", callback=reloadFolder)
    dpg.add_text("Number of Sentences: ", tag="sentence_number")
    dpg.add_text("Polarity Values:", tag="polarity_text")
    dpg.add_text("Overall Sentiment Score:", tag="overall_sentiment_text", label="Overall Sentiment Score:")

    #Barplot for the sentiment values
    with dpg.plot(label='Sentiment Values', width=570, height=400):

        legend = dpg.add_plot_legend(show=True)
        dpg.show_item(legend)
        dpg.add_plot_axis(dpg.mvXAxis, label="Sentiment", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Score", tag="y_axis")
        dpg.add_bar_series([-1.5], [10], label="Neutral", weight=1, parent="y_axis", tag="bar_neutral")
        dpg.add_bar_series([0], [7], label="Negative", weight=1, parent="y_axis", tag="bar_negative")
        dpg.add_bar_series([1.5], [9], label="Positive", weight=1, parent="y_axis", tag="bar_positive")

    #CSV section betweeen the two plots
    dpg.add_input_text(tag='input_text', multiline=True, readonly=True, width=570, height= 580, pos=[600, 30])
    dpg.add_input_text(tag='console_text', multiline=True, readonly=True, width=570, height= 130, pos=[600, 620])
    dpg.add_button(tag="csv_save", label="Append Sentiment Score to CSV", callback=csv_export)
    dpg.add_combo(tag="cbo_csv_import", items=csv_files, default_value=f"{csv_files[0]}", width=570)
    dpg.add_text("Enter the name of the current topic found in the file names create a new CSV")
    dpg.add_input_text(tag="csv_name", default_value="topic", width=570)
    dpg.add_button(tag="csv_create", label="Create new topic CSV", callback=create_csv)
    dpg.add_button(tag="csv_load", label="Create Score Plot from existing CSV", callback=load_csv)

    #Line Plot for the overall sentiment score visualisation of multiple articles
    with dpg.plot(label="Sentiment_Scores", width=570, height=200):

        legend = dpg.add_plot_legend(show=True)
        dpg.show_item(legend)
        dpg.add_plot_axis(dpg.mvXAxis, label="Sentimentt", tag="x_axis_s")
        dpg.add_plot_axis(dpg.mvYAxis, label="Scoree", tag="y_axis_s")
        dpg.add_line_series([0],[0], label="Sentimen Score", tag="sen_score", parent="y_axis_s")
        dpg.set_axis_limits_auto("y_axis_s")
        dpg.set_axis_limits_auto("x_axis_s")


#On-script-start functions

#Entry function of the script
analyise()

#Default dpg functions to properly display the UI            
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

