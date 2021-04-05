import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth

#Connect to firebase
cred = credentials.Certificate('fbadmin.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))

auth = pb.auth()

print(dir(auth))


try:
	ac1 = auth.current_user()
	print(ac1)
	

except:
	print("None User")		

auth.sign_in_with_email_and_password("dsta_staff1@dsta.com", 123456)
ac2 = auth.current_user
if ac2 == None:
	print("None User")
else:
	print(ac2)