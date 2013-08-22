from flask import Flask
from flask import render_template,request,redirect,url_for,Response
from flask.ext.pymongo import PyMongo
from random import choice


appName = "LunchRoulette"
app = Flask(appName)
mongo = PyMongo(app)

@app.route('/')
def primary():
    return render_template('main.html')



#Add a person to the python database
#Return true if added, false if they've already exist
def addPerson(first_name,last_name,email_address,department):
	if None == mongo.people.find_one({"email": email_address}):
            entry = {"first": first_name,"last": last_name,
                     "email": email_address,"department": department, 
                     "priority": 1}
            mongo.people.insert(entry)
            return true
        else:
            return false


 

#For now, returning an empty list till you figure out what to return
#Given a set number of people to include do the following
#If an existing lunch set exists, clear it, saving partipants back to the 
#database with 0 priority
#Randomly select a new group of people to go to lunch respecting priorities
def createNewLunchSet(number_participants):
	if mongo.ls.find().count() != 0:
		for person in mongo.ls.find():
			mongo.people.update({"email": person["email"]}, 
								{"$set": {"priority": 0}})
			mongo.ls.remove(person)

	addToLunchSet(number_participants)
	updatePriority()
	return []




#If this person is in the current lunch set
#put them back into the main database at their previous priority
#select someone else randomly to take their place in this lunch set
def skipThisPerson(email):
    person = mongo.ls.find({"email": email})
    if person == None:
    	return false
    mongo.people.update({"email": email}, {"$set": {"priority": person["priority"]+1}})
    mongo.ls.remove({"email": email})
    addToLunchSet(1)
    return true




#Add specified number of people to the lunch set
#Returns true upon success
def addToLunchSet(number_of_additions):
	eligable = mongo.people.find({"priority": {"$gt": 0}})
	weightedList = []
	for entry in eligable:
		i = entry["priority"]
		for j in range(i):
			weightedList.append({"email": entry["email"]})

	for k in range(number_of_additions):
		selected = choice(weightedList)
		mongo.ls.insert(mongo.people.find({"email" :selected["email"]}))
		try:
			while(1):
				weightedList.remove(selected)
		except:
			pass	
	return true




#remove this person entirely from the database.
#Return true upon success, false when email doesn't exist
def removePerson(email):
	if mongo.ls.find({"email": email}) != None:
		skipThisPerson(email)		

	try:
		mongo.people.remove({"email": email})
	except:
		return false
	return true
	



#Update priorities of people not chosen in the lunch set
#Returns true upon success
def updatePriority():
	for person in mongo.people.find():
		if mongo.ls.find(person) == None:
			mongo.people.update({"email": person["email"]},
								{"$set": {"priority": person["priority"]+1}})
	return true
    



if __name__ == '__main__':
    app.run(debug=True)
