import csv
from LunchRoulette.__init__ import mongo
from random import choice
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


def addToDBFromCSV(uploadFile):
	format = True
	reader = csv.reader(uploadFile, delimiter=',')
	for row in reader:
		#Check to make sure all data fields are present 
		if(len(row)<5):
			format = False
		else:
			addPerson(row[0],row[1],row[2],row[3],parseHireDate(row[4]))
	return format


#Add a person to the database
#Return True if added, False if they've already exist
def addPerson(first_name,last_name,email_address,department,hire):
	if (mongo.db.people.find({"email": email_address.lstrip()}).count()==0):
		entry = {"first": first_name.lstrip(),"last": last_name.lstrip(),
		"email": email_address.lstrip(),"department": department.lstrip(), 
		"hire":hire, "priority": 1, "pause":0}
		mongo.db.people.insert(entry)
		return True
	else:
		return False
 

#Function to parse the hired date into a comparable format
#changes from mm/dd/yyyy -> yyyymmdd
def parseHireDate(dateString):
	dateList = dateString.split("/")
	return (int(dateList[2])*10000+int(dateList[0])*100+int(dateList[1]))

#Creates new lunch set.  If lunch set already contains members,
#their priority is set to 0 and they are removed
#returns list of the new lunch set
def createNewLunchSet(number_participants,dateStr):
	skippedUpdate()
	dateList = dateStr.split("-")
	dateStrFixed = dateList[1]+"/"+dateList[2]+"/"+dateList[0]
	if mongo.db.ls.find().count() != 0:
		for person in mongo.db.ls.find():
			mongo.db.people.update({"email": person["email"]}, 
								{"$set": {"priority": 0}})
			mongo.db.people.update({"email":person["email"]},
								{"$set": {"pause":4}})
			mongo.db.ls.remove(person)
	lunchList = addToLunchSet(number_participants,"",dateStrFixed)
	updatePriority()
	return


#If this person is in the current lunch set
#put them back into the main database with 
#the negation of their previous priority
#and select someone else randomly to take their place in this lunch set
#returns True upon success, False upon failure
def skipThisPerson(email):
	ret = False
	person = mongo.db.ls.find_one({"email":email})
	#Check to see if the given email is in the current lunch set
	if person == None:
		return ret
	#Increment and negate skipped person's priority (so they don't get picked again)
	mongo.db.people.update({"email":email},{"$set":{"priority": -(person["priority"]+1)}})
	mongo.db.ls.remove({"email": email})
	#Determine which set (older/newer) of employees to draw from
	if(person["hire"]<avgDate()):
		#Add older
		if (addToLunchSet(1,"pre",person['lsDate'])):
			ret = True
	else:
		if (addToLunchSet(1,"post",person['lsDate'])):
			ret = True
	return ret


#Add specified number of people to the lunch set
#Returns True upon success or false upon failure
def addToLunchSet(number_of_additions,flag,dateStr):
	lsIns = False
	#find everyone eligable to join the lunch set
	eligable = mongo.db.people.find({"priority": {"$gt": 0}})
	date = avgDate()
	eligableOld = []
	eligableNew = []
	if (eligable.count() == 0):
		return False
	for entry in eligable:
		i = entry["priority"]
		#if not in the current lunch set
		if(mongo.db.ls.find(entry).count()==0):
			#if entry is "older" employee, add to that weighted list
			if(entry["hire"]< date and (flag=="" or flag=="pre")):
				#Add "priority" number of copies of entry to the weighted list
				for j in range(i):
					eligableOld.append({"email": entry["email"]})
			#if entry is "newer" employee, add to weighted list
			if(entry["hire"]>= date and (flag=="" or flag=="post")):
				for j in range(i):
					eligableNew.append({"email": entry["email"]})
	#Add employee based off specified hire date
	if(flag!=""):
		#older employee
		if(flag=="pre"):
			for k in range(number_of_additions):
				lsIns = aTLShelper(eligableOld,dateStr)
		#newer employee
		else:
			for k in range(number_of_additions):
				lsIns = aTLShelper(eligableNew,dateStr)
	#add employees from both older and newer lists
	else:
		#get half of members from "older" list
		for k in range(number_of_additions/2):
			lsIns = aTLShelper(eligableOld,dateStr)
		#get other half from "newer" list
		for k in range(number_of_additions-(number_of_additions/2)):
			lsIns = aTLShelper(eligableNew,dateStr)
	if (lsIns):
		return True
	else:	
		return False


#Helper function to populate Lunch Set
def aTLShelper(person_list,dateStr):
	lsIns = False;
	size = len(person_list)
	if (size >0):
		while(lsIns == False and size>0):
			selected = choice(person_list)
			if departmentCheck(mongo.db.people.find_one(selected)['department']):
				newPerson = mongo.db.people.find_one(selected)
				newPerson['emailed'] = False
				newPerson['lsDate'] = dateStr
				mongo.db.ls.insert(newPerson)
				lsIns = True
			#remove all copies of selected person from weighted list
			try:
				while(1):
					person_list.remove(selected)
			except:
				pass
		return lsIns

#remove this person entirely from the database.
#Return True upon success, False when email doesn't exist in the db
def removePerson(email):
	#Replace person if they're in the current lunch set
	if mongo.db.ls.find({"email": email}).count() >0:
		skipThisPerson(email)		
	try:
		#Remove given email(and associated entry) from DB
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
			if (person["pause"]==0):
				mongo.db.people.update({"email": person["email"]},
										{"$set": {"priority": person["priority"]+1}})
			else:
				mongo.db.people.update({"email": person["email"]},
										{"$set": {"pause": person["pause"]-1}})
	return True


#Updates priorities of skipped members by (re)negating them
def skippedUpdate():
	eligable = mongo.db.people.find({"priority": {"$lt": 0}})
	if eligable.count() == 0:
		return
	else:
		for person in eligable:
			mongo.db.people.update({"email":person["email"]},
									{"$set":{"priority":-person["priority"]}})
		return


#Sorts all members by hire date and then find midpoint
def avgDate():
	datesortdb = mongo.db.people.find().sort([("hire",1)])
	sortedList = []
	for person in datesortdb:
		sortedList.append(person["hire"])
	return sortedList[len(sortedList)/2]


#Check input for blank fields/primitave date check
def validatePerson(first,last,email,department,hire):
	if(len(first) == 0 or len(last) == 0 or len(email) == 0 
		or len(department) == 0):
		return False
	return True


#Check to see if too many entries from the same department are present
#Returns true if new member is valid, false if not
def departmentCheck(entryDept):
	DEPTCAP = 3   #!!!Change this value to change the department cap
	valid = True
	dept = str(entryDept)
	deptCount = mongo.db.ls.find({"department":dept}).count()
	if(deptCount == DEPTCAP):
		return False
	else:
		return True


#Send email to the current Lunch Set
def emailLS():
	ret = True
	filePath = os.path.join(os.getcwd(),"LunchRoulette/templates/templateEmail.html")
	smtpObj = smtplib.SMTP('HMS1.BoomTownROI.Com')
	smtpObj.login("bulkmail","StarField1232")
	sender = 'Talent@boomtownroi.com'

	for person in mongo.db.ls.find():
		message=""
		member = person["first"]+" "+person["last"]
		if not person['emailed']:
			o = open(filePath)
			mongo.db.ls.update({"email": person["email"]}, 
								{"$set": {"emailed": True}})
			for line in o:
				message+=line.replace("Insert name here",member)
			o.close()
			MESSAGE = MIMEMultipart('alternative')
			MESSAGE['subject'] = "You've been selected!"
			MESSAGE['To'] = person['email']
			MESSAGE['From'] = sender
			HTML_BODY = MIMEText(message, 'html')
			MESSAGE.attach(HTML_BODY)

			try:
  				smtpObj.sendmail(sender, [person['email']], MESSAGE.as_string())         
  				print "Successfully sent email"
			except smtplib.SMTPException:
  				print "Error: unable to send email for "+member
  				ret = False
  	return ret