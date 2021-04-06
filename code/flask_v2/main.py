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
import testclass
from testclass import TestClass;

# from flask_login import LoginManager


#App configuration
app = Flask(__name__)
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
        ##### READ FROM ANOTHER FILE
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

    return render_template('dashboard_home2.html', max=17000, labels=graph_labels, values=graph_values, category=graph_cats, set=zip(values, labels, colors))
    # else:
        # return redirect('/')

    
@app.route('/postbreakdown')
def post_breakdown():
    if isinstance(auth.current_user, dict):
        return "Post Breakdown is still being built"
    else:
        return redirect('/')


@app.route('/runscript')
def runscript():
    if isinstance(auth.current_user, dict):
        

        return render_template("runscript.html")
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
    
