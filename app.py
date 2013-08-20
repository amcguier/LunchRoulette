from flask import Flask
from flask import render_template,request,redirect,url_for,Response
from flask.ext.pymongo import PyMongo


appName = "LunchRoulette"
app = Flask(appName)
mongo = PyMongo(app)

@app.route('/')
def primary():
    return render_template('main.html')


if __name__ == '__main__':
    app.run(debug=True)
