import json

import os.path
import socket, struct
import subprocess
import sys
import threading
import time
import requests
import fcntl
from resetsettings import *


def checkForReset():
    # FABconv2 = []

    while True:

        time.sleep(CheckForReset)

        try:

            if os.path.isfile(FabnrFile):
                with open(FabnrFile, 'r') as file:
                    data = file.read().rstrip()
                    jdata = {'pumpid': data, 'accesstoken': ''}
                    session = openSession()
                    if debug == 2:
                        req = post(session, WebserviceResetURL2, jdata)
                    else:
                        req = post(session, WebserviceResetURL, jdata)
                    reqdata = req.json()
                    if debug == 2:
                        print(reqdata)
                    #                         {
                    #     "Access": "Granted",
                    #     "forcereboot": "1",
                    #     "online": 0,
                    #     "update": 1,
                    #     "up": {
                    #         "piboot": {
                    #             "set": "1",
                    #             "id": "291556"
                    #         }
                    #     }
                    # }
                    if (reqdata['update'] == 1):
                        jo = reqdata['up']
                        jo2 = json.dumps(jo)
                        if 'piboot' in jo2:
                            jo3 = jo['piboot']
                            a = jo3['set']
                            if a == "1":
                                subprocess.call(['/sbin/reboot'], shell=True)
                            else:
                                print("set is not 1 so not rebooting/resetting the client")
                        else:
                            print("piboot not in the return set so not rebooting/resetting the client")
                    else:
                        print("update is not in set to 1 so not rebooting/resetting the client")
            else:
                print("file with fabnr do not exist" + FabnrFile + " so cannot check for reset/reboot yet")
        except:
            if debug == 2:
                error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  checkForReset Error\n")
                print(error)
            pass


"""



#Open a new requests session



"""


def openSession():
    s = requests.Session()

    return s


"""



#Post json data to server



"""


def post(session, wsadr, postdata):
    session = session

    webserviceaddress = wsadr

    data = postdata

    session.headers.update({'content-type': 'application/json'})

    out = session.post(webserviceaddress, data=json.dumps(data), timeout=30.0)

    if debug == 2:
        print(out.json())

    return out
