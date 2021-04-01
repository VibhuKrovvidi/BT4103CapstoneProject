import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth
from flask import Flask, request,render_template,flash, redirect,jsonify
import forms
from forms import LoginForm
import webbrowser
import time
import random
# from flask_login import LoginManager


#App configuration
app = Flask(__name__)
# login = LoginManager(app)

app.config['SECRET_KEY'] = 'you-will-never-guess'

#Connect to firebase
cred = credentials.Certificate('fbadmin.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))

auth = pb.auth()

#Api route to get a new token for a valid user
@app.route('/', methods=['GET', 'POST'])
# def main():
#     return "works"
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
    graph_labels=labels
    graph_values=values
    return render_template('dashboard_home.html', max=17000, labels=graph_labels, values=graph_values, set=zip(values, labels, colors))

@app.route('/postbreakdown')
def post_breakdown():
    return "Post Breakdown is still being built"

if __name__ == '__main__':
    app.run(debug=False)
    
