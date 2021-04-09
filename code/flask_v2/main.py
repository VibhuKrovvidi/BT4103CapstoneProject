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

	data = df

	data_tag = data["entity"].tolist()
	data_freq = data["Freq_singlish"].tolist()
	data_score = data["Avg_sent_singlish"].tolist()

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
		datatag = data_tag, datafreq = data_freq, datascore = data_score,
		allrtag = allr_tag, allrsent = allr_sent
		)
	# else:
		# return redirect('/')
	
@app.route('/postbreakdown',  methods=['GET'])
def post_breakdown():
	if isinstance(auth.current_user, dict):
		entities = ["SERVICE", "MEDICAL", "IPPT", "LOCATION", "CAMP", "FCC", "ICT", "ALL"]
		return render_template("postsbreakdown.html", entities=entities)
	else:
		return redirect('/')


@app.route('/display_spacy/ALL')
def display_spacy():
	return render_template("entitiesextracted.html")

body_start = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>displaCy</title>
    </head>

    <body style="font-size: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; padding: 4rem 2rem; direction: ltr">
<figure style="margin-bottom: 6rem">
<div class="entities" style="line-height: 2.5; direction: ltr">

"""
body_end = """
</div>
</figure>
</body>
</html>
"""

@app.route('/display_spacy/SERVICE')
def display_spacy_service():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">SERVICE</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")


	finstr = ' '.join(finlist)

	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_service.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_service.html")

@app.route('/display_spacy/MEDICAL')
def display_spacy_medical():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">MEDICAL</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_medical.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_medical.html")
	

@app.route('/display_spacy/IPPT')
def display_spacy_ippt():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">IPPT</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_ippt.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_ippt.html")

@app.route('/display_spacy/LOCATION')
def display_spacy_location():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">LOCATION</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_location.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_location.html")

@app.route('/display_spacy/CAMP')
def display_spacy_camp():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">CAMP</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_camp.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_camp.html")

@app.route('/display_spacy/FCC')
def display_spacy_fcc():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">FCC</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_fcc.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_fcc.html")


@app.route('/display_spacy/ICT')
def display_spacy_ict():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">ICT</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_ict.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_ict.html")


@app.route("/display_sentence_level")
def sentence_level():
	init = threading.Thread(target=init_scraper)
	init.start()
	init.join()
	scraper = myqueue.get()
	t1 = threading.Thread(target=scraper.initialiseDB)
	t1.start()
	t1.join()
	data = scraper.get_sentence_level()
	df = pd.DataFrame(data)
	df = df.sort_values(["review_id", "sentence_id"], ascending=[True, True])
	content = df["sentence_content"].tolist()
	sent = df["sentence_sent"].tolist()
	review = df["review_id"].tolist()

	finlist = []
	for i in range(0, len(review)):
		if i != 0:
			if review[i] != review[i-1]:
				finlist.append(["<br><hr><br>", "<hr>\n\n"])
		finlist.append([content[i], sent[i]])
	# print(finlist)

	return render_template("sentence_level.html", finlist = finlist)







@app.route('/login')
def login_out():
	# auth.signOut()
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
	
