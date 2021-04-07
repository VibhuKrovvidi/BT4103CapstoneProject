import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth
from flask import Flask, request,render_template,flash, redirect,jsonify,Response
#from flask.markdown import Markdown
import forms
from forms import LoginForm
import webbrowser
import time
import random
import datetime
from loguru import logger
import threading
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import queue
from wordcloud import WordCloud, STOPWORDS


'''
import spacy
from spacy import displacy
nlp = spacy.load('en_core_web_sm')
'''

import sda
from sda import DSTA_Service_Delivery
import pandas as pd;

# from flask_login import LoginManager


#App configuration
app = Flask(__name__)
#Markdown(app)
# login_manager.init_app(app)
# login = LoginManager(app)

app.config['SECRET_KEY'] = 'you-will-never-guess'

#Connect to firebase
cred = credentials.Certificate('fbadmin.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))

auth = pb.auth()

#Api route to get a new token for a valid user
@app.route('/', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():

		email = form.email.data
		password = form.password.data
		try:
			user = auth.sign_in_with_email_and_password(email, password)
			return redirect('/holding')
		except:
			return "Invalid Credentials. Please try again"

	return render_template('login.html', title='Sign In', form=form)



@app.route('/holding')
def holding():
	if isinstance(auth.current_user, dict):
		return render_template('holding.html', title="Holding")
	else:
		return redirect('/')


@app.route('/dashboard')
def dashboard():
	# if isinstance(auth.current_user, dict):
	
	# Read from file
	df = pd.read_csv("../../output/sentiment evaluation/features-entity-score.csv")
	df.drop(["Unnamed: 0"], axis=1, inplace=True)

	# Top 10 by freq Bar
	pos = df[df["Avg_sent_singlish"] > 1]

	pos = pos.head(10)

	pos_tag = pos["index"].tolist()
	pos_freq = pos["Freq_singlish"].tolist()

	neg = df[df["Avg_sent_singlish"] < 1]
	neg = neg.head(10)
	print(neg)
	neg_tag = neg["index"].tolist()
	neg_freq = neg["Freq_singlish"].tolist()

	allr = df.head(10)
	allr_tag = allr["index"].tolist()
	allr_sent = allr["Avg_sent_singlish"].tolist()
	allr_sent = [i-1 for i in allr_sent]

	#wordcloud
	comment_words = ''
	stopwords = set(STOPWORDS)
	# iterate through the csv file
	for val in df["index"]:
	      
	    # typecaste each val to string
	    val = str(val)
	  
	    # split the value
	    tokens = val.split()
	      
	    # Converts each token into lowercase
	    for i in range(len(tokens)):
	        tokens[i] = tokens[i].lower()
	      
	    comment_words += " ".join(tokens)+" "
	  
	wordcloud = WordCloud(width = 400, height = 400,
	                background_color ='white',
	                stopwords = stopwords,
	                min_font_size = 10).generate(comment_words)
	  
	wordcloud.to_file("./Static/wordcloud.png")
  

	labels = [
		'JAN', 'FEB', 'MAR', 'APR',
		'MAY', 'JUN', 'JUL', 'AUG',
		'SEP', 'OCT', 'NOV', 'DEC'
	]

	values = [
		1, 1.1, 1.3, 1.3,
		1.25, 1.2, 1.1, 1,
		0.95, 0.7, 0.9, 1
	]

	colors = [
		"#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
		"#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
		"#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]




	labels2 = [
		"Reddit", "Hardwarezone", "Google Reviews", "Others"
	]

	values2 = [
		600, 3000, 350, 0 
	]

	values3 = [	
		0.95, 0.7, 0.9, 1,
		1, 1.1, 1.3, 1.3,
		1.25, 1.2, 1.1, 1,
	]

	colors2 = [
		"#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA"]
	graph_labels=labels
	graph_values=values
	graph_cats = ["IPPT", "Medical", "Cat C", "Cat D", "Cat E"]

	return render_template('dashboard_home2.html', max=17000, labels=graph_labels, 
		values=graph_values, values3=values3, category=graph_cats, set=zip(values2, labels2, colors2),
		postag = pos_tag, posfreq = pos_freq, negtag = neg_tag, negfreq=neg_freq,
		allrtag = allr_tag, allrsent = allr_sent
		)
	# else:
		# return redirect('/')
	
@app.route('/postbreakdown')
def post_breakdown():
	if isinstance(auth.current_user, dict):
		return "Post Breakdown is still being built"
	else:
		return redirect('/')

'''
@app.route('/extractentity', methods=["GET", "POST"])
def extractentitiy():
	if request.method == "POST":
		inputtext = request.form["inputtext"]
		docx = nlp(inputtext)
		html = displacy.render(docx, style="ent")
		result = html
	return render_template("entities.html", inputtext=inputtext, result=result)
'''

myqueue = queue.Queue()
@app.route('/runscript')
def runscript():
	if isinstance(auth.current_user, dict):
		
		init = threading.Thread(target=init_scraper)
		init.start()
		init.join()
		scraper = myqueue.get()

		t1 = threading.Thread(target=scraper.initialiseDB)
		t1.start()
		t1.join()
		t2 = threading.Thread(target=scraper.runscraping)
		t2.start()

		return render_template("runscript.html")
	else:
		return redirect('/')

def init_scraper():
	scraper = DSTA_Service_Delivery()
	myqueue.put(scraper)


logger.add("app/static/job.log", format="{time} - {message}")

def flask_logger():
	flag=True;
	"""creates logging information"""
	
	with open("app/static/job.log") as log_info:
		while flag:
			logger.info(f"")
			data = log_info.read()
			yield data.encode()
			time.sleep(5)
		# Create empty job.log, old logging will be deleted
		open("app/static/job.log", 'w').close()

def loginfo(details):
	open("app/static/job.log", 'w').close()
	if isinstance(details, str):
		logger.info(details)
	else:
		try:
			logger.info(str(details))
		except:
			logger.info("Attempted to log non-string. Was unable to do so.")
	

@app.route("/log_stream", methods=["GET"])
def stream():
	"""returns logging information"""
	return Response(flask_logger(), mimetype="text/plain", content_type="text/event-stream")


if __name__ == '__main__':
	app.run(debug=False)
	
