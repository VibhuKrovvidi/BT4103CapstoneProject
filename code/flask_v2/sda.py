# DSTA Scraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options

# Import standard tools
import time
import pandas as pd
import praw
import requests
import math
import sys
import string
from datetime import datetime, date, timedelta
import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, firestore
from loguru import logger
import numpy as np
import nltk
import regex
import re
from tqdm import tqdm
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.wordnet import WordNetLemmatizer 
from sklearn.feature_extraction.text import TfidfVectorizer
import stanza
import spacy
from spacy import displacy

class DSTA_Service_Delivery():
    def __init__(self):
        stanza.download('en') # download English model
        nltk.download('stopwords')
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')

        self.chrome_options = Options();
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_prefs = {}
        self.chrome_options.experimental_options["prefs"] = self.chrome_prefs
        self.chrome_prefs["profile.default_content_settings"] = {"images": 2}
        self.nlp = stanza.Pipeline('en')
        self.replacements = {'/':'_', '-':'_','u':'you', 'im': "i'm", 'tbh':'to be honest', 'dk': "dont' know", 'dont': "don't", 'Ã°Ã¿â„¢ÂÃ°Ã¿ÂÂ»':'', 'imo': 'in my opinion', 'n"t':'not',"'s":'is'}


    def initialiseDB(self):
        # Initialise Firebase
        cred = credentials.Certificate('fbadmin.json')
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        print("Database Initialised")

    def get_google_reviews(self, url, location = "CMPB"):
        """
        Retrieves Google Reviews and pushes them to the Firebase storage
        This function will

        """
        driver = webdriver.Chrome(options=self.chrome_options)
        driver.get(url);

        delay = 3# seconds
        try:
            myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'content-container')))
            print("Page is ready!")
        except TimeoutException:
            print("Loading took too much time!")

        time.sleep(3)
        reviewCount = len(driver.find_elements_by_xpath("//div[@class='section-review ripple-container']"))

        totalReviews = driver.find_elements_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[3]/div[2]/div/div[2]/div[2]');
        totalReviews = [i for i in totalReviews][0].text
        totalReviews = int(totalReviews.split()[0])
        print(str(totalReviews) + " reviews found")

        # loading a minimum of 50 reviews
        while reviewCount < totalReviews: #<=== change this number based on your requirement
            #print("Scrolling to review number :", reviewCount)
            # load the reviews
            driver.find_element_by_xpath("//div[contains(@class,'section-loading-spinner')]").location_once_scrolled_into_view 
            # wait for loading the reviews
            WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@class='section-loading-overlay-spinner'][@style='display:none']")))
            # get the reviewsCount
            reviewCount = len(driver.find_elements_by_class_name("section-review-content"))

        content = []
        temp_content = driver.find_elements_by_class_name('section-review-review-content')
        content = [c.text for c in temp_content]

        time.sleep(2)
        driver.quit()

        # Push to Firebase
        gr_ref = self.db.collection(u'google_reviews')
        
        
        # Get last pushed data
        latest = gr_ref.where(u'location', u'==', location).order_by(u'timestamp', direction=firestore.Query.DESCENDING).order_by(u'id').limit(1).stream()
        latest = [i.to_dict() for i in latest]
        has_latest = False
        try:
            print(latest[0]['content'])
            has_latest = True
        except:
            pass
        idcount = 1
        now = datetime.now()
        dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S"))

        for i in content:
            if has_latest:
                if i == latest[0]['content']:
                    break;
                else:
                    pushid = idcount;
                    dt = dt_string;
                    content = i;
                    pushref = gr_ref.add({
                        'id' : pushid,
                        'timestamp' : dt_string,
                        'content' : content,
                        'location' : location
                        });
                    print("Pushed ", pushref)
                    idcount += 1;
            else:
                pushid = idcount;
                dt = dt_string;
                content = i;
                pushref = gr_ref.add({
                    'id' : pushid,
                    'timestamp' : dt_string,
                    'content' : content,
                    'location' : location
                    });
                print("Pushed ", pushref)
                idcount += 1;

    def get_harwarezone(self, 
        url = 'https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html', 
        forum="nsknowledge", 
        limit=30):
        
        post_title = []
        post_username = []
        post_message = []
        reply_to = []

        # driver = webdriver.Chrome()
        driver = webdriver.Chrome(options=self.chrome_options)

        #for each page:
        #load the forum
        driver.get(url)
        time.sleep(10)

        #title of forum
        forum_title = driver.find_element_by_class_name('p-title-value').text
        print('forum title = ' + forum_title)

        flag = True

        idx = 0;
        while flag:
            if idx >= limit:
                break;
            #get list of all posts
            print('getting posts')
            posts = driver.find_elements_by_class_name('message-body.js-selectToQuote')
            print('done getting posts')
                        #first username is not the first post username
            names = driver.find_elements_by_class_name('username')
            try:
                names.pop(0)
                for n in names:
                    post_username.append(n.text)
            except:
                pass;

            #message (whole box) = post_message, message being replied to = quote
            #for every post, check if there is quote.
            for p in posts:
                #get the full message, including prev if present
                full = p.find_element_by_class_name('bbWrapper').text
                #check if there is reply
                try:
                    reply = p.find_element_by_class_name('bbCodeBlock.bbCodeBlock--expandable.bbCodeBlock--quote.js-expandWatch').text
                    reply = reply.split('\n')
                    full = full.split('\n')[1:]
                    #wtv that is in the full message, but not in the quote is the reply for that user
                    new = [i for i in full if i not in reply]
                    new = " ".join(new) #join to one string
                    reply = " ".join(reply)
                    post_message.append(new) #adding the actual message to a list
                    reply_to.append(reply) #adding the reply to a list if there is
                    post_title.append(forum_title) #adding title
                except NoSuchElementException:
                    full = full.split('\n')
                    full = " ".join(full)
                    post_message.append(full)
                    reply_to.append('NIL') #no replies
                    post_title.append(forum_title)
            try:
                                next_button = driver.find_element_by_class_name("pageNav-jump.pageNav-jump--next")
                                next_button.click()
            except NoSuchElementException:
                                flag = False
                                print("No more next button")
            
        # data = pd.DataFrame(list(zip(post_title,post_username,post_message,reply_to)), columns = ['post_title','post_username', 'post', 'reply to'])
        # data.to_csv("hwz_Post_title_output.csv")
        driver.close()
        
        # Push to Firebase
        hz_ref = self.db.collection(u'hardwarezone_reviews')
        
        # Get last pushed data
        latest = hz_ref.where(u'forum', u'==', forum).order_by(u'timestamp', direction=firestore.Query.DESCENDING).order_by(u'id').limit(1).stream()
        latest = [i.to_dict() for i in latest]
        has_latest = False;
        try:
            print(latest[0]['content'])
            has_latest = True;
        except:
            pass;
        idcount = 1;
        now = datetime.now()
        dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S"))

        # Push content
        for i in post_message:
            if has_latest:
                if i == latest[0]['content']:
                    break;
                else:
                    pushid = idcount;
                    dt = dt_string;
                    content = i;
                    pushref = hz_ref.add({
                        'id' : pushid,
                        'timestamp' : dt_string,
                        'content' : content,
                        'forum' : forum
                        });
                    print("Pushed ", pushref)
                    idcount += 1;
            else:
                pushid = idcount;
                dt = dt_string;
                content = i;
                pushref = hz_ref.add({
                    'id' : pushid,
                    'timestamp' : dt_string,
                    'content' : content,
                    'forum' : forum
                    });
                print("Pushed ", pushref)
                idcount += 1;

        print("HardwareZone data for", forum, "has been scraped and stored.")

    def submissions_pushshift_praw(self, subreddit, reddit, start=None, end=None, limit=100, extra_query=""):
        """
        A simple function that returns a list of PRAW submission objects during a particular period from a defined sub.
        This function serves as a replacement for the now deprecated PRAW `submissions()` method.
        
        :param subreddit: A subreddit name to fetch submissions from.
        :param start: A Unix time integer. Posts fetched will be AFTER this time. (default: None)
        :param end: A Unix time integer. Posts fetched will be BEFORE this time. (default: None)
        :param limit: There needs to be a defined limit of results (default: 100), or Pushshift will return only 25.
        :param extra_query: A query string is optional. If an extra_query string is not supplied, 
                            the function will just grab everything from the defined time period. (default: empty string)
        
        Submissions are yielded newest first.
        
        For more information on PRAW, see: https://github.com/praw-dev/praw 
        For more information on Pushshift, see: https://github.com/pushshift/api
        """
        matching_praw_submissions = []
        
        # Default time values if none are defined (credit to u/bboe's PRAW `submissions()` for this section)
        utc_offset = 28800
        now = int(time.time())
        start = max(int(start) + utc_offset if start else 0, 0)
        end = min(int(end) if end else now, now) + utc_offset
        
        # Format our search link properly.
        search_link = ('https://api.pushshift.io/reddit/submission/search/'
                       '?subreddit={}&after={}&before={}&sort_type=score&sort=asc&limit={}&q={}')
        search_link = search_link.format(subreddit, start, end, limit, extra_query)
        
        # Get the data from Pushshift as JSON.
        retrieved_data = requests.get(search_link)
        returned_submissions = retrieved_data.json()['data']
        
        i = 0
        # Iterate over the returned submissions to convert them to PRAW submission objects.
        for submission in returned_submissions:
            
            self.progress(i, len(returned_submissions), status='Collecting posts')
            # Take the ID, fetch the PRAW submission object, and append to our list
            praw_submission = reddit.submission(id=submission['id'])
            matching_praw_submissions.append(praw_submission)
            i += 1
         
        # Return all PRAW submissions that were obtained.
        return matching_praw_submissions

    def progress(self, count, total, status=''):
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))
        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
        sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)

    def get_reddit(self, subreddit_name = "NationalServiceSG", start_date=1612108800, limit_amt=2000):
        reddit = praw.Reddit(client_id='kQoyoJ9Ag4JxTQ', client_secret='fPR3EGxAsC4ERoPHW4HNfxaMsle5Nw', user_agent='nsscraper')
        
        # Get posts beginning from February 1 2021
        extracted_posts = self.submissions_pushshift_praw(subreddit = subreddit_name, start = start_date, limit=limit_amt, reddit = reddit)

        posts = []
        for p in extracted_posts:
            try:
                posts.append([p.title, p.score, p.id, p.subreddit, p.url, p.num_comments, p.selftext, p.link_flair_template_id, p.link_flair_text, p.created])
            except AttributeError:
                posts.append([p.title, p.score, p.id, p.subreddit, p.url, p.num_comments, p.selftext, "None", "None", p.created])

        posts = pd.DataFrame(posts, columns=['title', 'score', 'id', 'subreddit', 'url', 'num_comments', 'body', 'flair_id', 'flair', 'created'])
        print("Posts:")
        print(posts)

        # Get all comments per post
        all_comments = []
        i = 0
        for iden in posts['id']:
            self.progress(i, len(posts.index), status='Collecting comments')
            post = reddit.submission(id=iden)
            post.comments.replace_more(limit=0)
            for c in post.comments.list():
                all_comments.append([c.score, c.id, c.subreddit, c.depth, c.body, c.created, iden])
            i += 1

        all_comments = pd.DataFrame(all_comments, columns=['score', 'id', 'subreddit', 'depth', 'body', 'created', 'op_id'])
        print("Comments:")
        print(all_comments)

        # Preprocess data
        posts.loc[(posts.body == "[removed]"), "body"] = ""
        posts.loc[(posts.body == "[deleted]"), "body"] = ""
        all_comments.loc[(all_comments.body == "[removed]"), "body"] = "" 
        all_comments = all_comments.filter(items = ["body"]).rename(columns = {"body": "content"})

        posts = posts['body'].tolist()
        comments = all_comments['content'].tolist()

        # Push to Firebase
        rd_ref = self.db.collection(u'reddit_posts')
        
        # Get last pushed data
        latest = rd_ref.order_by(u'timestamp', direction=firestore.Query.DESCENDING).order_by(u'id').limit(1).stream()
        latest = [i.to_dict() for i in latest]
        has_latest = False;
        try:
            print(latest[0]['content'])
            has_latest = True;
        except:
            pass;
        idcount = 1;
        now = datetime.now()
        dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S"))

        # Push content
        for i in posts:
            if has_latest:
                if i == latest[0]['content']:
                    break;
                else:
                    pushid = idcount;
                    dt = dt_string;
                    content = i;
                    pushref = rd_ref.add({
                        'id' : pushid,
                        'timestamp' : dt_string,
                        'content' : content
                        });
                    print("Pushed ", pushref)
                    idcount += 1;
            else:
                pushid = idcount;
                dt = dt_string;
                content = i;
                pushref = rd_ref.add({
                    'id' : pushid,
                    'timestamp' : dt_string,
                    'content' : content
                    });
                print("Pushed ", pushref)
                idcount += 1;

        # Push to Firebase
        rdc_ref = self.db.collection(u'reddit_comments')
        
        # Get last pushed data
        latest = rdc_ref.order_by(u'timestamp', direction=firestore.Query.DESCENDING).order_by(u'id').limit(1).stream()
        latest = [i.to_dict() for i in latest]
        has_latest = False;
        try:
            print(latest[0]['content'])
            has_latest = True;
        except:
            pass;
        idcount = 1;
        now = datetime.now()
        dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S"))

        # Push content
        for i in posts:
            if has_latest:
                if i == latest[0]['content']:
                    break;
                else:
                    pushid = idcount;
                    dt = dt_string;
                    content = i;
                    pushref = rdc_ref.add({
                        'id' : pushid,
                        'timestamp' : dt_string,
                        'content' : content
                        });
                    print("Pushed ", pushref)
                    idcount += 1;
            else:
                pushid = idcount;
                dt = dt_string;
                content = i;
                pushref = rdc_ref.add({
                    'id' : pushid,
                    'timestamp' : dt_string,
                    'content' : content
                    });
                print("Pushed ", pushref)
                idcount += 1;

        print("Reddit Data for " + subreddit_name + " have been scraped and stored");

    def get_all_data(self):
        data = []

        gr_ref = self.db.collection(u'google_reviews')
        try:
            gdata = gr_ref.get()
            for entry in gdata:
                data.append(entry.to_dict()['content']);
        except:
            print("Error getting Google Reviews")

        hz_ref = self.db.collection(u'hardwarezone_reviews')
        try:
            hzdata = hz_ref.get()
            for entry in hzdata:
                data.append(entry.to_dict()['content']);
        except:
            print("Error getting Hardwarezone Reviews")
        
        
        rd_ref = self.db.collection(u'reddit_posts')
        try:
            rddata = rd_ref.get();
            for entry in rddata:
                data.append(entry.to_dict()['content']);
        except:
            print("Error getting Reddit Posts")

        rdc_ref = self.db.collection(u'reddit_comments')
        try:
            rdcdata = rd_ref.get();
            for entry in rdcdata:
                data.append(entry.to_dict()['content']);
        except:
            print("Error getting Reddit Comments")
        
        print(data)
        return data

    def feature_extraction(self, txt):
        """
        Extracts features and their corresponding descriptors for each review.
        The output will be a list of lists. For each list element in the output, it will include 
        the extracted feature and a list of the descriptors for that particular feature.

        Parameters:
        txt : str
            This will be the review to undergo feature extraction.
        """
        # Do replacements for short forms and abbreviations
        txt = txt.split()
        replaced = []
        for words in txt:
            if words in self.replacements:
                replaced.append(self.replacements[words])
            else:
                replaced.append(words)
        txt = ' '.join(replaced)

        # Add fullstop to the end of the review and paragraph
        txt += '.'
        txt = txt.replace("\n", ".")

        # Tokenise para into sentences
        sentList = nltk.sent_tokenize(txt)

        #final list to be returned
        retlist = [];

        # For each sentence
        for line in sentList:
            # Tag and word tokenize
            txt_list = nltk.word_tokenize(line)
            taggedList = nltk.pos_tag(txt_list)
            
            newwordList = []
            # Merge possible consecutive features ("Phone" "Battery" ==> "PhoneBattery")
            # Condition for merge: consecutive nouns 
            flag = 0
            for i in range(0,len(taggedList)-1):
                if(taggedList[i][1]=="NN" and taggedList[i+1][1]=="NN"):
                    newwordList.append(taggedList[i][0] + taggedList[i+1][0])
                    flag=1
                else:
                    if(flag==1):
                        flag=0
                        continue
                    newwordList.append(taggedList[i][0])
                    if(i==len(taggedList)-2):
                        newwordList.append(taggedList[i+1][0])
            finaltxt = ' '.join(newwordList)
        
            # Re-tag the words list to identify the newly combined words together
            taggedList = nltk.pos_tag(newwordList)
            
            # Use dependancy analysis to parse and extract features + descriptors
            doc = self.nlp(finaltxt)
            dep_node = []
            try:
                for dep_edge in doc.sentences[0].dependencies:
                    dep_node.append([dep_edge[2].text, dep_edge[0].id, dep_edge[1]])
                for i in range(0, len(dep_node)):
                    if (int(dep_node[i][1]) != 0):
                        dep_node[i][1] = newwordList[(int(dep_node[i][1]) - 1)]
            except:
                pass;
            
            # Selection of final features + descriptors
            featureList = []
            categories = []
            for i in taggedList:
                if(i[1]=='JJ' or i[1]=='NN' or i[1]=='JJR' or i[1]=='NNS' or i[1]=='RB'):
                    featureList.append(list(i))
                    categories.append(i[0])
            fcluster = []
            for feat in featureList:
                descriptors = []
                for j in dep_node:
                    #if the feature or the id matches
                    #j[0] --> feature, j[1] --> id, j[2] --> type of word
                    if((j[0]==feat[0] or j[1]==feat[0]) and (j[2] in [
                        # Different types of words that are identified as potential features
                        "nsubj",
                        "acl:relcl",
                        "obj",
                        "dobj",
                        "agent",
                        "advmod",
                        "amod",
                        "neg",
                        "prep_of",
                        "acomp",
                        "xcomp",
                        "compound"
                    ])):
                        if(j[0]==feat[0]):
                            descriptors.append(j[1])
                        else:
                            descriptors.append(j[0])
                fcluster.append([feat[0], descriptors])
            print(fcluster) 
            
            retlist.append(fcluster)
        return retlist;

    def do_extraction(self, df, feat_count, feat_sent, content_str = "Content"):
        """
        Given a dataframe containing reviews, extract features and their descriptors
        The output consists of 2 dictionary: one will contain the frequency of each feature
        while the other will contain the features and their descriptors.

        Parameters:
        df : pandas dataframe
            The dataframe containing the review to do feature extraction on.
        feat_count : dictionary
            A dictionary that will keep track of frequency of occurrence of the features.
        feat_sent: dictionary
            A dictionary that will keep track of the descriptors for each feature.
        content_str: str
            The column name of the column containing the review content in dataframe. If not
            specified, it will be 'Content' by default.
        """
        idx = 0;
        # Replace empty reviews with nan's for removal
        df[content_str].replace('', np.nan, inplace=True)
        df.dropna(subset=[content_str], inplace=True)
        
        review_list = df[content_str].to_list()
         
        print(" Processing : " , df.shape[0], "rows of data")

        #Feature Extraction for each review
        for review in tqdm(review_list):
            print("Review Number : ", idx);
            
            # Convert review to all lowercase
            review = review.lower()
            
            # Merge hyphenated words
            separate = review.split('-')
            review = ''.join(separate)
            
            idx += 1;
            # Perform Feature Extraction
            if idx >= df.shape[0]:
                break;
            try:
                output = self.feature_extraction(review);
            except:
                pass;
            
            # Combine the features extracted to the overall collection in feat_sent
            for sent in output:
                for pair in sent:
                    print(pair)
                    # If feature already exists in feat_sent, append the descriptors 
                    if pair[0] in feat_sent:
                        if pair[1] is not None:
                            flist = feat_sent[pair[0]]
                            if isinstance(pair[1], list):
                                for i in pair[1]:
                                    flist.append(i)
                            else:
                                flist.append(pair[1])
                            feat_sent[pair[0]] = flist;
                    # If feature does not exist, add feature as a new key and its descriptors as the respective value
                    else:
                        if pair[1] is not None:
                            flist = pair[1]
                        else:
                            flist = list()
                        feat_sent[pair[0]] = flist;
                    
                    #Update occurrence count of feature in feat_count
                    if pair[0] in feat_count:
                        feat_count[pair[0]] = feat_count[pair[0]] + 1;
                    else:
                        feat_count[pair[0]] = 1
        
        #remove punctuation features for sentiment analysis
        for a in feat_count.copy():
            if a in string.punctuation:
                del feat_count[a]
        for a in feat_sent.copy():
            if a in string.punctuation:
                del feat_sent[a]
        return feat_count, feat_sent;

    def get_sentiment(self, feat_count, feat_sent):
        """
        Calculates average sentiment score of each feature based on its descriptors
        This function will output 2 dataframes: 
            final_sent --> columns: Feature, String of Descriptors, Sentiment Score, Frequency of Feature
            desc_df --> columns: Feature, Descriptor
        
        Parameters:
        feat_count: dictionary
            This dictionary should have each feature as a key and its frequency of occurrence as the respective value
        fea_sent: dictionary
            This dictionary should have each feature as a key and a string of its descriptors, each seperated by comma, as the respective value
        """
        # Initialise dictionary to keep track of average sentiment score for each feature
        sentiment_score = dict()

        # Initialise Singlish Dictionary
        singlish = pd.read_csv("singlish_sent2.csv")
        singlish.columns = ["word", "sent"]
        singlish = dict(zip(singlish.word,singlish.sent))
        print("Singlish dict initialised")

        # Delete features with no descriptors
        cob = feat_sent.copy()
        for feat in cob.keys():
            if cob[feat] == []:
                del feat_sent[feat]
            else:
                feat_sent[feat] = [str(x) for x in feat_sent[feat]]
                feat_sent[feat] = ', '.join(feat_sent[feat])

        # Define a new df to track at descriptor level
        dcolumns = ["Feature", "Descriptor", "Sentiment", "Freq of Feature"]
        desc_df = pd.DataFrame(columns=dcolumns)
        
        # Run pre-built sentiment score and take avg of all descriptors
        for f in tqdm(feat_sent.keys()):
            print("Calculating Sentiment for: ", f);
            print(feat_sent[f].split(" ,"))
            ssum = 0;
            length = 0;
            for g in feat_sent[f].split(" ,"):
                length += 1;
                # Check for word in Singlish Dictionary, if present, take the Singlish score, else move to stanza
                if g in singlish.keys():
                    ssum += singlish[g]
                else:
                    try:
                        doc = self.nlp(g);
                        for i in doc.sentences:
                                ssum += i.sentiment;
                                new_row = [[f, g, i.sentiment, feat_count[f]]]
                                desc_df = desc_df.append(pd.DataFrame(new_row, columns=dcolumns))
                    except:
                        pass;
            # Average sentiment score for each feature = Sum of score of all descriptors / Number of descriptors
            sentiment_score[f] = ssum / length;
            
        # Convert feature count to dataframe and sort by frequency in descending order (adf)
        adf = pd.DataFrame.from_dict(feat_count, orient='index', columns=['Freq'])
        adf.sort_values(by="Freq", ascending=False, inplace = True)

        # Convert sentiment score and descriptors to dataframe (avg_sent and desc_words respectively)
        avg_sent = pd.DataFrame.from_dict(sentiment_score, orient='index', columns=["Avg_sent"])
        desc_words = pd.DataFrame.from_dict(feat_sent, orient="index", columns=["Descriptors"])
        
        # Merge the Sentiment Score with Descriptors into one dataframe (avg_sent)
        avg_sent = avg_sent.merge(desc_words, left_index=True, right_index=True)
        
        # Merge Frequency and with avg_sent to obtain final output of dataframe (final_sent) and sort by frequency in descending order
        final_sent = avg_sent.merge(adf, left_index=True, right_index=True)
        final_sent.sort_values(by="Freq", ascending=False, inplace=True)
        print(final_sent.columns)
        return final_sent, desc_df;

    def run_feat_extraction(self, df, content_str="Content"):
        """
        A simple function that runs feature extraction and sentiment calculation for the reviews. Dataframe output from sentiment analysis 
        will be pushed to Firebase.

        Parameters:
        df : dataframe
            A dataframe containing the reviews to undergo feature extraction and sentiment analysis.
        content_str : str
            The column name of the column containing the review content in dataframe. If not secified, it will be 'Content' by default.
        """
        # rdr = pd.read_csv('../../output/scraped-ns/cmpb.csv')
        # fdr = pd.read_csv("../../output/corpus.csv")

        a = dict()
        b = dict()
        a, b = self.do_extraction(df, a, b, content_str)
        fin, desc = self.get_sentiment(a, b)

        # fin.to_csv("fin.csv")
        # desc.to_csv("desc.csv")
        print("Code completed")

        fin.reset_index(inplace=True)
        # print(fin)
        # fin.drop("Unnamed: 0", axis= 1, inplace=True)
        fin.columns = ["Feature", "Avg_sent", "Descriptors", "Freq"]
        rec_fin = fin.to_dict('records')
        today = str(date.today())
        collection_name = "feat_sent" + today
        feat_ref = self.db.collection(collection_name)

        for i in rec_fin:
            feat_ref.document(i["Feature"]).set(i)
            print("Pushed processed data for :", i["Feature"])

    def run_entityextraction(self, data_list):
        
        # Set nlp's settings
        nlp = spacy.load("en_core_web_sm")
        ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": True}).from_disk("patterns.jsonl")
        
        # Set displacy's options
        colors = {"TRAINING": "#EEE2DF", "BMT": "#ADA8B6", "ICT": "#DCABDF", "IPPT": "#bfe1d9", "RT/IPT": "#D0C4DF", "MEDICAL": "#EE8434", "CAMP": "#CBEFB6", "FCC": "#DDDFDF", "CMPB": "#717ec3", "PORTAL": "#635d5c", "SERVICE": "#9b1d20", "LOCATION": "#fbba72"}
        options = {"ents": ["TRAINING", "BMT", "ICT", "IPPT", "RT/IPT", "MEDICAL", "CAMP", "FCC", "CMPB", "PORTAL", "SERVICE", "LOCATION"], "colors": colors}
        
        # Run entity extraction and render results
        cleaned1 = [x for x in data_list if x] # get rid of empty '' in list 
        cleaned2 = map(lambda s: s.replace('\n', ' '), cleaned1) # get rid of '\n' in the strings within the list
        data_string = '\n\n'.join([str(review) for review in cleaned2])
        print("\nData as string:")
        print(data_string)

        docx = nlp(data_string)

        html = displacy.render(docx, style="ent", page=True, options=options) # output html file here for now
        #print("HTML markup: ", html)
        with open("entitiesextracted.html", "w+", encoding="utf-8") as fp:
            fp.write(html)
            fp.close()

        entities = [(ent.text, ent.label_) for ent in docx.ents]

        return html, entities

    def intersect_features(self, featuresDF, entities):
        entitiesDF = pd.DataFrame(entities, columns=['Feature', 'Entity'])
        entitiesDF['Feature'] = entitiesDF['Feature'].str.lower()
        entitiesDF = entitiesDF.drop_duplicates()

        final = pd.merge(entitiesDF, featuresDF, on = 'Feature', how='inner')#.drop(columns=['Unnamed: 0']) #replace test with corpus-refined-features
        mergedDF = final[final['Entity'].isin(['MEDICAL', 'SERVICE', 'CMPB', 'BMT', 'ICT', 'IPPT', 'RT/IPT', 'FCC', 'PORTAL', 'CAMP', 'TRAINING', 'LOCATION'])]
        print(mergedDF)
        return mergedDF

    def runscraping(self):
        self.get_google_reviews("https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1", "CMPB")
        logger.info("Scraped Google Reviews for CMPB")

        self.get_google_reviews("https://www.google.com/maps/place/Bedok+FCC+in+Bedok+Camp+2/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da22d0dd021831:0x72f9d7d2f5dfe24d!8m2!3d1.3168752!4d103.954114!9m1!1b1", "BedokFCC")
        logger.info("Scraped Google Reviews for BedokFCC")

        self.get_google_reviews("https://www.google.com/maps/place/Maju+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da114548788fbf:0xe7b1351cb138a2dc!8m2!3d1.3297773!4d103.7717872!9m1!1b1", "MajuFCC")
        logger.info("Scraped Google Reviews for MajuFCC")

        self.get_google_reviews("https://www.google.com/maps/place/Kranji+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da11ae095fac6f:0xfbe6c8bc26249e47!8m2!3d1.400557!4d103.7416568!9m1!1b1", "KranjiFCC")
        logger.info("Scraped Google Reviews for KranjiFCC")

        self.get_google_reviews("https://www.google.com/maps/place/Clementi+Camp/@1.3170913,103.9013688,13z/data=!4m11!1m2!2m1!1sMedical+Center+NS!3m7!1s0x31da11a69aa0ac43:0xca88158b0ea52b74!8m2!3d1.3290056!4d103.7629462!9m1!1b1!15sChFNZWRpY2FsIENlbnRlciBOU1omChFtZWRpY2FsIGNlbnRlciBucyIRbWVkaWNhbCBjZW50ZXIgbnOSAQRjYW1w", "ClementiCamp")
        logger.info("Scraped Google Reviews for ClementiCamp")
        

        # Hardwarezone
        self.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/ffi-need-go-every-year-after-35-a-4109332.html", "FFI");
        logger.info("Scraped " + "FFI") 

        self.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/pes-d-dilemma-3709993.html", "Pes_D_dilemma");
        logger.info("Scraped " + "Pes_D_dilemma") 

        self.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/after-40-years-old-still-need-go-back-reservist-5111453.html", "reservist");
        logger.info("Scraped " + "reservist") 

        self.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html", "IPPT_IPT_RT");
        logger.info("Scraped " + "IPPT_IPT_RT") 

        self.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/cmpb-enlistment-medical-checkup-tomorrow-no-form-healthbooklet-how-3623665.html", "CMPB");
        logger.info("Scraped " + "CMPB") 

        # scrape reddit
        d = date.today() - timedelta(days=365)
        unixtime = time.mktime(d.timetuple())

        self.get_reddit(start_date = unixtime, limit_amt=10)
        print("Scraped Reddit" )

    def runprocessing(self):
        data = self.get_all_data()
        data = pd.DataFrame(data, columns=["Content"])
        self.run_feat_extraction(data)


def main():
    print("Starting DSTA Web Scraper")
    scraper = DSTA_Service_Delivery()
    scraper.initialiseDB()

    # Test greview
    # scraper.get_google_reviews("https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1", "CMPB")

    # Test harewarezone
    # scraper.get_harwarezone();
    # Test reddit
    # scraper.get_reddit();
'''
    # GR
    scraper.get_google_reviews("https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1", "CMPB")
    print("Scraped Google Reviews for CMPB")

    scraper.get_google_reviews("https://www.google.com/maps/place/Bedok+FCC+in+Bedok+Camp+2/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da22d0dd021831:0x72f9d7d2f5dfe24d!8m2!3d1.3168752!4d103.954114!9m1!1b1", "BedokFCC")
    print("Scraped Google Reviews for ", "BedokFCC")

    scraper.get_google_reviews("https://www.google.com/maps/place/Maju+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da114548788fbf:0xe7b1351cb138a2dc!8m2!3d1.3297773!4d103.7717872!9m1!1b1", "MajuFCC")
    print("Scraped Google Reviews for ", "MajuFCC")

    scraper.get_google_reviews("https://www.google.com/maps/place/Kranji+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da11ae095fac6f:0xfbe6c8bc26249e47!8m2!3d1.400557!4d103.7416568!9m1!1b1", "KranjiFCC")
    print("Scraped Google Reviews for ", "KranjiFCC")

    scraper.get_google_reviews("https://www.google.com/maps/place/Clementi+Camp/@1.3170913,103.9013688,13z/data=!4m11!1m2!2m1!1sMedical+Center+NS!3m7!1s0x31da11a69aa0ac43:0xca88158b0ea52b74!8m2!3d1.3290056!4d103.7629462!9m1!1b1!15sChFNZWRpY2FsIENlbnRlciBOU1omChFtZWRpY2FsIGNlbnRlciBucyIRbWVkaWNhbCBjZW50ZXIgbnOSAQRjYW1w", "ClementiCamp")
    print("Scraped Google Reviews for ", "ClementiCamp")
    

    # Hardwarezone
    scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/ffi-need-go-every-year-after-35-a-4109332.html", "FFI");
    print("Scraped " + "FFI") 

    scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/pes-d-dilemma-3709993.html", "Pes_D_dilemma");
    print("Scraped " + "Pes_D_dilemma") 

    scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/after-40-years-old-still-need-go-back-reservist-5111453.html", "reservist");
    print("Scraped " + "reservist") 

    scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html", "IPPT_IPT_RT");
    print("Scraped " + "IPPT_IPT_RT") 

    scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/cmpb-enlistment-medical-checkup-tomorrow-no-form-healthbooklet-how-3623665.html", "CMPB");
    print("Scraped " + "CMPB") 
'''
    # scrape reddit
    #d = date.today() - timedelta(days=365)
    #unixtime = time.mktime(d.timetuple())

    #scraper.get_reddit(start_date = unixtime, limit_amt=10)
    #print("Scraped Reddit")
'''
    # Run processing code:
    data = scraper.get_all_data()
    html, entities = scraper.run_entityextraction(data)

    data = pd.DataFrame(data, columns=["Content"])
    features = scraper.run_feat_extraction(data)
    scraper.intersect_features(features, entities)
'''
if __name__ == '__main__':
    main()
    print("Completed all processes. Will exit code now")