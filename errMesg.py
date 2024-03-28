import os
import errno
from dotenv import load_dotenv
import platform

load_dotenv()
ERR_PIPE_PATH = os.getenv('ERR_PIPE_PATH')
ERR_FILE_NAME = os.getenv("ERR_FILE_NAME")

def safePipeRead(fifo, nBytes):
    try:
        return os.read(fifo, nBytes)
    except OSError as err:
        if err.errno == errno.EAGAIN:
            return ""
        raise

def getPipeMesg():
    mesg = None
    if(platform.system() != 'Linux'):
        return mesg
    
    try:
        pipe = os.open(ERR_PIPE_PATH, os.O_RDONLY | os.O_NONBLOCK)
        _mesg = safePipeRead(pipe, 100)
        while(len(_mesg)):
            mesg = mesg + _mesg
            mesg = safePipeRead(pipe, 100)
        mesg = mesg.decode('utf-8')
    except:
        mesg = "Error reading from pipe."

    os.close(pipe)
    return mesg

def getFileMesg():
    mesg = None
    with open(ERR_FILE_NAME, 'r+') as f:
        mesg = f.read()
        f.truncate(0)
    return mesg

def getErrMesg():
    mesg = None
    mesg = getFileMesg()
    if(not mesg):
        print("Nothing from file")
        mesg = getPipeMesg()

    return mesg