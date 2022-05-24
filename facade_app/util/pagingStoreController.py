import json, os, datetime
from pymongo import MongoClient
import pymongo

def connectToMongo(page_store_time=1200):
    
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = os.environ["MONGO_DB_URL"]

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example (we will use the same database throughout the tutorial
    db = client['Paging']
    if(not 'Pages' in db.list_collection_names()):
        col = db['Pages']
        col.create_index("date", expireAfterSeconds=page_store_time)
    else:
        col = db['Pages']
    return col

def storePage(page, page_id, page_store_time):
    if(os.environ["PAGING_STORE"]=="MONGO"):
        db = connectToMongo(page_store_time)
        db.insert_one({"_id":page_id,"date":datetime.datetime.now(),"page":page})
    else:
        try:
            with open(f"./pages/{page_id}",'w') as outFile:
                json.dump(page, outFile, indent="")
        except IOError:
            print(IOError)
            return f"Error writing page with ID {page_id}", 403

def getPage(page_id):
    if(os.environ["PAGING_STORE"]=="MONGO"):
        db = connectToMongo()
        return db.find_one({'_id':page_id})["page"]
    else:
        try:
            with open(f"./pages/{page_id}",'r') as inFile:
                return json.load(inFile)
        except:
            return f"No Page with ID {page_id} found", 403

def clearPages(page_store_time, dir_to_search="./pages/"):
    if(os.environ["PAGING_STORE"]=="MONGO"):
        print()
    else:
        for dirpath, dirnames, filenames in os.walk(dir_to_search):
            for file in filenames:
                curpath = os.path.join(dirpath, file)
                file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(curpath))
                if datetime.datetime.now() - file_modified > datetime.timedelta(seconds=page_store_time):
                    os.remove(curpath)