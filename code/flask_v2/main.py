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
            return redirect('/dashboard')
        except:
            return "Invalid Credentials. Please try again"

    return render_template('login.html', title='Sign In', form=form)

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



@app.route('/dashboard')
def dashboard():
    if isinstance(auth.current_user, dict):
        graph_labels=labels
        graph_values=values
        return render_template('dashboard_home.html', max=17000, labels=graph_labels, values=graph_values, set=zip(values, labels, colors))
    else:
        return redirect('/')

    
@app.route('/postbreakdown')
def post_breakdown():
    if isinstance(auth.current_user, dict):
        return "Post Breakdown is still being built"
    else:
        return redirect('/')





logger.add("app/static/job.log", format="{time} - {message}")

def flask_logger():
    """creates logging information"""
    with open("app/static/job.log") as log_info:
        for i in range(25):
            logger.info(f"iteration #{i}")
            data = log_info.read()
            yield data.encode()
            time.sleep(1)
        # Create empty job.log, old logging will be deleted
        open("app/static/job.log", 'w').close()


@app.route("/log_stream", methods=["GET"])
def stream():
    """returns logging information"""
    return Response(flask_logger(), mimetype="text/plain", content_type="text/event-stream")

if __name__ == '__main__':
    app.run(debug=False)
    
