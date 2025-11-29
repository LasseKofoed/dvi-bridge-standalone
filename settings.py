# -*- coding: utf-8 -*-

from modbus_tk import modbus_rtu
import serial

"""
#Versions nummer
"""
Version = "3.4.40"

"""
#URL to webservice
"""
WebserviceURL = "https://ws.dvienergi.com/ws-dvi.php"
WebserviceURL2 = "http://awseb-e-t-awsebloa-17kvf6oxolgul-616217914.eu-central-1.elb.amazonaws.com/includes/webservice/ws-dvi.php"

"""
#Port Debian "/dev/ttyACM0"
#Port Windows 'COM1'
"""
ModbusPort = '/dev/ttyACM0'
SlavePORT = '/dev/serial0'

"""
#Path to the errorlog
"""
ErrorLog = "/tmp/dvi_error.log"

"""
#Path to last post time
"""
PostTimePath = "/tmp/dvi_net_posted"
"""
#Path to the config file
"""
ConfigFile = "/home/code/config.cfg"

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
debug = 1  # <--- enable verbose debug output from functions.py

"""
Modbus Master
"""

master = modbus_rtu.RtuMaster(serial.Serial(ModbusPort, baudrate=9600, bytesize=8, parity="N", stopbits=1, xonxoff=0),
                              interchar_multiplier=20, interframe_multiplier=40)
master.set_timeout(2.0)

"""
#Variables for this software
#Online = User is logged in or out
#waitMS is time in seconds the modbustool wait to start a request 
"""

global ModbusServer
global netoffline
global olderror
global errorrelay
global online
global DVIversionTop
global DVIversionBot
global SpeedSettings
global ServerConnection
global FabNR

online = 0
waitMS = 0.03
errorrelay = 0
olderror = 0
netoffline = False
timenetoffline = 43200
DVIversionTop = 0.00
DVIversionBot = 0.00
pingtiming = 3
ModbusServer = False
ServerConnection = True
FabNR = '000000'

"""
#Name and time in seconds
#What raspberry pi send and how often
#All time
"""
SpeedSettings = {
    #                 "getDigitalInput": 10,
    "getRelayData": 10,
    "getPWMData": 10,
    "getMonteurData": 3600,
    "getSensorData": 10,
    "getSpecialBlocksData": 3600,
    "getUserData": 10,
    "getSystemStatusData": 3600,
    "getAdminData": 3600,
    "getSystemTimeData": 3600,
    "getSystemBlocksData": 60,
    #                 "getPing": 10
}

"""
#Name and time in seconds
#What raspberry pi send and how often
#If a user is logged in
"""
LoginSpeedSettings = {
    #                 "getSensorData": 30,
    #                 "getRelayData": 10,
    #                 "getMonteurData": 1200,
    #                 "getUserData": 60,
    #                 "getPing": 3,
    #                 "getPWMData": 10,
    #                 "getAdminData": 800,
}

"""
#Dictonary for all settings
#"SettingName": ModbusID,
#If ID is 250 or over, thats are settings for the raspberry pi
"""
dictSettingList = {
    "B1": 1,
    "B2": 2,
    "B3": 3,
    "B4": 4,
    "B5": 5,
    "B6": 6,
    "B7": 7,
    "B8": 8,
    "B9": 9,
    "B10": 10,
    "B11": 11,
    "B12": 12,
    "B13": 13,
    "B14": 14,
    "B15": 15,
    "B16": 16,
    "B17": 17,
    "B18": 18,
    "B19": 19,
    "B20": 20,
    "M1": 21,
    "M2": 22,
    "M3": 23,
    "M4": 24,
    "M5": 25,
    "M6": 26,
    "M7": 27,
    "M8": 28,
    "M9": 29,
    "M10": 30,
    "M11": 31,
    "M12": 32,
    "M13": 33,
    "M14": 34,
    "M15": 35,
    "M16": 36,
    "M17": 37,
    "M18": 38,
    "M19": 39,
    "M20": 40,
    "M21": 41,
    "M22": 42,
    "M23": 43,
    "M24": 44,
    "M25": 45,
    "DVI1": 46,
    "DVI2": 47,
    "DVI3": 48,
    "DVI4": 49,
    "DVI5": 50,
    "DVI6": 51,
    "DVI7": 52,
    "DVI8": 53,
    "DVI9": 54,
    "DVI10": 55,
    "DVI11": 56,
    "DVI12": 57,
    "DVI13": 58,
    "DVI14": 59,
    "DVI15": 60,
    "DVI16": 61,
    "DVI17": 62,
    "DVI18": 63,
    "DVI19": 64,
    "DVI20": 65,
    "DVI21": 66,
    "DVI22": 67,
    "DVI23": 68,
    "DVI24": 69,
    "DVI25": 70,
    "DVI26": 71,
    "DVI27": 72,
    "DVI28": 73,
    "DVI29": 74,
    "DVI30": 75,
    "DVI31": 76,
    "DVI32": 77,
    "DVI33": 78,
    "DVI34": 79,
    "DVI35": 80,
    "DVI36": 81,
    "DVI37": 82,
    "DVI38": 83,
    "DVI39": 84,
    "DVI40": 85,
    "DVI41": 86,
    "DVI42": 87,
    "DVI43": 88,
    "DVI44": 89,
    "DVI45": 90,
    "DVI46": 91,
    "DVI47": 92,
    "DVI48": 93,
    "DVI49": 94,
    "DVI50": 95,
    "DVI51": 96,
    "DVI52": 97,
    "DVI53": 98,
    "DVI54": 99,
    "DVI55": 100,
    "DVI56": 101,
    "DVI57": 102,
    "DVI58": 103,
    "DVI59": 104,
    "DVI60": 105,
    "DVI61": 106,
    "DVI62": 107,
    "DVI63": 108,
    "DVI64": 109,
    "DVI65": 110,
    "DVI66": 111,
    "DVI67": 112,
    "DVI68": 113,
    "DVI69": 114,
    "DVI70": 115,
    "DVI71": 116,
    "DVI72": 117,
    "DVI73": 118,
    "DVI74": 119,
    "DVI75": 120,
    "DVI76": 121,
    "DVI77": 122,
    "DVI78": 123,
    "DVI79": 124,
    "DVI80": 125,
    "DVI81": 126,
    "DVI82": 127,
    "DVI83": 128,
    "DVI84": 129,
    "DVI85": 130,
    "DVI86": 131,
    "DVI87": 132,
    "DVI88": 133,
    "DVI89": 134,
    "DVI90": 135,
    "DVI91": 136,
    "DVI92": 137,
    "DVI93": 138,
    "DVI94": 139,
    "DVI95": 140,
    "DVI96": 141,
    "DVI97": 142,
    "DVI98": 143,
    "DVI99": 144,
    "DVI100": 145,
    "PUMPSTATUS": 156,
    "AFRIM": 157,
}
