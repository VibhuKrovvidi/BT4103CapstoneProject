from flask import Flask

app = Flask(__name__)

users = [{'uid': 1, 'name': 'Noah Schairer'}]

@app.route('/api/userinfo')
def userinfo():
    return {'data': users}, 200

if __name__ == '__main__':
    app.run(debug=True)