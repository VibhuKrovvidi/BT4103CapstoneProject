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
<<<<<<< Updated upstream
import testclass
from testclass import TestClass

'''
import spacy
from spacy import displacy
nlp = spacy.load('en_core_web_sm')
'''
from testclass import TestClass;
=======
import sda
from sda import DSTA_Service_Delivery
>>>>>>> Stashed changes
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
	df = pd.read_csv("../../output/features-entity-score.csv")
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

	labels = [
		'JAN', 'FEB', 'MAR', 'APR',
		'MAY', 'JUN', 'JUL', 'AUG',
		'SEP', 'OCT', 'NOV', 'DEC'
	]

	values = [
		967.67, 1190.89, 1079.75, 1349.19,
		2328.91, 2504.28, 2873.83, 4764.87,
		4349.29, 6458.30, 9907, 16297
	]

	colors = [
		"#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
		"#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
		"#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]
	graph_labels=labels
	graph_values=values
	graph_cats = ["Cat A", "Cat B", "Cat C", "Cat D", "Cat E"]

	return render_template('dashboard_home2.html', max=17000, labels=graph_labels, 
		values=graph_values, category=graph_cats, set=zip(values, labels, colors),
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

@app.route('/runscript')
def runscript():
	if isinstance(auth.current_user, dict):
		


		return render_template("runscript.html")
	else:
		return redirect('/')

@app.route('/runscript/running')
def runningscript():
	if isinstance(auth.current_user, dict):
		print("Starting DSTA Web Scraper")
		scraper = DSTA_Service_Delivery()
		scraper.initialiseDB()

		# GR
		scraper.get_google_reviews("https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1", "CMPB")
		loginfo("Scraped Google Reviews for CMPB")

		scraper.get_google_reviews("https://www.google.com/maps/place/Bedok+FCC+in+Bedok+Camp+2/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da22d0dd021831:0x72f9d7d2f5dfe24d!8m2!3d1.3168752!4d103.954114!9m1!1b1", "BedokFCC")
		loginfo("Scraped Google Reviews for ", "BedokFCC")

		scraper.get_google_reviews("https://www.google.com/maps/place/Maju+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da114548788fbf:0xe7b1351cb138a2dc!8m2!3d1.3297773!4d103.7717872!9m1!1b1", "MajuFCC")
		loginfo("Scraped Google Reviews for ", "MajuFCC")

		scraper.get_google_reviews("https://www.google.com/maps/place/Kranji+FCC/@1.3170913,103.9013688,13z/data=!4m7!3m6!1s0x31da11ae095fac6f:0xfbe6c8bc26249e47!8m2!3d1.400557!4d103.7416568!9m1!1b1", "KranjiFCC")
		loginfo("Scraped Google Reviews for ", "KranjiFCC")

		scraper.get_google_reviews("https://www.google.com/maps/place/Clementi+Camp/@1.3170913,103.9013688,13z/data=!4m11!1m2!2m1!1sMedical+Center+NS!3m7!1s0x31da11a69aa0ac43:0xca88158b0ea52b74!8m2!3d1.3290056!4d103.7629462!9m1!1b1!15sChFNZWRpY2FsIENlbnRlciBOU1omChFtZWRpY2FsIGNlbnRlciBucyIRbWVkaWNhbCBjZW50ZXIgbnOSAQRjYW1w", "ClementiCamp")
		loginfo("Scraped Google Reviews for ", "ClementiCamp")
		

		# Hardwarezone

		scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/ffi-need-go-every-year-after-35-a-4109332.html", "FFI");
		loginfo("Scraped " + "FFI") 

		scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/pes-d-dilemma-3709993.html", "Pes_D_dilemma");
		loginfo("Scraped " + "Pes_D_dilemma") 

		scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/after-40-years-old-still-need-go-back-reservist-5111453.html", "reservist");
		loginfo("Scraped " + "reservist") 

		scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html", "IPPT_IPT_RT");
		loginfo("Scraped " + "IPPT_IPT_RT") 

		scraper.get_harwarezone("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/cmpb-enlistment-medical-checkup-tomorrow-no-form-healthbooklet-how-3623665.html", "CMPB");
		loginfo("Scraped " + "CMPB") 

		# scrape reddit
		d = date.today() - timedelta(days=365)
		unixtime = time.mktime(d.timetuple())

		scraper.get_reddit(start_date = unixtime, limit_amt=10)
		loginfo("Scraped Reddit" )
	else:
		return redirect('/')

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
	
