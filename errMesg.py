import os
from dotenv import load_dotenv

load_dotenv()
ERR_FILE_PATH = os.getenv("ERR_FILE_PATH")

def getFileMesg():
    mesg = None
    with open(ERR_FILE_PATH, 'r+') as f:
        mesg = f.read()
        f.truncate(0)
    return mesg

def getErrMesg():
    return getFileMesg()