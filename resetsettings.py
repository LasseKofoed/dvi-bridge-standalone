# -*- coding: utf-8 -*-

"""
#URL to webservice
"""

WebserviceResetURL = "https://ws.dvienergi.com/ws-dvi-reboot.php?forcereboot=1"
WebserviceResetURL2 = "https://SmartControAPI.fslogin.dk/ws-dvi-reboot.php?forcereboot=1"

"""
#Path to the fabrikationsnummer file
"""

FabnrFile = "/home/code/fabnr.cfg"

"""
#Debug mode 0/1/2
#0 = No debug
#1 = Can also run as service and write $Errorlog
#2 = Shouldn't run as service and show post and recieved data
"""

debug = 0

global FabNR
# check for reset every (x seconds)
global CheckForReset

FabNR = '000000'
CheckForReset = 60
