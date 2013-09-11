import flask
from flask import Flask
from flask import render_template,request,redirect,url_for,Response,jsonify,send_from_directory
from flask.ext.pymongo import PyMongo
import csv
from random import choice



appName = "LunchRoulette"
app = Flask(appName)
mongo = PyMongo(app)

ALLOWED_EXTENSIONS = set(['csv'])

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
		createNewLunchSet(int(request.form['num']))
		return Response(flask.json.dumps(True),status=200,mimetype='application/json')

@app.route('/newPerson', methods=['POST'])
def addNewPerson():
	if validatePerson(request.form["first"],request.form["last"],request.form["email"],request.form["department"],request.form["hire"]):
		if addPerson(request.form["first"],request.form["last"],request.form["email"],request.form["department"],request.form["hire"]):
			return Response(flask.json.dumps(True),status=200,mimetype='application/json')
		else:
			return Response(flask.json.dumps(False),status=200,mimetype='application/json')
	else:
		return Response(flask.json.dumps(False),status=200,mimetype='application/json')

@app.route('/removeSelected', methods=['POST'])
def removeSelected():
	if removePerson(request.form["email"]):
		return Response(flask.json.dumps(True),status=200,mimetype='application/json')
	else:
		return Response(flask.json.dumps(False),status=200,mimetype='application/json')

@app.route('/toSkip', methods=['POST'])
def skipEmail():
	if skipThisPerson(request.form['email']):
		return Response("true",status=200,mimetype='application/json')
	else:
		return Response("false",status=200,mimetype='application/json')

@app.route('/addCSV',methods=['POST'])
def getCSV():
	print "Calling script now"
	myfile = request.files['fileInput']
	if(addToDBFromCSV(myfile)):
		return redirect('/add?Success')
	else:
		return redirect('/add?Failure')


def addToDBFromCSV(uploadFile):
	format = True
	reader = csv.reader(uploadFile, delimiter=',')
	for row in reader:
		if(len(row)<4):
			format = False
		else:
			addPerson(row[0],row[1],row[2],row[3],row[4])
	return format



#Add a person to the database
#Return True if added, False if they've already exist
def addPerson(first_name,last_name,email_address,department,hire):
	if (None == mongo.db.people.find_one({"email": email_address})):
		entry = {"first": first_name,"last": last_name,
		"email": email_address,"department": department, 
		"hire":hire, "priority": 1}
		mongo.db.people.insert(entry)
		return True
	else:
		return False
 

#Creates new lunch set.  If lunch set already contains members,
#their priority is set to 0 and they are removed
#returns list of the new lunch set
def createNewLunchSet(number_participants):
	skippedUpdate()
	if mongo.db.ls.find().count() != 0:
		for person in mongo.db.ls.find():
			mongo.db.people.update({"email": person["email"]}, 
								{"$set": {"priority": 0}})
			mongo.db.ls.remove(person)
	lunchList = addToLunchSet(number_participants)
	updatePriority()
	return lunchList


#If this person is in the current lunch set
#put them back into the main database with 
#the negation of their previous priority
#and select someone else randomly to take their place in this lunch set
#returns True upon success, False upon failure
def skipThisPerson(email):
    if mongo.db.ls.find({"email": email}).count() == 0:
    	return False
    person = mongo.db.ls.find_one({"email":email})
    temp = person["priority"]
    mongo.db.people.update({"email":email},{"$set":{"priority": -(temp+1)}})
    mongo.db.ls.remove({"email": email})
    if (addToLunchSet(1)):
    	return True
    else:
    	return False


#Add specified number of people to the lunch set
#Returns True upon success or false upon failure
def addToLunchSet(number_of_additions):
	lsIns = False
	eligable = mongo.db.people.find({"priority": {"$gt": 0}})
	if (eligable.count() == 0):
		return False
	lunchList = []
	weightedList = []
	for entry in eligable:
		i = entry["priority"]
		if(mongo.db.ls.find(entry).count()==0):
			for j in range(i):
				weightedList.append({"email": entry["email"]})
	for k in range(number_of_additions):
		if (len(weightedList) >0):
			selected = choice(weightedList)
			mongo.db.ls.insert(mongo.db.people.find(selected))
			lsIns = True
			lunchList.append(selected)
			try:
				while(1):
					weightedList.remove(selected)
			except:
				pass
	if (lsIns):
		return True
	else:	
		return False


#remove this person entirely from the database.
#Return True upon success, False when email doesn't exist in the db
def removePerson(email):
	if mongo.db.ls.find({"email": email}).count() >0:
		skipThisPerson(email)		
	try:
		mongo.db.people.remove({"email": email})
	except:
		return False
	return True


#Update priorities of people not chosen in the lunch set
#If someone skipped, their priority is negated (again)
#Returns True upon success
def updatePriority():
	for person in mongo.db.people.find():
		if mongo.db.ls.find(person).count() == 0:
			mongo.db.people.update({"email": person["email"]},
									{"$set": {"priority": person["priority"]+1}})
	return True


#Updates priorities of skipped members
#TODO add return
def skippedUpdate():
	eligable = mongo.db.people.find({"priority": {"$lt": 0}})
	if eligable.count() == 0:
		return
	else:
		for person in eligable:
			mongo.db.people.update({"email":person["email"]},
									{"$set":{"priority":-person["priority"]}})
		return


def validatePerson(first,last,email,department,hire):
	if(len(first) == 0 or len(last) == 0 or len(email) == 0 or len(department) == 0 or len(hire)==0):
		return False
	return True

if __name__ == '__main__':
    app.run(debug=True)
