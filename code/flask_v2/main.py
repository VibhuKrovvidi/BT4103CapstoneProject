import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth
from flask import Flask, request,render_template,flash, redirect,jsonify,Response
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
import processing 
from processing import DSTA_Service_Delivery
import pandas as pd
from flask_caching import Cache



#App configuration
app = Flask(__name__)

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config["CACHE_TYPE"] = 'simple'
cache = Cache()
cache.init_app(app)


#Connect to firebase
cred = credentials.Certificate('fbadmin.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))

auth = pb.auth()

@cache.cached(timeout=300, key_prefix='init_scraper')
def init_scraper():
	scraper = DSTA_Service_Delivery()
	myqueue.put(scraper)

myqueue = queue.Queue()

#Api route to get a new token for a valid user
@app.route('/', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		email = form.email.data
		password = form.password.data
		try:
			user = auth.sign_in_with_email_and_password(email, password)
			return redirect('/dashboard')
		except:
			return "Invalid Credentials. Please try again"

	return render_template('login.html', title='Sign In', form=form)

@app.route('/dashboard')
@cache.cached(timeout=600)
def dashboard():
	if isinstance(auth.current_user, dict):
		
		init = threading.Thread(target=init_scraper)
		init.start()
		# init.join()
		scraper = myqueue.get()
		scraper.initialiseDB()
		data = scraper.get_entity_sent()
		df = pd.DataFrame(data)

		data = df

		data_tag = data["Entity"].tolist()
		data_freq = data["Freq"].tolist()
		data_score = data["Avg_sent"].tolist()
		data_score = [i-1 for i in data_score]

		poslist = []
		neglist = []

		for i in data_score:
			if i >=0:
				poslist.append(round(i, 2))
				neglist.append(0)
			else:
				poslist.append(0)
				neglist.append(round(i, 2))


	# #wordcloud
	# comment_words = ''
	# stopwords = set(STOPWORDS)
	# # iterate through the csv file
	# for val in df["index"]:
	      
	#     # typecaste each val to string
	#     val = str(val)
	  
	#     # split the value
	#     tokens = val.split()
	      
	#     # Converts each token into lowercase
	#     for i in range(len(tokens)):
	#         tokens[i] = tokens[i].lower()
	      
	#     comment_words += " ".join(tokens)+" "
	  
	# wordcloud = WordCloud(width = 400, height = 400,
	#                 background_color ='white',
	#                 stopwords = stopwords,
	#                 min_font_size = 10).generate(comment_words)
	  
	# wordcloud.to_file("./Static/wordcloud.png")
  

		return render_template('dashboard_home2.html', max=17000, 
			datatag = data_tag, datafreq = data_freq, datascore = data_score,
			poslist=  poslist, neglist = neglist
			)
	else:
		return redirect('/')
	
@app.route('/postbreakdown',  methods=['GET'])
@cache.cached(timeout=600)
def post_breakdown():
	if isinstance(auth.current_user, dict):
		init = threading.Thread(target=init_scraper)
		init.start()
		# init.join()
		scraper = myqueue.get()
		scraper.initialiseDB()
		labels, med, ser, cmpb, bmt, ict, ippt, rt, fcc, portal, camp, training, loc = scraper.get_entity_sent_over_time()



		entities = ["SERVICE", "MEDICAL", "IPPT", "LOCATION", "CAMP", "FCC", "ICT", "CMPB", "BMT", "RT", "PORTAL", "TRAINING", "ALL"]
		return render_template("postsbreakdown.html", entities=entities, labels = labels,
			med = med, ser = ser, cmpb = cmpb, bmt = bmt, ict = ict, ippt = ippt, rt = rt, 
			fcc = fcc, portal = portal, camp = camp, training = training, loc = loc)
	else:
		return redirect('/')


@app.route('/display_spacy/ALL')
@cache.cached(timeout=600)
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
@cache.cached(timeout=600)
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
@cache.cached(timeout=600)
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
@cache.cached(timeout=600)
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
@cache.cached(timeout=600)
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
@cache.cached(timeout=600)
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
@cache.cached(timeout=600)
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
@cache.cached(timeout=600)
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

@app.route('/display_spacy/CMPB')
@cache.cached(timeout=600)
def display_spacy_cmpb():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">CMPB</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_cmpb.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_cmpb.html")


@app.route('/display_spacy/BMT')
@cache.cached(timeout=600)
def display_spacy_bmt():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">BMT</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_bmt.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_bmt.html")


@app.route('/display_spacy/RT')
@cache.cached(timeout=600)
def display_spacy_rt():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">RT_IPT</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_rt.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_rt.html")


@app.route('/display_spacy/PORTAL')
@cache.cached(timeout=600)
def display_spacy_portal():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">PORTAL</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_portal.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_portal.html")

@app.route('/display_spacy/TRAINING')
@cache.cached(timeout=600)
def display_spacy_training():
	f = open("./templates/entitiesextracted.html")
	file = f.read()
	f.close()
	x = file.replace("</br></br>", "<br> <hr /> <br>")

	x = x.split("<hr />")

	finlist = []

	for i in x:
	    if """<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">TRAINING</span>""" not in i:
	        pass;
	    else:
	        finlist.append(i)
	        finlist.append("<br> <hr /> <br>")

   
	finstr = ' '.join(finlist)
	finstr = body_start + finstr + body_end

	y = open("./templates/formatted_entities_train.html", "w")
	y.write(finstr)
	y.close()


	return render_template("formatted_entities_train.html")

@app.route("/display_sentence_level")
@cache.cached(timeout=600)
def sentence_level():

	init = threading.Thread(target=init_scraper)
	init.start()
	init.join()
	scraper = myqueue.get()
	scraper.initialiseDB()

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

@app.route('/runscript')
def runscript():
	# if isinstance(auth.current_user, dict):
		
	init = threading.Thread(target=init_scraper)
	init.start()
	init.join()
	scraper = myqueue.get()

	t1 = threading.Thread(target=scraper.initialiseDB)
	t1.start()
	t1.join()
	t2 = threading.Thread(target=scraper.run_processing)
	t2.start()

	return render_template("runscript.html")
	# else:
		# return redirect('/')


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
	
