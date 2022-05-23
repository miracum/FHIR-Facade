import json, os, datetime

def storePage(page, pageId):
    try:
        with open(f"./pages/{pageId}",'w') as outFile:
            json.dump(page, outFile, indent="")
    except:
        return f"Error writing page with ID {pageId}", 403

def getPage(pageId):
    try:
        with open(f"./pages/{pageId}",'r') as inFile:
            return json.load(inFile)
    except:
        return f"No Page with ID {pageId} found", 403

def clearPages(page_store_time, dir_to_search="./pages/"):
    for dirpath, dirnames, filenames in os.walk(dir_to_search):
        for file in filenames:
            curpath = os.path.join(dirpath, file)
            file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(curpath))
            if datetime.datetime.now() - file_modified > datetime.timedelta(seconds=page_store_time):
                os.remove(curpath)