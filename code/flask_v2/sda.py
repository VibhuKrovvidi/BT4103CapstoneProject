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

stanza.download('en') # download English model
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


class DSTA_Service_Delivery():
	def __init__(self):
		self.chrome_options = Options();
		self.chrome_options.add_argument("--headless")
		self.chrome_options.add_argument("--no-sandbox")
		self.chrome_options.add_argument("--disable-dev-shm-usage")
		self.chrome_prefs = {}
		self.chrome_options.experimental_options["prefs"] = self.chrome_prefs
		self.chrome_prefs["profile.default_content_settings"] = {"images": 2}
		self.nlp = stanza.Pipeline('en')

	def initialiseDB(self):
		# Initialise Firebase
		cred = credentials.Certificate('fbadmin.json')
		# firebase_admin.initialize_app(cred)
		self.db = firestore.client()



	def get_google_reviews(self, url, location = "CMPB"):

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
		has_latest = False;
		try:
			print(latest[0]['content'])
			has_latest = True;
		except:
			pass;
		idcount = 1;
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

		
			
		print("Hardwarezone Data for " + forum + " have been scraped and stored");

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

	# Progress bar
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
		return data;

	def feature_extraction(self, txt):
		# Convert para into sentences
		sentList = nltk.sent_tokenize(txt)

		retlist = [];
		# For each sentence
		for line in sentList:
			# Tag and word tokenize
			txt_list = nltk.word_tokenize(line)
			taggedList = nltk.pos_tag(txt_list)
			
			newwordList = []
			# Merge possible consecutive features ("Phone Battery" ==> "PhoneBattery")
			flag = 0
			for i in range(0,len(taggedList)-1):
				if(taggedList[i][1]=="NN" and taggedList[i+1][1]=="NN"):
					newwordList.append(taggedList[i][0]+taggedList[i+1][0])
					flag=1
				else:
					if(flag==1):
						flag=0
						continue
					newwordList.append(taggedList[i][0])
					if(i==len(taggedList)-2):
						newwordList.append(taggedList[i+1][0])
			finaltxt = ' '.join(word for word in newwordList)
		
			# Remove stop words and tag
			stop_words = set(stopwords.words('english'))
			new_txt_list = nltk.word_tokenize(finaltxt)
			wordsList = [w for w in new_txt_list if not w in stop_words]
			taggedList = nltk.pos_tag(wordsList)
			
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
			
			# Final features + descriptors
			featureList = []
			categories = []
			for i in taggedList:
				if(i[1]=='JJ' or i[1]=='NN' or i[1]=='JJR' or i[1]=='NNS' or i[1]=='RB'):
					featureList.append(list(i))
					categories.append(i[0])
			
			fcluster = []
			for i in featureList:
				filist = []
				for j in dep_node:
					if((j[0]==i[0] or j[1]==i[0]) and (j[2] in [
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
						if(j[0]==i[0]):
							filist.append(j[1])
						else:
							filist.append(j[0])
				fcluster.append([i[0], filist])
			print(fcluster) 
			
			retlist.append(fcluster)
		return retlist;

	def do_extraction(self, df, feat_count, feat_sent, content_str = "Content"):
		
		idx = 0;
		# Replace "" with nan's for removal
		df[content_str].replace('', np.nan, inplace=True)
		df.dropna(subset=[content_str], inplace=True)
		
		review_list = df[content_str].to_list()
		 
		print(" Processing : " , df.shape[0], "rows of data")
		for review in tqdm(review_list):
			print("Review Number : ", idx);
			
			# Some data pre-processing
			
			review = review.lower()
			
			# Merge hyphenated words
			separate = review.split('-')
			review = ''.join(separate)
			
			idx += 1;
			if idx >= df.shape[0]:
				break;
			try:
				output = self.feature_extraction(review);
			except:
				pass;
			for sent in output:
				for pair in sent:
					print(pair)
					if pair[0] in feat_sent:
						if pair[1] is not None:
							flist = feat_sent[pair[0]]
							if isinstance(pair[1], list):
								for i in pair[1]:
									flist.append(i)
							else:
								flist.append(pair[1])
							feat_sent[pair[0]] = flist;
					else:
						if pair[1] is not None:
							flist = pair[1]
						else:
							flist = list()
						feat_sent[pair[0]] = flist;
					
					if pair[0] in feat_count:
						feat_count[pair[0]] = feat_count[pair[0]] + 1;
					else:
						feat_count[pair[0]] = 1
		
		#remove punctuation for sentiment analysis
		for a in feat_count:
			if a in string.punctuation:
				feat_count.remove(a)
		for a in feat_sent:
			if a in string.punctuation:
				feat_sent.remove(a)
		return feat_count, feat_sent;
	

	def get_sentiment(self, feat_count, feat_sent):

		sentiment_score = dict()
		singlish = pd.read_csv("singlish_sent2.csv")
		singlish.columns = ["word", "sent"]
		singlish = dict(zip(singlish.word,singlish.sent))
		print("Singlish dict initialised")

		# Delete features with no descriptors
		cob = feat_sent.copy()
		for feat in cob.keys():
			#print(cob[feat])
			
			if cob[feat] == []:
				del feat_sent[feat]
			else:
				feat_sent[feat] = ' ,'.join(feat_sent[feat])

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
				if g in singlish.keys():
					ssum += singlish[g]
				else:
					try:

						doc = self.nlp(g);

						for i in doc.sentences:

								#print(i.sentiment)
								ssum += i.sentiment;
								new_row = [[f, g, i.sentiment, feat_count[f]]]
								desc_df = desc_df.append(pd.DataFrame(new_row, columns=dcolumns))
					except:
						pass;
			sentiment_score[f] = ssum / length;
			

		adf = pd.DataFrame.from_dict(feat_count, orient='index', columns=['Freq'])
		adf.sort_values(by="Freq", ascending=False, inplace = True)

		

		avg_sent = pd.DataFrame.from_dict(sentiment_score, orient='index', columns=["Avg_sent"])
		desc_words = pd.DataFrame.from_dict(feat_sent, orient="index", columns=["Descriptors"])
		
		avg_sent = avg_sent.merge(desc_words, left_index=True, right_index=True)
		
		
		final_sent = avg_sent.merge(adf, left_index=True, right_index=True)
		final_sent.sort_values(by="Freq", ascending=False, inplace=True)
		print(final_sent.columns)
		return final_sent, desc_df;

	def run_feat_extraction(self, df, content_str="Content"):
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

	# scrape reddit
	d = date.today() - timedelta(days=365)
	unixtime = time.mktime(d.timetuple())

	scraper.get_reddit(start_date = unixtime, limit_amt=10)
	print("Scraped Reddit" )

	# Run processing code:

	# data = scraper.get_all_data()
	# data = pd.DataFrame(data, columns=["Content"])
	# scraper.run_feat_extraction(data)   


	
	

if __name__ == '__main__':
	main()
	print("Completed all processes. Will exit code now")










