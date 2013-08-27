import flask
from flask import Flask
from flask import render_template,request,redirect,url_for,Response,jsonify
from flask.ext.pymongo import PyMongo
from random import choice


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

@app.route('/newPerson', methods=['POST'])
def addNewPerson():
	if addPerson(request.form["first"],request.form["last"],request.form["email"],request.form["department"]):
            return Response(flask.json.dumps(True),status=200,mimetype='application/json')
 	else:
            return Response(flask.json.dumps(False),status=200,mimetype='application/json')

@app.route('/removeSelected', methods=['POST'])
def removeSelected():
	if removePerson(request.form["email"]):
		return Response("True",status=200,mimetype='application/json')
	else:
		return Response("False",status=200,mimetype='application/json')


#Add a person to the python database
#Return True if added, False if they've already exist
def addPerson(first_name,last_name,email_address,department):
	if None == mongo.db.people.find_one({"email": email_address}):
            entry = {"first": first_name,"last": last_name,
                     "email": email_address,"department": department, 
                     "priority": 1}
            mongo.db.people.insert(entry)
            return True
        else:
            return False




 

#For now, returning an empty list till you figure out what to return
#Given a set number of people to include do the following
#If an existing lunch set exists, clear it, saving partipants back to the 
#database with 0 priority
#Randomly select a new group of people to go to lunch respecting priorities
def createNewLunchSet(number_participants):
	if mongo.db.ls.find().count() != 0:
		for person in mongo.db.ls.find():
			mongo.db.people.update({"email": person["email"]}, 
								{"$set": {"priority": 0}})
			mongo.db.ls.remove(person)

	lunchList = addToLunchSet(number_participants)
	updatePriority()
	return lunchList




#If this person is in the current lunch set
#put them back into the main database at their previous priority
#select someone else randomly to take their place in this lunch set
#returns True upon success, False upon failure
def skipThisPerson(email):
    
    if mongo.db.ls.find({"email": email}).count() == 0:
    	return False
    mongo.db.people.update({"email": email}, {"$set": {"priority": person["priority"]+1}})
    mongo.db.ls.remove({"email": email})
    addToLunchSet(1)
    return True




#Add specified number of people to the lunch set
#Returns list of lunch set
def addToLunchSet(number_of_additions):
	eligable = mongo.db.people.find({"priority": {"$gt": 0}})
	lunchList = []
	weightedList = []
	for entry in eligable:
		i = entry["priority"]
		for j in range(i):
			weightedList.append({"email": entry["email"]})

	for k in range(number_of_additions):
		selected = choice(weightedList)
		person = [x for x in eligable if x["email"] == selected].pop()
		mongo.db.ls.insert(person)
		lunchList.append(person)
		try:
			while(1):
				weightedList.remove(selected)
		except:
			pass	
	return lunchList




#remove this person entirely from the database.
#Return True upon success, False when email doesn't exist
def removePerson(email):
	if mongo.db.ls.find({"email": email}).count() >0:
		skipThisPerson(email)		

	try:
		mongo.db.people.remove({"email": email})
	except:
		return False
	return True
	



#Update priorities of people not chosen in the lunch set
#Returns True upon success
def updatePriority():
	for person in mongo.db.people.find():
		if mongo.db.ls.find(person).count() == 0:
			mongo.db.people.update({"email": person["email"]},
								{"$set": {"priority": person["priority"]+1}})
	return True
    



if __name__ == '__main__':
    app.run(debug=True)
