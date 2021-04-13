from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
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
import string

class DSTA_Service_Delivery():

	def __init__(self):
		"""
		Upon initialising this class, download natural language processing packages' (i.e. NLTK, 
		Stanza and spaCy) dependencies, initialise their pipelines, and configure Chrome's webdriver needed
		for webscraping using Selenium.

		For the pipelines, we rely on pre-trained English NLP components. At this stage, they contain:
		stanza_nlp :
		spacy_nlp : # TO ADD
		"""
		# Download NLP packages' dependencies
		stanza.download("en")
		nltk.download("stopwords")
		nltk.download("punkt")
		nltk.download("averaged_perceptron_tagger")

		# Initialise NLP pipelines
		self.stanza_nlp = stanza.Pipeline("en")
		self.spacy_nlp = spacy.load("en_core_web_sm")

		# Configure Chrome webdriver
		self.chrome_options = Options()
		self.chrome_options.add_argument("--headless")
		self.chrome_options.add_argument("--no-sandbox")
		self.chrome_options.add_argument("--disable-gpu")
		self.chrome_options.add_argument("--disable-dev-shm-usage")
		self.chrome_options.add_argument("--disable-software-rasterizer")
		self.chrome_prefs = {}
		self.chrome_options.experimental_options["prefs"] = self.chrome_prefs
		self.chrome_prefs["profile.default_content_settings"] = {"images": 2}

		# Dictionary of replacements for feature extraction
		self.replacements = {'/':'_', '-':'_','u':'you', 'im': "i'm", 'tbh':'to be honest', 'dk': "dont' know", 'dont': "don't", 'Ã°Ã¿â„¢ÂÃ°Ã¿ÂÂ»':'', 'imo': 'in my opinion', 'n"t':'not',"'s":'is'}

		# Stop words from Stanza
		self.stop_words = stopwords.words('english')

	def initialiseDB(self):
		"""
		Initialise Firebase app by providing administrative credentials in a JSON file, fbadmin.json.
		"""
		cred = credentials.Certificate("fbadmin.json")
		# firebase_admin.initialize_app(cred)
		self.db = firestore.client()
	
	def get_google_reviews(self, location="CMPB", url="https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1"):
		"""
		Scrape data from the Google Reviews of a specified location, and push it to Firebase.
		The data scraped include the text content of the review, the timestamp of scraping, an 
		assigned ID number to the review, and the location of the reviewed place.

		Parameters:
		location : str
			The name of the location whose Google Review is to be scraped (default is "CMPB")
		url : str
			The URL of the Google Review page to be scraped (default is CMPB's Google Maps reviews)
		"""
		# Load the page we want to scrape
		driver = webdriver.Chrome(options=self.chrome_options)
		driver.get(url)
		delay = 3
		try:
			WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, "content-container")))
		except TimeoutException:
			print("Loading took too much time!")
	 
		# Get the number of reviews currently loaded and the stated total number of reviews
		time.sleep(3)
		loaded_count = len(driver.find_elements_by_xpath("//div[@class='section-review ripple-container']"))
		stated_count = driver.find_element_by_xpath("//*[@id='pane']/div/div[1]/div/div/div[3]/div[2]/div/div[2]/div[2]").text.split()[0]
		stated_count = int(stated_count)

		# Scroll to the bottom of the pane until all reviews are loaded
		while loaded_count < stated_count:
			driver.find_element_by_xpath("//div[contains(@class,'section-loading-spinner')]").location_once_scrolled_into_view
			WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='section-loading-overlay-spinner'][@style='display:none']")))
			loaded_count = len(driver.find_elements_by_class_name("section-review-content"))

		# Get body text of each review, click on More if needed, and remove review if body text is empty
		more_buttons = driver.find_elements_by_class_name("section-expand-review")
		for button in more_buttons:
			button.click()
		all_content_elements = driver.find_elements_by_class_name("section-review-review-content")
		all_content_unclean = [i.text for i in all_content_elements]
		all_content = [i for i in all_content_unclean if i]
		
		# Get each review's date of posting
		#all_postdates_elements = driver.find_elements_by_class_name("section-review-publish-date")
		#all_postdates = [i.text for i in all_postdates_elements] # Considerations: just now, a minute ago, 3 minutes ago, an hour ago, 2 hours ago, a day ago, 5 days ago, a week ago, 2 weeks ago, a month ago, 7 months ago, a year ago, 3 years ago

		time.sleep(2)
		driver.quit()
		
		# Push to Firebase if the collection's last pushed data doesn't exist in our above scraped content
		gr_ref = self.db.collection(u"google_reviews")
		latest_post = gr_ref.where(u"location", u"==", location).order_by(u"timestamp", direction=firestore.firestore.Query.DESCENDING).order_by(u"id").limit(1).stream()
		latest_post = [i.to_dict() for i in latest_post]
		
		has_latest = False
		try:
			print(latest_post[0]["content"])
			has_latest = True
		except:
			pass

		idcount = 1
		now = datetime.now()
		now_str = str(now.strftime("%d/%m/%Y %H:%M:%S"))

		for c in all_content:
			if has_latest and c == latest_post[0]["content"]:
				break
			pushref = gr_ref.add({
				"id": idcount,
				"timestamp": now_str,
				"content": c,
				"location": location
			})
			print("Pushed", pushref)
			idcount += 1
		print("\nGoogle Review data for", location, "has been scraped and stored.\n")
		
	def get_hardwarezone(self, forum="NSKnowledgeBase", url="https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html", maxpages=30):
		"""
		Scrape data from a specific HardwareZone forum, and push it to Firebase.
		The data scraped include the text content of the review, the timestamp of scraping, an 
		assigned ID number to the review, and the location of the reviewed place.

		Parameters:
		forum : str
			The name of the forum whose posts are to be scraped (default is "NSKnowledgeBase")
		url : str
			The URL of the first HardwareZone page to be scraped (default is National Service Knowledge-Base's URL)
		maxpages : int
			Maximum number of pages in advance to scrape, not inclusive of current page, until there are no more pages left (default is 30)
		"""
		# Load the page we want to scrape
		driver = webdriver.Chrome(options=self.chrome_options)
		driver.get(url)
		time.sleep(10)

		# Get the title of the forum
		forum_title = driver.find_element_by_class_name("p-title-value").text
		print("Forum:", forum, "-", forum_title)

		# Get a list of all the posts' content, message it is replying to (if any), and dates
		all_content = []
		#all_repliedtos = []
		#all_postdates = []        
		
		curr_page = 0
		while curr_page <= maxpages:
			print("Page", curr_page + 1)
			posts = driver.find_elements_by_class_name("bbWrapper")
			#dates = driver.find_elements_by_class_name("u-dt")[1:]
			
			# For every post, check if quote(s) exist; if present, it indicates the post is responding to the quoted portion of an earlier post
			for i in range(len(posts)):
				p = posts[i]
				ptext = p.text
				quotes = p.find_elements_by_class_name("bbCodeBlock.bbCodeBlock--expandable.bbCodeBlock--quote.js-expandWatch")
				#qtext = ""
				for q in quotes:
					ptext = ptext.replace(q.text, "")
					#qtext += q.text + " "
				all_content.append(self.addPunctuation(ptext).strip())
				print("Scraped", i, "HWZ post")
				#all_repliedtos.append(qtext)
			
			#for d in dates:
			#    all_postdates.append(d.text)

			# Does the Next page button exist? If no, the while loop breaks here.
			list_of_nextbuttons = driver.find_elements_by_class_name("pageNav-jump.pageNav-jump--next")
			print("Next button:", list_of_nextbuttons)

			on_lastpage = len(list_of_nextbuttons) == 0
			if on_lastpage:
				print("You've reached the forum's last page!")
				break

			# If yes, go to next page as long as curr_page <= maxpages and repeat the scraping process
			curr_page += 1
			list_of_nextbuttons[0].click()
			
		driver.quit()
		
		# Push to Firebase if the collection's last pushed data doesn't exist in our above scraped content
		hz_ref = self.db.collection(u"hardwarezone")
		latest_post = hz_ref.where(u"forum", u"==", forum_title).order_by(u"timestamp", direction=firestore.firestore.Query.DESCENDING).order_by(u"id").limit(1).stream()
		latest_post = [i.to_dict() for i in latest_post]
		
		has_latest = False
		try:
			print(latest_post[0]["content"])
			has_latest = True
		except:
			pass

		idcount = 1
		now = datetime.now()
		now_str = str(now.strftime("%d/%m/%Y %H:%M:%S"))

		for c in all_content:
			if has_latest and c == latest_post[0]["content"]:
				break
			pushref = hz_ref.add({
				"id": idcount,
				"timestamp": now_str,
				"content": c,
				"forum": forum
			})
			print("Pushed", pushref)
			idcount += 1
		
		print("\nHardwareZone data for", forum, "has been scraped and stored.\n")
		
	def get_reddit(self, subreddit="NationalServiceSG", startdate=1612108800, limit=2000):
		"""
		Scrape data from a specified Reddit forum, and push it to Firebase. The data scraped include the ___. 
		Contains inner function, subsmissions_pushshift_praw().

		This scraping is conducted using the Reddit APIs: PRAW and Pushshift. 
		For more information on PRAW, see: https://github.com/praw-dev/praw 
		For more information on Pushshift, see: https://github.com/pushshift/api

		Parameters:
		subreddit : str
			The name of the subreddit whose posts and comments are to be scraped (default is "NationalServiceSG")
		startdate : int
			The Unix timestamp for the start date from which posts should be scraped (default is 1612108800, i.e. Feb 1 2021)
		limit : int
			The maximum number of posts to be scraped (default is 2000)
		"""

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
				self.progress(i, len(returned_submissions)-1, status='Collecting posts')

				# Take the ID, fetch the PRAW submission object, and append to our list
				praw_submission = reddit.submission(id=submission['id'])
				matching_praw_submissions.append(praw_submission)
				i += 1
			
			# Return all PRAW submissions that were obtained.
			return matching_praw_submissions

		reddit = praw.Reddit(client_id="kQoyoJ9Ag4JxTQ", client_secret="fPR3EGxAsC4ERoPHW4HNfxaMsle5Nw", user_agent="nsscraper")
		extracted_posts = submissions_pushshift_praw(self, subreddit=subreddit, reddit=reddit, start=startdate, limit=limit)

		# Get posts in this particular format [unique ID, title, body text, date created]
		all_posts = []
		for p in extracted_posts:
			all_posts.append([p.id, p.title, p.selftext, int(p.created)])

		# Get comments of posts in this particular format [body text, date created]
		all_comments = []
		i = 0
		for p in all_posts:
			self.progress(i, len(all_posts)-1, status="Collecting comments")
			post_id = p[0]
			post = reddit.submission(id=post_id)

			# Ensure all comments in the web page are loaded before getting them
			post.comments.replace_more(limit=0) 
			for c in post.comments.list():
				all_comments.append([c.body, int(c.created)])
			i += 1

		print("\nPre-cleaning ==========================================")
		print("\nposts:", len(all_posts), "\n", all_posts[:5])
		print("\ncomments:", len(all_comments), "\n", all_comments[:5])
		
		# We don't need posts and comments whose body text says [removed] or [deleted]
		undesirable_content = ["[removed]", "[deleted]"]
		all_posts = [i for i in all_posts if i[2] not in undesirable_content]
		all_comments = [i for i in all_comments if i[0] not in undesirable_content]

		# Further clean posts and comments to get lists of just those. Steps include:
			# Add a full stop to the end of strings if needed, as punctuation affects NLTK's and spaCy's POS taggers
			# Merge title and body text together for posts to maintain context
			# Remove leading and trailing spaces
		posts, postdates = [], []
		for post in all_posts:
			title, body, date = post[1], post[2], post[3]
			title_and_body = " ".join([self.addPunctuation(title), self.addPunctuation(body)])
			posts.append(title_and_body.strip())
			postdates.append(date)
		
		comments, commentdates = [], []
		for comment in all_comments:
			body, date = comment[0], comment[1]
			comments.append(self.addPunctuation(body).strip())
			commentdates.append(date)

		print("\nPost-cleaning ==========================================")
		print("\nposts:", len(posts), "\n", posts[:5], "\n\npost dates:", len(postdates), "\n", postdates[:5])
		print("\ncomments:", len(comments), "\n", comments[:5], "\n\ncomment dates:", len(commentdates), "\n", commentdates[:5])
		
		# For posts, push to Firebase if the collection's last pushed data doesn't exist in our above scraped content
		rd_ref = self.db.collection(u'reddit_posts')
		latest_post = rd_ref.order_by(u"timestamp", direction=firestore.firestore.Query.DESCENDING).order_by(u"id").limit(1).stream()
		latest_post = [i.to_dict() for i in latest_post]
		
		has_latest = False
		try:
			print(latest_post[0]["content"])
			has_latest = True
		except:
			pass

		idcount = 1
		now = datetime.now()
		now_str = str(now.strftime("%d/%m/%Y %H:%M:%S"))
		
		for i in range(len(posts)):
			p = posts[i]
			if has_latest and p == latest_post[0]["content"]:
				break
			pushref = rd_ref.add({
				"id": idcount,
				"timestamp": now_str,
				"content": p,
				"subreddit": subreddit,
				"created": postdates[i]
			})
			print("Pushed", pushref)
			idcount += 1

		print("\nReddit's posts data for", subreddit, "has been scraped and stored.\n")
		
		# For comments, push to Firebase if the collection's last pushed data doesn't exist in our above scraped content
		rdc_ref = self.db.collection(u'reddit_comments')
		latest_post = rdc_ref.order_by(u"timestamp", direction=firestore.firestore.Query.DESCENDING).order_by(u"id").limit(1).stream()
		latest_post = [i.to_dict() for i in latest_post]
		
		has_latest = False
		try:
			print(latest_post[0]["content"])
			has_latest = True
		except:
			pass

		idcount = 1
		now = datetime.now()
		now_str = str(now.strftime("%d/%m/%Y %H:%M:%S"))

		for i in range(len(comments)):
			c = comments[i]
			if has_latest and c == latest_post[0]["content"]:
				break
			pushref = rdc_ref.add({
				"id": idcount,
				"timestamp": now_str,
				"content": c,
				"subreddit": subreddit,
				"created": commentdates[i]
			})
			print("Pushed", pushref)
			idcount += 1
		
		print("\nReddit's comments data for", subreddit, "has been scraped and stored.\n")
		
	def progress(self, count, total, status=''):
		"""
		Progress bar that's added to some of the functions. 
		As suggested by Rom Ruben. (See: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)
		"""
		bar_len = 60
		filled_len = int(round(bar_len * count / float(total)))
		percents = round(100.0 * count / float(total), 1)
		bar = '=' * filled_len + '-' * (bar_len - filled_len)
		sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
		sys.stdout.flush()

	def addPunctuation(self, sentence, punctuation="."):
		"""
		Method to add a punctuation to the end of a given string to end its sentence, when you don't know whether
		such a punctuation already exists. Default is a full stop unless otherwise specified.

		Parameters:
		sentence : str
			A string whose sentence you're not sure is already complete, but want it complete.
		punctuation : str
			Punctuation to add to the above sentence.
		"""
		if sentence == "":
			return sentence
		if sentence[-1] not in string.punctuation:
			return sentence + punctuation
		return sentence

	def get_all_contentdata(self, separate=False):
		"""
		Reads all content data from Firebase. If separate=False, it returns {"general": list of text data from all 3 sources}.
		If separate=True, it returns {"general": list of text data from HardwareZone and Reddit, "reviews": list of text data from Google Reviews}

		Parameters:
		separate : bool
			Determines whether the returned list of data is split into Google Reviews and HardwareZone/Reddit (default is False)
		"""
		data = []

		hz_ref = self.db.collection(u"hardwarezone")
		try:
			hzdata = hz_ref.get()
			for entry in hzdata:
				data.append(entry.to_dict()["content"])
		except:
			print("Error getting Hardwarezone Posts")
		
		rd_ref = self.db.collection(u"reddit_posts")
		try:
			rddata = rd_ref.get()
			for entry in rddata:
				data.append(entry.to_dict()["content"])
		except:
			print("Error getting Reddit Posts")

		rdc_ref = self.db.collection(u"reddit_comments")
		try:
			rdcdata = rdc_ref.get()
			for entry in rdcdata:
				data.append(entry.to_dict()["content"])
		except:
			print("Error getting Reddit Comments")

		gdata = []
		gr_ref = self.db.collection(u"google_reviews")
		try:
			gr = gr_ref.get()
			for entry in gr:
				gdata.append(entry.to_dict()["content"])
		except:
			print("Error getting Google Reviews")

		if separate:
			return {"reviews": gdata, "general": data}
		else:
			return {"general": data + gdata}

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
			if '/' in words:
				words = words.replace('/','_')
				replaced.append(words)
			if '\\' in words:
				words = words.replace('/','_')
				replaced.append(words)
			if '-' in words:
				words = words.replace('-','_')
				replaced.append(words)
			else:
				replaced.append(words)
		txt = ' '.join(replaced)

		# Add fullstop to the end of the review and paragraph
		txt += '.'
		txt = txt.replace("\n", ".")

		# Tokenise para into sentences
		sentList = nltk.sent_tokenize(txt)

		#final list to be returned
		retlist = []

		# For each sentence
		for line in sentList:
			line = line.replace('.','')
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
			doc = self.stanza_nlp(finaltxt)
			dep_node = []
			try:
				for dep_edge in doc.sentences[0].dependencies:
					dep_node.append([dep_edge[2].text, dep_edge[0].id, dep_edge[1]])
				for i in range(0, len(dep_node)):
					if (int(dep_node[i][1]) != 0):
						dep_node[i][1] = newwordList[(int(dep_node[i][1]) - 1)]
			except:
				pass
			
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
		return retlist

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
		idx = 0
		# Replace empty reviews with nan's for removal
		df[content_str].replace('', np.nan, inplace=True)
		df.dropna(subset=[content_str], inplace=True)
		
		review_list = df[content_str].to_list()
		 
		print(" Processing : " , df.shape[0], "rows of data")

		#Feature Extraction for each review
		for review in tqdm(review_list):
			print("\nReview Number : ", idx)
			
			# Convert review to all lowercase
			review = review.lower()
			
			# Merge hyphenated words
			separate = review.split('-')
			review = ''.join(separate)
			
			idx += 1
			# Perform Feature Extraction
			if idx >= df.shape[0]:
				break
			#try:
			#    output = self.feature_extraction(review)
			#except:
			#    pass
			output = self.feature_extraction(review)
			# Combine the features extracted to the overall collection in feat_sent
			print('Combining Features and Descriptors')
			counter = 1 #counter to make sure loop is running
			for sent in output:
				print('Features for Review ' + str(counter))
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
							feat_sent[pair[0]] = flist
					# If feature does not exist, add feature as a new key and its descriptors as the respective value
					else:
						if pair[1] is not None:
							flist = pair[1]
						else:
							flist = list()
						feat_sent[pair[0]] = flist
					
					#Update occurrence count of feature in feat_count
					print('Updating Count')
					if pair[0] in feat_count:
						feat_count[pair[0]] = feat_count[pair[0]] + 1
					else:
						feat_count[pair[0]] = 1
				counter += 1
		#remove punctuation features for sentiment analysis
		print('Removing Punctuation')
		for a in feat_count.copy():
			if a in string.punctuation:
				del feat_count[a]
		for a in feat_sent.copy():
			if a in string.punctuation:
				del feat_sent[a]
		return feat_count, feat_sent

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
			print("\nCalculating Sentiment for: ", f)
			print(feat_sent[f].split(" ,"))
			ssum = 0
			length = 0
			des_list = []
			for g in feat_sent[f].split(" ,"):
				# Removal of stop words
				if g in self.stop_words:
					continue
				else:
					length += 1
					# Check for word in Singlish Dictionary, if present, take the Singlish score, else move to stanza
					if g in singlish.keys():
						ssum += singlish[g]
						des_list.append(g)
						new_row = [[f, g, singlish[g], feat_count[f]]]
						desc_df = desc_df.append(pd.DataFrame(new_row, columns=dcolumns))
					else:
						try:
							doc = self.stanza_nlp(g)
							for i in doc.sentences:
								#print(i.text)
								#print(i.sentiment)
								des_list.append(i.text)
								ssum += i.sentiment
								new_row = [[f, g, i.sentiment, feat_count[f]]]
								desc_df = desc_df.append(pd.DataFrame(new_row, columns=dcolumns))
						except:
							pass
			# Average sentiment score for each feature = Sum of score of all descriptors / Number of descriptors
			feat_sent[f] = ' ,'.join(des_list)
			if length != 0:
				sentiment_score[f] = ssum / length
			
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
		return final_sent, desc_df

	def run_feat_extraction(self, df, content_str="Content"):
		"""
		A simple function that runs feature extraction and sentiment calculation for the reviews. Dataframe output from sentiment analysis 
		will be returned for entity extraction and also pushed to Firebase.

		Parameters:
		df : dataframe
			A dataframe containing the reviews to undergo feature extraction and sentiment analysis.
		content_str : str
			The column name of the column containing the review content in dataframe. If not secified, it will be 'Content' by default.
		"""

		# Initialise 2 dictionaries: one to track feature count, one to keep features and descriptors
		feat_count = dict()
		feat_sent = dict()
		feat_count, feat_sent = self.do_extraction(df, feat_count, feat_sent, content_str)
		fin, desc = self.get_sentiment(feat_count, feat_sent)
		print("Code completed")

		# Push extracted features and descriptors to Firebase 
		fin.reset_index(inplace=True)
		fin.columns = ["Feature", "Avg_sent", "Descriptors", "Freq"]
		rec_fin = fin.to_dict('records')

		# Include time stamp 
		today = str(date.today())
		collection_name = "feat_sent" + today
		feat_ref = self.db.collection(collection_name)

		for i in range(len(rec_fin)):
			feature = rec_fin[i]
			print(str(i), 'Pushing processed data for :', feature["Feature"] )
			feat_ref.document(feature["Feature"]).set(feature)
			print(str(i), "Pushed processed data for :", feature["Feature"])
		return fin

	def run_entityextraction(self, data_list, entityrules="patterns.jsonl"):
		"""
		Identify and extracts entities and the respective feature from each review.
		This function will return a colour-coded html file that displays the feature and its respective entity at the review level.

		Parameters:
		data_list : pandas dataframe
			A dataframe containing the reviews to undergo entity extraction.
		entityrules : str

		"""
		# Set nlp's settings
		self.spacy_nlp.add_pipe("entity_ruler", config={"overwrite_ents": True}).from_disk(entityrules)
		
		# Set displacy's options
		colors = {"TRAINING": "#EEE2DF", "BMT": "#ADA8B6", "ICT": "#DCABDF", "IPPT": "#bfe1d9", "RT_IPT": "#D0C4DF", "MEDICAL": "#EE8434", "CAMP": "#CBEFB6", "FCC": "#DDDFDF", "CMPB": "#717ec3", "PORTAL": "#635d5c", "SERVICE": "#9b1d20", "LOCATION": "#fbba72"}
		options = {"ents": ["TRAINING", "BMT", "ICT", "IPPT", "RT_IPT", "MEDICAL", "CAMP", "FCC", "CMPB", "PORTAL", "SERVICE", "LOCATION"], "colors": colors}
		
		# Run entity extraction and render results
		cleaned1 = [x for x in data_list if x] # get rid of empty '' in list 
		cleaned2 = map(lambda s: s.replace('\n', ' '), cleaned1) # get rid of '\n' in the strings within the list
		data_string = '\n\n'.join([str(review) for review in cleaned2])
		print("\nData as string:")
		print(data_string)

		docx = self.spacy_nlp(data_string)

		# Output html file here 
		html = displacy.render(docx, style="ent", page=True, options=options) 
		with open("./templates/entitiesextracted.html", "w+", encoding="utf-8") as fp:
			fp.write(html)
			fp.close()

		# Output list of tuples that include all entities identifies and their corresponding entity
		entities = [(ent.text, ent.label_) for ent in docx.ents]

		return html, entities

	def intersect_features(self, featuresDF, entities):
		"""
		A simple function to merge all features extracted and those that are identified for entity extraction.

		Parameters:
		featuresDF : pandas dataframe
			This dataframe should include the all features extracted for all reviews under the column 'Feature'.
		entities : list of tuples 
			For each element, it should be in the format (feature, entity).
		"""
		# Converts the list of tuples into dataframe format
		entitiesDF = pd.DataFrame(entities, columns=['Feature', 'Entity'])
		entitiesDF['Feature'] = entitiesDF['Feature'].str.lower()
		entitiesDF = entitiesDF.drop_duplicates()

		# Merge all extracted features with those recognised as features with entities
		final = pd.merge(entitiesDF, featuresDF, on = 'Feature', how='inner')#.drop(columns=['Unnamed: 0']) #replace test with corpus-refined-features

		# Extract the entities identified that are in our pre-defined rules
		mergedDF = final[final['Entity'].isin(['MEDICAL', 'SERVICE', 'CMPB', 'BMT', 'ICT', 'IPPT', 'RT/IPT', 'FCC', 'PORTAL', 'CAMP', 'TRAINING', 'LOCATION'])]
		print(mergedDF)
		return mergedDF
	
	def entity_table(self, entitiesDF, sent = 'Avg_sent', entity = 'Entity', freq = 'Freq'):
		"""
		A simple function that calculates average sentiment of each sentiment by averaging the sentiment score of the features identified for each entity.
		Output dataframe will be pushed to Firebase.

		Parameters:
		entitiesDF : pandas dataframe
			A dataframe that should contain: average sentiment of each feature with corresponding entity, entity label for each feature
		sent : str
			Column name of the column containing the average sentiment of feature. If not specified, 'Avg_sent' will be used by default.
		entity : str
			Column name of the column containing the entity label of feature. If not specified, 'Entity' will be used by default.
		"""
		# Group the rows by entity, then calculate average sentiment score of entity group and frequency of occurence 
		sent_by_entity = entitiesDF.groupby(entity)[[sent]].mean()
		freq_by_entity = entitiesDF.groupby(entity)[[freq]].sum()
		entity_df = pd.concat([sent_by_entity, freq_by_entity],axis = 1)
		entity_df = entity_df.reset_index()
		entity_df.columns = ["Entity", "Avg_sent", "Freq"]


		# Push to Firebase
		today = str(date.today())
		collection_name = "sentiment_freq_by_entity" + today
		entity_ref = self.db.collection(collection_name)


		entity_dict = entity_df.to_dict('records')

		for i in entity_dict:
			print(i)
			entity_ref.document(i["Entity"]).set(i) 
			print("Pushed processed data for :", i["Entity"])
		return entity_df

	def sentence_level_sentiment(self):
		"""
		A function which breaks each review down into sentences and computes the average sentiment score by sentence level.
		This function takes these and pushes each sentence as well as its sentiment score as calculated.
		"""
		data = self.get_all_contentdata()["general"]
		data = pd.DataFrame(data, columns=["Content"])
		dfl = data["Content"].to_list()

		# Preprocess
		final_list = []
		for review in dfl:
			stop_words = set(stopwords.words('english'))
			new_txt_list = nltk.word_tokenize(review)
			wordsList = [w for w in new_txt_list if not w in stop_words]
			cleaned = " ".join(wordsList)
		#     print(cleaned)
			final_list.append(cleaned)

		singlish = pd.read_csv("singlish_sent2.csv")
		singlish.columns = ["word", "sent"]
		sd = singlish.to_dict('index')

		singlish_dict = dict()

		for i in sd.keys():
			j = sd[i]
		#     print(j)
			singlish_dict[j["word"]] = j["sent"]
		singlish_dict 
		count = 0

		review_level_s = []
		for review in final_list: 
			count += 1
			sentences = nltk.sent_tokenize(review)
			sent_list = []
			for sentence in sentences:
				len_sent = 0
				wordlist = nltk.word_tokenize(sentence)
				ssum = 0
				for word in wordlist:
					len_sent += 1
					
					if word in singlish_dict.keys():
						ssum += singlish_dict[word]
					else:
						doc = self.stanza_nlp(word)
						for i in doc.sentences:
							ssum += i.sentiment
				avg_sent = ssum / len_sent
				sent_list.append((sentence, avg_sent))
		#         print("Sent_lIst = ", sent_list)
			
			review_level_s.append(sent_list)
			# print(review, "\n", review_level_s, "\n\n")
			
		now = datetime.now()
		dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S"))

		id_count = 1
		list_of_dicts = []
		for review in review_level_s:
			sentence_count = 1
			for sentence in review:
				now = datetime.now()
				dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S"))
				return_dict = dict()
				return_dict["review_id"] = id_count
				return_dict["sentence_id"] = sentence_count
				return_dict["sentence_content"] = sentence[0]
				return_dict["sentence_sent"] = sentence[1]
				return_dict["timestamp"] = dt_string
				list_of_dicts.append(return_dict)
				sentence_count += 1
			id_count += 1

		print(list_of_dicts)

		today = str(date.today())

		collection_name = "sentence_level" + today
		sentence_ref = self.db.collection(collection_name)

		for i in list_of_dicts:
			sentence_ref.add(i)
			print("Pushed processed data for :", i["review_id"])

	def get_sentence_level(self):
		"""
		Getter method to get sentence level data as processed by the sentence_level_sentiment method.
		Returns: data
			A list of dict instances containing review id, sentence id within the review, the sentence content and timestamp

		"""
		collections = []
		for col in self.db.collections():
			if "sentence_level" in str(col.id):
				collections.append(str(col.id))

		collections = sorted(collections, reverse=True)

		data = []
		sent_ref = self.db.collection(collections[0])
		try:
			sdata = sent_ref.get()
			for entry in sdata:
				data.append(entry.to_dict())
		except:
			print("Error getting Sentence Level Reviews")

		return data

	def get_feat_data(self):
		"""
		Getter method to get the features and descriptors from firebase
		Returns: data
			A list of dict objects reflecting features, descriptors
		"""
		collections = []
		for col in self.db.collections():
			if "feat_sent" in str(col.id):
				collections.append(str(col.id))

		collections = sorted(collections, reverse=True)
		fref = self.db.collection(collections[0]).get()
		data = []
		for entry in fref:
			data.append(entry.to_dict());

		return data


	def get_entity_sent(self):
		"""
		Getter method to get the entity level sentiment score
		Returns: data
			A list of dict objects reflecting each entity's sentiment score
		"""
		collections = []
		for col in self.db.collections():
			if "sentiment_freq_by_entity" in str(col.id):
				collections.append(str(col.id))

		collections = sorted(collections, reverse=True)

		ges_ref = self.db.collection(collections[0]);
		data = []
		try:
			sdata = ges_ref.get()
			for entry in sdata:
				data.append(entry.to_dict())
		except:
			print("error getting entity level data");
		return data;

	def get_entity_sent_over_time(self):
		"""
		Getter method to get sentiment scores for entities over all previously scraped times
		Returns: labels, med, ser, cmpb, bmt, ict, ippt, rt, fcc, portal, camp, training, loc
			Lists used for the rendering of charts on the Posts Breakdown page
		"""
		collections = []
		for col in self.db.collections():
			if "sentiment_freq_by_entity" in str(col.id):
				collections.append(str(col.id))

		collections = sorted(collections)
		#['MEDICAL', 'SERVICE', 'CMPB', 'BMT', 'ICT', 'IPPT', 'RT/IPT', 'FCC', 'PORTAL', 'CAMP', 'TRAINING', 'LOCATION']
		labels = []

		for col in collections:
			st = col[24:]
			if st == "":
				pass;
			else:
				labels.append(st)
		print(labels)

		med, ser, cmpb, bmt, ict, ippt, rt, fcc, portal, camp, training, loc = list(),list(),list(),list(),list(),list(),list(),list(),list(),list(),list(), list()

		for col in collections:
			data = self.db.collection(col).get()
			for entry in data:
				entry = entry.to_dict()

				if entry["Entity"] == "MEDICAL":
					med.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "SERVICE":
					ser.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "CMPB":
					cmpb.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "BMT":
					bmt.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "ICT":
					ict.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "IPPT":
					ippt.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "RT/IPT":
					rt.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "FCC":
					fcc.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "PORTAL":
					portal.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "CAMP":
					camp.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "TRAINING":
					training.append(round(entry["Avg_sent"]-1, 2))
				elif entry["Entity"] == "LOCATION":
					loc.append(round(entry["Avg_sent"]-1, 2))
		return labels, med, ser, cmpb, bmt, ict, ippt, rt, fcc, portal, camp, training, loc


	def run_processing(self):
		"""
		Driver method for running all processing tasks. 
		Warning: Requires significant compute power and can take 3+ hours. Works faster with GPU enabled mode
		"""
		# Web Scraping
		self.get_google_reviews("CMPB", "https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1")
		logger.info("\nScraped Google Reviews for CMPB")
		self.get_google_reviews("BedokFCC", "https://www.google.com/maps/place/Bedok+FCC+in+Bedok+Camp+2/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da22d0dd021831:0x72f9d7d2f5dfe24d!8m2!3d1.3168752!4d103.954114!9m1!1b1")
		logger.info("Scraped Google Reviews for BedokFCC")
		self.get_google_reviews("MajuFCC", "https://www.google.com/maps/place/Maju+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da114548788fbf:0xe7b1351cb138a2dc!8m2!3d1.3297773!4d103.7717872!9m1!1b1")
		logger.info("Scraped Google Reviews for MajuFCC")
		self.get_google_reviews("KranjiFCC", "https://www.google.com/maps/place/Kranji+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da11ae095fac6f:0xfbe6c8bc26249e47!8m2!3d1.400557!4d103.7416568!9m1!1b1")
		logger.info("Scraped Google Reviews for KranjiFCC")
		self.get_google_reviews("ClementiCamp", "https://www.google.com/maps/place/Clementi+Camp/@1.3170913,103.9013688,13z/data=!4m11!1m2!2m1!1sMedical+Center+NS!3m7!1s0x31da11a69aa0ac43:0xca88158b0ea52b74!8m2!3d1.3290056!4d103.7629462!9m1!1b1!15sChFNZWRpY2FsIENlbnRlciBOU1omChFtZWRpY2FsIGNlbnRlciBucyIRbWVkaWNhbCBjZW50ZXIgbnOSAQRjYW1w")
		logger.info("Scraped Google Reviews for ClementiCamp")

		self.get_hardwarezone("SAF Training", "https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html")
		logger.info("\nScraped HardwareZone 1")
		self.get_hardwarezone("FFI", "https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/ffi-need-go-every-year-after-35-a-4109332.html")
		logger.info("\nScraped HardwareZone 2")
		self.get_hardwarezone("Reservists", "https://forums.hardwarezone.com.sg/threads/after-40-years-old-still-need-to-go-back-to-reservist.5111453/")
		logger.info("\nScraped HardwareZone 3")
		
		d = date.today() - timedelta(days=365)
		unixtime = time.mktime(d.timetuple())
		self.get_reddit(startdate=unixtime)
		logger.info("\nScraped Reddit")

		# Get all the data from firebase
		data_dict = self.get_all_contentdata(separate=False)
		logger.info("\nDone getting content data from Firebase!")

		# Run Entity Extraction
		data = data_dict["general"]
		html, entities = self.run_entityextraction(data)
		logger.info("\nDone extracting entities!")

		# Run Feature Extraction Code
		dataDF = pd.DataFrame(data, columns=["Content"])
		features = self.run_feat_extraction(dataDF)
		logger.info("\nDone extracting features and running sentiment analysis!")

		# Intersect Features
		# Get the intersection of features and output entity-sentiment-freq table
		intersecting_features = self.intersect_features(features, entities)
		logger.info(intersecting_features.head(10))
		final_entity_table = self.entity_table(intersecting_features)
		logger.info(final_entity_table.head(10))

		# Get sentence-level sentiments
		self.sentence_level_sentiment()
		logger.info("\nDone calculating and pushing sentence-level sentiments!")
	



def main():
	"""
	Driver method to test functionality in 3rd party codes.
	"""
	scraper = DSTA_Service_Delivery()
	scraper.initialiseDB()

	'''
	# Don't need to run these again:

	scraper.get_google_reviews("CMPB", "https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1")
	print("\nScraped Google Reviews for", "CMPB")
	scraper.get_google_reviews("BedokFCC", "https://www.google.com/maps/place/Bedok+FCC+in+Bedok+Camp+2/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da22d0dd021831:0x72f9d7d2f5dfe24d!8m2!3d1.3168752!4d103.954114!9m1!1b1")
	print("Scraped Google Reviews for", "BedokFCC")
	scraper.get_google_reviews("MajuFCC", "https://www.google.com/maps/place/Maju+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da114548788fbf:0xe7b1351cb138a2dc!8m2!3d1.3297773!4d103.7717872!9m1!1b1")
	print("Scraped Google Reviews for", "MajuFCC")
	scraper.get_google_reviews("KranjiFCC", "https://www.google.com/maps/place/Kranji+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da11ae095fac6f:0xfbe6c8bc26249e47!8m2!3d1.400557!4d103.7416568!9m1!1b1")
	print("Scraped Google Reviews for", "KranjiFCC")
	scraper.get_google_reviews("ClementiCamp", "https://www.google.com/maps/place/Clementi+Camp/@1.3170913,103.9013688,13z/data=!4m11!1m2!2m1!1sMedical+Center+NS!3m7!1s0x31da11a69aa0ac43:0xca88158b0ea52b74!8m2!3d1.3290056!4d103.7629462!9m1!1b1!15sChFNZWRpY2FsIENlbnRlciBOU1omChFtZWRpY2FsIGNlbnRlciBucyIRbWVkaWNhbCBjZW50ZXIgbnOSAQRjYW1w")
	print("Scraped Google Reviews for", "ClementiCamp")

	scraper.get_hardwarezone("SAF Training", "https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html")
	print("\nScraped HardwareZone 1")
	scraper.get_hardwarezone("FFI", "https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/ffi-need-go-every-year-after-35-a-4109332.html")
	print("\nScraped HardwareZone 2")
	scraper.get_hardwarezone("Reservists", "https://forums.hardwarezone.com.sg/threads/after-40-years-old-still-need-to-go-back-to-reservist.5111453/")
	print("\nScraped HardwareZone 3")
	
	d = date.today() - timedelta(days=365)
	unixtime = time.mktime(d.timetuple())
	scraper.get_reddit(startdate=unixtime)
	print("\nScraped Reddit")
	'''
	
	# Run this to read the text data from Firebase, scraped from the above sources
	data_dict = scraper.get_all_contentdata(separate=False)
	print("\nDone getting content data from Firebase!")
	
	'''
	data = data_dict["general"]
	words = [word for line in data for word in line.split()]
	words = [word.replace("\n", "") for word in words]
	desired = []
	punct = ["/", "\\", "-"]
	for word in words:
		for p in punct:
			if word.find(p) != -1:
				desired.append(word)
	print(desired)

	'''
	# Run entity extraction
	data = data_dict["general"]
	html, entities = scraper.run_entityextraction(data)
	print("\nDone extracting entities!")

	# Run feature extraction and sentiment analysis 
	dataDF = pd.DataFrame(data, columns=["Content"])
	features = scraper.run_feat_extraction(dataDF)
	print("\nDone extracting features and running sentiment analysis!")

	# Get the intersection of features and output entity-sentiment-freq table
	intersecting_features = scraper.intersect_features(features, entities)
	print(intersecting_features.head(10))
	final_entity_table = scraper.entity_table(intersecting_features)
	print(final_entity_table.head(10))

	# Get sentence-level sentiments
	scraper.sentence_level_sentiment()
	print("\nDone calculating and pushing sentence-level sentiments!")
	

if __name__ == "__main__":
	main()
	print("Completed all processes. Will exit code now.")