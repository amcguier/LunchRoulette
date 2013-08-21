from flask import Flask
from flask import render_template,request,redirect,url_for,Response
from flask.ext.pymongo import PyMongo


appName = "LunchRoulette"
app = Flask(appName)
mongo = PyMongo(app)

@app.route('/')
def primary():
    return render_template('main.html')



#Add a person to the python database
#Return true if added, false if they've already exist
def addPerson(first_name,last_name,email_address,department):
    return true

#For now, returning an empty list till you figure out what to return
#Given a set number of people to include do the following
#If an existing lunch set exists, clear it, saving partipants back to the 
#database with 0 priority
#Randomly select a new group of people to go to lunch respecting priorities
def createNewLunchSet(number_participants):
    return []

#If this person is in the current lunch set
#put them back into the main database at their previous priority
#select someone else randomly to take their place in this lunch set
def skipThisPerson(email):
    return true

#remove this person entirely from the database.
def removePerson(email):
    

if __name__ == '__main__':
    app.run(debug=True)
