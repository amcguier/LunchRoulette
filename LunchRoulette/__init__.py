import flask
from flask import Flask
from flask.ext.pymongo import PyMongo


appName = "LunchRoulette"
app = Flask(appName)
mongo = PyMongo(app)

from LunchRoulette.views import *