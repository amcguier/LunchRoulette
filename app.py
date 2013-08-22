from flask import Flask
from flask import render_template,request,redirect,url_for,Response
from flask.ext.pymongo import PyMongo


appName = "LunchRoulette"
app = Flask(appName)
mongo = PyMongo(app)

@app.route('/')
def primary():
    return render_template('main.html')


@app.route('/add')
def addPersonPage():
    return render_template('addPerson.html')



#Add a person to the python database
#Return true if added, false if they've already exist
def addPerson(first_name,last_name,email_address,department):
    if None == mongo.people.find_one({"email": email_address}):
        entry = {"first": first_name,"last": last_name,
                 "email": email_address,"department": department, 
                 "priority": 0}
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
            mongo.people.update({"email": person["email"]}, {"$set": {"priority": 0}})
            mongo.ls.remove(person)        
    return []

#If this person is in the current lunch set
#put them back into the main database at their previous priority
#select someone else randomly to take their place in this lunch set
def skipThisPerson(email):
    return true

#remove this person entirely from the database.
def removePerson(email):
    return true

if __name__ == '__main__':
    app.run(debug=True)
