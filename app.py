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


#Add a person to the python database
#Return true if added, false if they've already exist
def addPerson(first_name,last_name,email_address,department):
	if None == mongo.db.people.find_one({"email": email_address}):
            entry = {"first": first_name,"last": last_name,
                     "email": email_address,"department": department, 
                     "priority": 1}
            mongo.db.people.insert(entry)
            return true
        else:
            return false


 

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
#returns true upon success, false upon failure
def skipThisPerson(email):
    person = mongo.db.ls.find({"email": email})
    if person == None:
    	return false
    mongo.db.people.update({"email": email}, {"$set": {"priority": person["priority"]+1}})
    mongo.db.ls.remove({"email": email})
    addToLunchSet(1)
    return true




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
#Return true upon success, false when email doesn't exist
def removePerson(email):
	if mongo.db.ls.find({"email": email}) != None:
		skipThisPerson(email)		

	try:
		mongo.db.people.remove({"email": email})
	except:
		return false
	return true
	



#Update priorities of people not chosen in the lunch set
#Returns true upon success
def updatePriority():
	for person in mongo.db.people.find():
		if mongo.db.ls.find(person) == None:
			mongo.db.people.update({"email": person["email"]},
								{"$set": {"priority": person["priority"]+1}})
	return true
    



if __name__ == '__main__':
    app.run(debug=True)
