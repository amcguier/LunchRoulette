import flask
from flask import Flask
from flask import render_template,request,redirect,url_for,Response,jsonify,send_from_directory
from flask.ext.pymongo import PyMongo
import csv
from random import choice
import lsLib



appName = "LunchRoulette"
app = Flask(appName)
mongo = PyMongo(app)

@app.route('/')
def primary():
    return render_template('main.html')

@app.route('/add')
def addPersonPage():
    return render_template('addPerson.html')	

@app.route('/remove')
def removePerson():
	return render_template('removePerson.html')

@app.route('/allEmails')
def getAllEmails():
	js = flask.json.dumps([x['email'] for x in mongo.db.people.find()])
	return Response(js,status=200,mimetype='application/json')

@app.route('/ls')
def getLS():
	js = flask.json.dumps({"lunchset":sorted([x for x in mongo.db.ls.find({},{"first":1,"last":1,"email":1, "_id":0})],key=lambda x: x["first"])})
	return Response(js,status=200,mimetype='application/json')

@app.route('/newLS', methods=['POST'])
def newLS():
	if ((mongo.db.people.find().count()-mongo.db.ls.find().count())<(int(request.form['num']))):
		return Response(flask.json.dumps(False),status=200,mimetype='application/json')
	else:
		lsLib.createNewLunchSet(int(request.form['num']))
		return Response(flask.json.dumps(True),status=200,mimetype='application/json')

@app.route('/newPerson', methods=['POST'])
def addNewPerson():
	hireDate = lsLib.parseDate(request.form["hire"])
	if lsLib.validatePerson(request.form["first"],request.form["last"],request.form["email"],request.form["department"],hireDate):
		if lsLib.addPerson(request.form["first"],request.form["last"],request.form["email"],request.form["department"],hireDate):
			return Response(flask.json.dumps(True),status=200,mimetype='application/json')
		else:
			return Response(flask.json.dumps(False),status=200,mimetype='application/json')
	else:
		return Response(flask.json.dumps(False),status=200,mimetype='application/json')

@app.route('/removeSelected', methods=['POST'])
def removeSelected():
	if lsLib.removePerson(request.form["email"]):
		return Response(flask.json.dumps(True),status=200,mimetype='application/json')
	else:
		return Response(flask.json.dumps(False),status=200,mimetype='application/json')

@app.route('/toSkip', methods=['POST'])
def skipEmail():
	if lsLib.skipThisPerson(request.form['email']):
		return Response("true",status=200,mimetype='application/json')
	else:
		return Response("false",status=200,mimetype='application/json')

@app.route('/addCSV',methods=['POST'])
def getCSV():
	myfile = request.files['fileInput']
	if(lsLib.addToDBFromCSV(myfile)):
		return redirect('/add?Success')
	else:
		return redirect('/add?Failure')




if __name__ == '__main__':
    app.run(debug=True)
