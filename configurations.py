from flask_pymongo import pymongo


CONNECTION_STRING = "mongodb+srv://PTCVDL:PTCVDL@ptcvdl.tynhefy.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client.get_database("PTCVDL")
