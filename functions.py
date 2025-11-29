# -*- coding: utf-8 -*-
"""
#Modbus Server dev
"""

import json
import os.path
import queue
import socket, struct
import subprocess
import sys
import threading
import time
from datetime import datetime

from modbus_tk import modbus_rtu
from modbus_tk import modbus_tcp
import modbus_tk
from modbus_tk.hooks import call_hooks
import requests
import serial

import fcntl
import modbus_tk.defines as cst
import modbus_tk.hooks as hooks
from settings import *

confirmationQueue = queue.Queue()
startTime = time.time()


def _dbg(msg: str) -> None:
    """Simple debug helper; prints only when debug >= 1."""
    if debug >= 1:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{ts}] [functions] {msg}", flush=True)


def getModbusServerState():
    return ModbusServer


class modbusSlaveDataThread(threading.Thread):

    def __init__(self, DB, ModbusSlaveQueue, Modserver):
        threading.Thread.__init__(self)
        self.ModbusSlaveQueue = ModbusSlaveQueue

        self.slave2 = DB.get_slave(Modserver)
        self.slave2.add_block('RelayData', 4, 1, 14)
        self.slave2.add_block('SensorData', 4, 21, 20)
        self.slave2.add_block('SettingData', 3, 1, 16)

    def run(self):
        while True:
            if modbusServer == 0:
                break
            else:
                pass
            ModbusData = self.ModbusSlaveQueue.get()
            ModbusData = dict(json.loads(ModbusData))
            if 'sensordata' in ModbusData:
                self.slave2.set_values('SensorData', 21, ModbusData['sensordata']['F1'])
                self.slave2.set_values('SensorData', 22, ModbusData['sensordata']['F2'])
                self.slave2.set_values('SensorData', 23, ModbusData['sensordata']['F3'])
                self.slave2.set_values('SensorData', 24, ModbusData['sensordata']['F4'])
                self.slave2.set_values('SensorData', 25, ModbusData['sensordata']['F5'])
                a = ModbusData['sensordata']['F6']
                b = ModbusData['sensordata']['F10']
                if a <= b:
                    output = a
                elif b < a:
                    output = b
                self.slave2.set_values('SensorData', 26, output)
                self.slave2.set_values('SensorData', 27, ModbusData['sensordata']['F7'])
                self.slave2.set_values('SensorData', 28, ModbusData['sensordata']['F8'])
                self.slave2.set_values('SensorData', 29, ModbusData['sensordata']['F9'])
                self.slave2.set_values('SensorData', 30, ModbusData['sensordata']['F10'])
                self.slave2.set_values('SensorData', 31, ModbusData['sensordata']['F11'])
                self.slave2.set_values('SensorData', 32, ModbusData['sensordata']['F12'])
                self.slave2.set_values('SensorData', 33, ModbusData['sensordata']['F13'])
                self.slave2.set_values('SensorData', 34, ModbusData['sensordata']['F14'])

            elif 'relaydata' in ModbusData:
                self.slave2.set_values('RelayData', 1, ModbusData['relaydata']['RLY1'])
                self.slave2.set_values('RelayData', 2, ModbusData['relaydata']['RLY2'])
                self.slave2.set_values('RelayData', 3, ModbusData['relaydata']['RLY3'])
                self.slave2.set_values('RelayData', 4, ModbusData['relaydata']['RLY4'])
                self.slave2.set_values('RelayData', 5, ModbusData['relaydata']['RLY5'])
                self.slave2.set_values('RelayData', 6, ModbusData['relaydata']['RLY6'])
                self.slave2.set_values('RelayData', 7, ModbusData['relaydata']['RLY7'])
                self.slave2.set_values('RelayData', 8, ModbusData['relaydata']['RLY8'])
                self.slave2.set_values('RelayData', 9, ModbusData['relaydata']['RLY9'])
                self.slave2.set_values('RelayData', 10, ModbusData['relaydata']['RLY10'])
                self.slave2.set_values('RelayData', 11, ModbusData['relaydata']['RLY11'])
                self.slave2.set_values('RelayData', 12, ModbusData['relaydata']['RLY12'])
                self.slave2.set_values('RelayData', 13, ModbusData['relaydata']['RLY13'])
                self.slave2.set_values('RelayData', 14, ModbusData['relaydata']['RLY14'])

                if ModbusData['KASKADEonLIST'] == 0:
                    kaskadata = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
                elif ModbusData['KASKADEonLIST'] == 1:
                    kaskadata = {1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
                elif ModbusData['KASKADEonLIST'] == 3:
                    kaskadata = {1: 1, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0}
                elif ModbusData['KASKADEonLIST'] == 7:
                    kaskadata = {1: 1, 2: 1, 3: 1, 4: 0, 5: 0, 6: 0}
                elif ModbusData['KASKADEonLIST'] == 15:
                    kaskadata = {1: 1, 2: 1, 3: 1, 4: 1, 5: 0, 6: 0}
                elif ModbusData['KASKADEonLIST'] == 31:
                    kaskadata = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 0}
                elif ModbusData['KASKADEonLIST'] == 63:
                    kaskadata = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}

                self.slave2.set_values('SensorData', 35, kaskadata[1])
                self.slave2.set_values('SensorData', 36, kaskadata[2])
                self.slave2.set_values('SensorData', 37, kaskadata[3])
                self.slave2.set_values('SensorData', 38, kaskadata[4])
                self.slave2.set_values('SensorData', 39, kaskadata[5])
                self.slave2.set_values('SensorData', 40, kaskadata[6])

            elif 'userdata' in ModbusData:
                self.slave2.set_values('SettingData', 1, ModbusData['userdata']['B1'])
                self.slave2.set_values('SettingData', 2, ModbusData['userdata']['B2'])
                self.slave2.set_values('SettingData', 3, ModbusData['userdata']['B3'])
                self.slave2.set_values('SettingData', 4, ModbusData['userdata']['B10'])
                self.slave2.set_values('SettingData', 5, ModbusData['userdata']['B11'])
                self.slave2.set_values('SettingData', 6, ModbusData['userdata']['B15'])
                self.slave2.set_values('SettingData', 7, ModbusData['PUMPSTATUS'])

            else:
                pass


class modbusServer():

    def __init__(self, DB, jobqueue, slavesendequeue, Modserver):
        self.slavesendequeue = slavesendequeue
        self.jobqueue = jobqueue
        self.DB = DB
        # logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")
        self.server = modbus_rtu.RtuServer(
            serial.Serial(port=SlavePORT, baudrate=19200, bytesize=8, parity='N', stopbits=1, xonxoff=0), databank=DB)
        # server = modbus_tcp.TcpServer(port=502, address="", timeout_in_sec=5, databank=self.DB)
        self.server.set_verbose(True)
        self.slave2 = self.server.get_slave(Modserver)
        hooks.install_hook("modbus_rtu.RtuServer.before_write", self.doifChange)

    def start(self):
        self.server.start()

    def stop(self):
        self.server.stop()

    def doifChange(self, out):
        a = (out[1][3])
        funktionskode = out[1][1]
        if funktionskode == 6:

            modblock = a

            moddata = self.slave2.get_values('SettingData', modblock, 1)

            moddata = moddata[0]

            if modblock == 1:
                block = 'B1'
            elif modblock == 2:
                block = 'B2'
            elif modblock == 3:
                block = 'B3'
            elif modblock == 4:
                block = 'B10'
            elif modblock == 5:
                block = 'B11'
            elif modblock == 6:
                block = 'B15'
            elif modblock == 7:
                block = 'PUMPSTATUS'

            jo = {block: {u'set': moddata, u'id': u'1000'}}
            jo2 = json.dumps(jo)
            self.jobqueue.put((1, "setSettingData", jo2))


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


"""
#convert 2 dec values to hex and back to one dec value
"""


def twodectohextodec(dec1, dec2):
    Out32Bit = (dec1 << 16) | dec2;
    return Out32Bit


"""
#Open a new requests session
"""


def openSession():
    s = requests.Session()
    return s


"""
#Check Software Version on DVI
"""


def checkDVIVersion():
    counter = 0
    global DVIversionBot
    global DVIversionTop
    while True:
        time.sleep(2)
        try:
            SWBOT = modbusopen(16, 6, 154, 1)
            SWTOP = modbusopen(16, 6, 155, 1)
            SWBOT2 = float(chr(SWBOT[2]) + "." + chr(SWBOT[3]) + chr(SWBOT[4]))
            SWTOP2 = float(chr(SWTOP[2]) + "." + chr(SWTOP[3]) + chr(SWTOP[4]))
            if SWBOT2 == SWTOP2:
                version = SWTOP2
            else:
                if SWBOT2 < SWTOP2:
                    version = SWBOT2
                else:
                    version = SWTOP2
            DVIversionBot = SWBOT2
            DVIversionTop = SWTOP2

            return (version)
            break
        except:
            if debug == 1:
                dat = open(ErrorLog, 'a')
                error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  Check DVI Error\n")
                dat.write(error)
                dat.close()
            pass


"""
#Check for Pump ID and Accesstoken or set
"""


def getConfigFile():
    try:
        if os.path.isfile(ConfigFile):
            """
            if debug == 2:
                print("Make a new config file.")
            jobj = json.loads('{"pumpid": '+FabNR+', "accesstoken": ""}')
           
            jdata = {'pumpid': FabNR, 'accesstoken': ''}

                jobj['accesstoken'] = reqdata['accesstoken']
                jobj2 = json.dumps(jobj)
                add = jobj2
                subprocess.call(['mount -o remount,rw /'], shell=True)
                f = open(ConfigFile, 'w')
                f.write(jobj2)
                f.close()
          
                f2 = open(FabnrFile, 'w')
                f2.write(str(FABout))
                f2.close()
                subprocess.call(['mount -o remount,ro /'], shell=True)
                out = add
                """
            f = open(ConfigFile, 'r')
            jobj = json.loads(f.read())
            f.close()
            out = {"pumpid": jobj['pumpid'], "accesstoken": jobj['accesstoken']}

        else:
            if debug == 2:
                print("No Config file.")
            out = False

        return out
    except:
        pass


def preStartExecute():
    try:
        subprocess.call(['/bin/sh /home/code/dvi-net3/preinit.sh'], shell=True)
    except:
        print("Unable to execute preinit script")


"""
#Check for Pump ID and Accesstoken or set
"""


def checkFirstStart():
    FABconv2 = []
    while True:
        time.sleep(2)
        try:
            if not os.path.isfile(ConfigFile):
                if debug == 2:
                    print("Make a new config file.")
                jobj = json.loads('{"pumpid": 0, "accesstoken": ""}')
                FABNR = modbusopen(16, 6, 153, 1)
                FABconv = ("%0.2X" % (FABNR[3]), "%0.2X" % (FABNR[4]), "%0.2X" % (FABNR[5]))
                for ea in FABconv:
                    if ea == "0":
                        ea = "00"
                    if ea == "1":
                        ea = "01"
                    if ea == "2":
                        ea = "02"
                    if ea == "3":
                        ea = "03"
                    if ea == "4":
                        ea = "04"
                    if ea == "5":
                        ea = "05"
                    if ea == "6":
                        ea = "06"
                    if ea == "7":
                        ea = "07"
                    if ea == "8":
                        ea = "08"
                    if ea == "9":
                        ea = "09"
                    FABconv2.append(ea)
                FABarray = FABconv2[0] + FABconv2[1] + FABconv2[2]
                FABout = int(FABarray, 16)
                if debug == 2:
                    print(FABout)
                jobj['pumpid'] = FABout
                jdata = {'pumpid': FABout, 'accesstoken': jobj['accesstoken']}
                session = openSession()
                req = post(session, WebserviceURL, jdata)
                reqdata = req.json()
                if debug == 2:
                    print(reqdata)
                jobj['accesstoken'] = reqdata['accesstoken']
                jobj2 = json.dumps(jobj)
                subprocess.call(['mount -o remount,rw /'], shell=True)
                f = open(ConfigFile, 'w')
                f.write(jobj2)
                f.close()

                f2 = open(FabnrFile, 'w')
                f2.write(str(FABout))
                f2.close()
                subprocess.call(['mount -o remount,ro /'], shell=True)
                touch(PostTimePath)
            break
        except:
            if debug == 1:
                dat = open(ErrorLog, 'a')
                error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  Start Error\n")
                dat.write(error)
                dat.close()
            pass


"""
#Ask modbus about status
"""


def modbusopen(slave_adress, functioncode, starting_address, quantity):
    # logger = modbus_tk.utils.create_logger("console")

    time.sleep(waitMS)
    # master.set_verbose(True)
    # Set variable slave_adress
    slave_adress = int(slave_adress)

    # Set variable functioncode
    functioncode = int(functioncode)

    # Set variable starting_adress
    starting_adress = int(starting_address)

    # Set quantity_0f_x
    quantity = int(quantity)

    ##Set value
    try:
        if starting_adress == 151:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 152:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 153:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 154:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 155:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 171:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 172:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 173:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 174:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 337:
            output = master.execute(slave_adress, functioncode, 37, quantity, data_format='>H')
        elif starting_adress == 338:
            output = master.execute(slave_adress, functioncode, 38, quantity, data_format='>H')
        elif starting_adress == 325:
            output = master.execute(slave_adress, functioncode, 25, quantity, data_format='>H')
        elif starting_adress == 326:
            output = master.execute(slave_adress, functioncode, 26, quantity, data_format='>H')
        else:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity)
    except IndexError:
        pass
    if 'output' in locals():
        return output


"""
#Write new data to the modbus
"""


def modbuswrite(slave_adress, functioncode, starting_address, quantity, changeto):
    time.sleep(waitMS)

    # Set variable slave_adress
    slave_adress = int(slave_adress)

    # Set variable functioncode
    functioncode = int(functioncode)

    # Set variable starting_adress
    starting_adress = int(starting_address)

    # Set quantity_0f_x
    quantity = int(quantity)

    ##Set value
    try:
        value = changeto
        if starting_address < 210:
            starting_adress = (starting_adress + 256)

        if starting_adress == 151:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 152:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 153:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 154:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 155:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 171:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 172:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 173:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 174:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value, data_format="BBBBBB",
                                    expected_length=10)
        else:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, value)
    except IndexError:
        if starting_adress == 151:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 152:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 153:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 154:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 155:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBB",
                                    expected_length=10)
        elif starting_adress == 171:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 172:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 173:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        elif starting_adress == 174:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity, data_format="BBBBBB",
                                    expected_length=10)
        else:
            output = master.execute(slave_adress, functioncode, starting_adress, quantity)
    if 'output' in locals():
        return output


"""
#Start all timer threads in speedsettings
"""


def setTimer(pri, que, var):
    for ea in var:
        if ea == "getSystemBlocksData":
            e = TimerThread(1, que, ea, var[ea])
            TimerThread.start(e)
        else:
            e = TimerThread(pri, que, ea, var[ea])
            TimerThread.start(e)


"""
#These is how a timer thread looks like
"""


class TimerThread(threading.Thread):

    def __init__(self, prior, jobqueue, name, speed):
        threading.Thread.__init__(self)
        self.name = name
        self.jobqueue = jobqueue
        self.speed = speed
        self.prior = prior

    def run(self):
        while True:
            self.jobqueue.put((self.prior, self.name))
            time.sleep(self.speed)
            if (self.prior == 2) & (online == 0):
                break


class PingThread(threading.Thread):

    def __init__(self, sendqueue, pingtiming):
        threading.Thread.__init__(self)
        self.sendqueue = sendqueue
        self.pingtiming = pingtiming

    def run(self):
        while True:
            output = {"Ping": 0}
            jsonres = json.dumps(output)
            self.sendqueue.put(jsonres)
            time.sleep(self.pingtiming)


class NetOfflineThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            if netoffline:
                time.sleep(timenetoffline)
                if netoffline:
                    subprocess.call(['systemctl stop DVI-net'], shell=True)
                break
            time.sleep(10)


class ErrorThread(threading.Thread):

    def __init__(self, prior, jobqueue, name, speed):
        threading.Thread.__init__(self)
        self.jobqueue = jobqueue
        self.name = name
        self.speed = speed
        self.prior = prior

    def run(self):
        global olderror
        firststart = True
        while True:
            if firststart:
                self.jobqueue.put((self.prior, self.name))
                firststart = False
            if netoffline:
                olderror = 5

            if (errorrelay == 1) | (olderror > 0):
                if (errorrelay == 1):
                    olderror = 5
                self.jobqueue.put((self.prior, self.name))
                olderror = olderror - 1
            time.sleep(self.speed)


def ping(host):
    """
    Returns True if host responds to a ping request
    """
    import os, platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"

    # Ping
    return os.system("ping " + ping_str + " " + host) == 0


"""
#This Class do if there is net connection set modbus to 1 else 2
"""


class InetThread(threading.Thread):

    def __init__(self, jobqueue, NetStatusQueue):
        threading.Thread.__init__(self)
        self.jobqueue = jobqueue
        self.NetStatusQueue = NetStatusQueue
        self.name = "setNet"
        self.speed = 30
        self.prior = 2

    def get_default_gateway_linux(self):
        # Read route
        try:
            with open("/proc/net/route") as fh:
                for line in fh:
                    fields = line.strip().split()
                    if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                        continue

                    g = socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

            out = g.split(".")
            return out
        except Exception as e:
            print(e)
            g = "0.0.0.0"
            out = g.split(".")
            return out

    def get_default_dns_linux(self):
        # Open the file for reading.
        try:
            data = subprocess.check_output("cat /etc/resolv.conf|grep -im 1 '^nameserver' |cut -d ' ' -f2",
                                           shell=True).decode('utf-8')
            b = data.replace('\n', '')
            if b == "":
                b = "0.0.0.0"
        except:
            b = "0.0.0.0"
            pass
        out = b.split(".")
        return out

    def get_ip_address(self, ifname):
        try:
            g = subprocess.check_output('hostname -I', shell=True).decode('utf-8')
            g = g.replace('\n', '')
            if g == "":
                g = "0.0.0.0"


        except:
            g = "0.0.0.0"
            pass
        out = g.split(".")
        return out

    def run(self):
        global netoffline
        pingoldvalue = False
        netold = {"a": 1}
        while True:
            try:
                # Get net state from dvi display
                self.jobqueue.put((self.prior, "getNetStatus"))

                # ping dvi server
                pingvalue = ServerConnection

                # Get default gateway
                gate = self.get_default_gateway_linux()

                # Get DNS Server
                dns = self.get_default_dns_linux()

                # Get IP

                interfaces = subprocess.Popen('ls /sys/class/net/', shell=True, stdout=subprocess.PIPE)
                interf = interfaces.stdout.read()
                interf = interf.decode()
                intface = tuple(interf.split('\n')[:-1])
                ip = self.get_ip_address(intface[0])

                # Put all data into JSON
                net = {"ip": ip, "gateway": gate, "dns": dns}

                time.sleep(5)

                NetStatus = self.NetStatusQueue.get()
                jobj = json.loads(NetStatus)

                if jobj["NetStatus"] == "unknown":
                    pingoldvalue = False

                elif jobj["NetStatus"] == "off":
                    pingoldvalue = False

                elif jobj["NetStatus"] == "on":
                    pingoldvalue = True

                if pingvalue and pingoldvalue:
                    # check if ip, gatgeway, dns are the same, if not set new value
                    if netold != net:
                        jout = json.dumps(net)
                        self.jobqueue.put((self.prior, "setIP", jout))
                        netold = net


                elif pingvalue and not pingoldvalue:

                    # set network led on
                    self.jobqueue.put((self.prior, "setNetOn"))
                    pingoldvalue = pingvalue

                    # set ip, gateway, dns
                    jout = json.dumps(net)
                    self.jobqueue.put((self.prior, "setIP", jout))
                    netold = net

                elif not pingvalue and pingoldvalue:

                    # set network led off
                    self.jobqueue.put((self.prior, "setNetOff"))
                    pingoldvalue = pingvalue

                    # set ip, gateway, dns
                    jout = json.dumps(net)
                    self.jobqueue.put((self.prior, "setIP", jout))
                    netold = net

                elif not pingvalue and not pingoldvalue:

                    # check if ip, gatgeway, dns are the same, if not set new value
                    if netold != net:
                        jout = json.dumps(net)
                        self.jobqueue.put((self.prior, "setIP", jout))
                        netold = net

                time.sleep(self.speed)
                pass
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " -> UserData Error\n")
                    dat.write(error)
                    dat.close()
                time.sleep(self.speed)
                pass


"""
#Class Job is to make a priority queue with priority and description
"""


class Job(object):
    def __init__(self, priority, description):
        self.priority = priority
        self.description = description
        return

    def __cmp__(self, other):
        return [(self.priority > other.priority) - (self.priority < other.priority)]


"""
#Class Job2 is to make a priority queue with priority and two descriptions
"""


class Job2(object):
    def __init__(self, priority, description, description2):
        self.priority = priority
        self.description = description
        self.description2 = description2
        return

    def __cmp__(self, other):
        return [(self.priority > other.priority) - (self.priority < other.priority)]


"""
#In these class you can find all functions this software can do
"""


def getWatchdogStatus():
    try:
        return subprocess.run(["systemctl", "is-active", "--quiet", "dvi_watchdog"], timeout=10).returncode
    except:
        return -1

def getWatchdogLog():
    try:
        try:
            return subprocess.check_output(["systemctl status dvi_watchdog"], timeout=10, shell=True, stderr=subprocess.STDOUT).decode("utf-8")
        except subprocess.CalledProcessError as cpe:
            return cpe.output.decode("utf-8")
        except Exception as ex:
            return ""
    except:
        return ""

def getOSId():
    try:
        d = {}
        with open("/etc/os-release") as f:
            for line in f:
                k, v = line.rstrip().split("=")
                d[k] = v
        return d["ID"].replace('"', '')
    except:
        return "unknown"


def getOSUptime():
    try:
        return int(time.monotonic())
    except:
        return 0


def getOSBootTime(uptime):
    try:
        return datetime.utcfromtimestamp(time.time() - uptime).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ""


def getProcessUptime():
    try:
        return int(time.time() - startTime)
    except:
        return 0

def getProcessBootTime():
    try:
        return datetime.utcfromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return 0


class WaitingThread(threading.Thread):

    # This Thread is waiting for Jobs.

    def __init__(self, jobqueue, sendqueue, NetStatusQueue, slavesendequeue):
        # Take Jobs Queue
        threading.Thread.__init__(self)
        self.sendqueue = sendqueue
        self.NetStatusQueue = NetStatusQueue
        self.jobqueue = jobqueue
        self.slavesendequeue = slavesendequeue
        self.var = 0
        # cache til systemstatus, så vi kan undgå tunge modbuskald ved senere læsninger
        self._cached_systemstatus: dict | None = None

    def run(self):
        pause = False
        # 'run' is the function you start with 'Waiting.Thread.start()'
        # Here we wait for a Job in the Queue

        while True:
            if pause == False:
                anweisung = self.jobqueue.get()

                if len(anweisung) == 3:
                    getattr(self, anweisung[1])(anweisung[2], dictSettingList)

                elif len(anweisung) == 2:
                    getattr(self, anweisung[1])()

    def doJob(self):
        if not self.jobqueue.empty():

            anweisung = self.jobqueue.get()
            if len(anweisung) == 3:

                getattr(self, anweisung[1])(anweisung[2], dictSettingList)

            elif len(anweisung) == 2:

                getattr(self, anweisung[1])()
        else:
            pass

    """
    check for DVI Net updates
    """

    def makeSWupdate(self):
        self.pause = True
        while True:
            try:
                subprocess.call(['service DVI-Net.sh update'], shell=True)
                break
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  makeSWupdate Error\n")
                    dat.write(error)
                    dat.close()
                break

        self.pause = False

    def setIP(self, desc2, dictSettingList):
        self.pause = True

        jin = json.loads(desc2)

        while True:
            try:
                modbuswrite(16, 6, 211, 1, int(jin["ip"][0]))
                modbuswrite(16, 6, 212, 1, int(jin["ip"][1]))
                modbuswrite(16, 6, 213, 1, int(jin["ip"][2]))
                modbuswrite(16, 6, 214, 1, int(jin["ip"][3]))

                modbuswrite(16, 6, 215, 1, int(jin["gateway"][0]))
                modbuswrite(16, 6, 216, 1, int(jin["gateway"][1]))
                modbuswrite(16, 6, 217, 1, int(jin["gateway"][2]))
                modbuswrite(16, 6, 218, 1, int(jin["gateway"][3]))

                modbuswrite(16, 6, 219, 1, int(jin["dns"][0]))
                modbuswrite(16, 6, 220, 1, int(jin["dns"][1]))
                modbuswrite(16, 6, 221, 1, int(jin["dns"][2]))
                modbuswrite(16, 6, 222, 1, int(jin["dns"][3]))
                break
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  setIP Error\n")
                    dat.write(error)
                    dat.close()
                break

        self.pause = False

    def getNetStatus(self):
        self.pause = True
        while True:
            try:

                req = modbusopen(16, 6, 210, 1)

                if req[1] == 0:
                    req = "unknown"
                elif req[1] == 1:
                    req = "on"
                elif req[1] == 2:
                    req = "off"
                output = {"NetStatus": req}
                jsonres = json.dumps(output)
                self.NetStatusQueue.put(jsonres)
                break
            except:
                req = "unknown"
                output = {"NetStatus": req}
                jsonres = json.dumps(output)
                self.NetStatusQueue.put(jsonres)
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  setNetOn Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False

    def setNetOn(self):
        self.pause = True
        while True:
            try:

                modbuswrite(16, 6, 466, 1, 1)
                break

            except Exception as e:
                print(e)
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  setNetOn Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False

    def setNetOff(self):
        self.pause = True
        while True:
            try:

                modbuswrite(16, 6, 466, 1, 2)

                break
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  setNetOff Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False

    def getSensorData(self):
        self.pause = True
        _dbg("getSensorData: start")
        while True:
            try:
                F1 = modbusopen(16, 4, 1, 1)
                F2 = modbusopen(16, 4, 2, 1)
                F3 = modbusopen(16, 4, 3, 1)
                F4 = modbusopen(16, 4, 4, 1)
                F5 = modbusopen(16, 4, 5, 1)
                F6 = modbusopen(16, 4, 6, 1)
                F7 = modbusopen(16, 4, 7, 1)
                F8 = modbusopen(16, 4, 8, 1)
                F9 = modbusopen(16, 4, 9, 1)
                F10 = modbusopen(16, 4, 10, 1)
                F11 = modbusopen(16, 4, 11, 1)
                F12 = modbusopen(16, 4, 12, 1)
                F13 = modbusopen(16, 4, 13, 1)
                F14 = modbusopen(16, 4, 14, 1)

                if F1[0] > 30000:
                    F1 = ((65536 - F1[0]) * -1)
                else:
                    F1 = F1[0]

                if F2[0] > 30000:
                    F2 = ((65536 - F2[0]) * -1)
                else:
                    F2 = F2[0]

                if F3[0] > 30000:
                    F3 = ((65536 - F3[0]) * -1)
                else:
                    F3 = F3[0]

                if F4[0] > 30000:
                    F4 = ((65536 - F4[0]) * -1)
                else:
                    F4 = F4[0]

                if F5[0] > 30000:
                    F5 = ((65536 - F5[0]) * -1)
                else:
                    F5 = F5[0]

                if F6[0] > 30000:
                    F6 = ((65536 - F6[0]) * -1)
                else:
                    F6 = F6[0]

                if F7[0] > 30000:
                    F7 = ((65536 - F7[0]) * -1)
                else:
                    F7 = F7[0]

                if F8[0] > 30000:
                    F8 = ((65536 - F8[0]) * -1)
                else:
                    F8 = F8[0]

                if F9[0] > 30000:
                    F9 = ((65536 - F9[0]) * -1)
                else:
                    F9 = F9[0]

                if F10[0] > 30000:
                    F10 = ((65536 - F10[0]) * -1)
                else:
                    F10 = F10[0]

                if F11[0] > 30000:
                    F11 = ((65536 - F11[0]) * -1)
                else:
                    F11 = F11[0]

                if F12[0] > 30000:
                    F12 = ((65536 - F12[0]) * -1)
                else:
                    F12 = F12[0]

                if F13[0] > 30000:
                    F13 = ((65536 - F13[0]) * -1)
                else:
                    F13 = F13[0]

                if F14[0] > 30000:
                    F14 = ((65536 - F14[0]) * -1)
                else:
                    F14 = F14[0]

                S_1_M1 = modbusopen(16, 4, 17, 1)
                S_1_M2 = modbusopen(16, 4, 18, 1)
                S_1_M = twodectohextodec(S_1_M1[0], S_1_M2[0])

                S_2_M1 = modbusopen(16, 4, 19, 1)
                S_2_M2 = modbusopen(16, 4, 20, 1)
                S_2_M = twodectohextodec(S_2_M1[0], S_2_M2[0])

                S_3_M1 = modbusopen(16, 4, 21, 1)
                S_3_M2 = modbusopen(16, 4, 22, 1)
                S_3_M = twodectohextodec(S_3_M1[0], S_3_M2[0])

                S_4_M1 = modbusopen(16, 4, 23, 1)
                S_4_M2 = modbusopen(16, 4, 24, 1)
                S_4_M = twodectohextodec(S_4_M1[0], S_4_M2[0])

                S_5_M1 = modbusopen(16, 4, 325, 1)
                S_5_M2 = modbusopen(16, 4, 326, 1)
                S_5_M = twodectohextodec(S_5_M1[0], S_5_M2[0])

                DezimalFlow = modbusopen(16, 4, 27, 1)

                DezimalPower = modbusopen(16, 4, 28, 1)

                DezimalHeatEnergy = modbusopen(16, 4, 29, 1)

                S101 = modbusopen(16, 4, 31, 1)
                S102 = modbusopen(16, 4, 32, 1)
                S10 = twodectohextodec(S101[0], S102[0])

                S111 = modbusopen(16, 4, 33, 1)
                S112 = modbusopen(16, 4, 34, 1)
                S11 = twodectohextodec(S111[0], S112[0])

                S121 = modbusopen(16, 4, 35, 1)
                S122 = modbusopen(16, 4, 36, 1)
                S12 = twodectohextodec(S121[0], S122[0])

                S131 = modbusopen(16, 4, 337, 1)
                S132 = modbusopen(16, 4, 338, 1)
                S13 = twodectohextodec(S131[0], S132[0])

                if (DezimalHeatEnergy[0] == 1):

                    S_5_M = S_5_M * 100

                elif (DezimalHeatEnergy[0] == 2):

                    S_5_M = S_5_M * 10

                elif (DezimalHeatEnergy[0] == 3):

                    S_5_M = S_5_M

                elif (DezimalHeatEnergy[0] == 4):

                    S_5_M = S_5_M / 10

                output = {'sensordata': {'F1': F1, 'F2': F2, 'F3': F3, 'F4': F4, 'F5': F5, 'F6': F6, 'F7': F7, 'F8': F8,
                                         'F9': F9, 'F10': F10, 'F11': F11, 'F12': F12, 'F13': F13, 'F14': F14,
                                         'S_1_M': S_1_M, 'S_2_M': S_2_M, 'S_3_M': S_3_M, 'S_4_M': S_4_M, 'S_5_M': S_5_M,
                                         'DeziFlow': DezimalFlow[0], 'DeziPower': DezimalPower[0],
                                         'DeziHeatEnergy': DezimalHeatEnergy[0], 'S10': S10, 'S11': S11, 'S12': S12,
                                         'S13': S13}}
                _dbg(f"getSensorData: output={json.dumps(output, ensure_ascii=False)}")
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  SensorData Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False

    def getRelayData(self):
        self.pause = True
        global errorrelay
        global olderror
        _dbg("getRelayData: start")
        while True:
            try:
                get_bin = lambda x, n: x >= 0 and str(bin(x))[2:].zfill(n) or "-" + str(bin(x))[3:].zfill(n)
                RLYLIST2 = modbusopen(16, 1, 1, 16)
                KASKADEonLIST = modbusopen(16, 6, 209, 1)
                _dbg(f"getRelayData: raw coils={RLYLIST2}, kask={KASKADEonLIST}")

                if (RLYLIST2[9] == 1):
                    errorrelay = 1
                    if olderror == 0:
                        olderror = 1
                if (RLYLIST2[9] == 0):
                    errorrelay = 0

                output = {'KASKADEonLIST': KASKADEonLIST[1],
                          'relaydata': {'RLY1': RLYLIST2[8], 'RLY2': RLYLIST2[9], 'RLY3': RLYLIST2[10],
                                        'RLY4': RLYLIST2[11], 'RLY5': RLYLIST2[12], 'RLY6': RLYLIST2[13],
                                        'RLY7': RLYLIST2[14],
                                        'RLY8': RLYLIST2[15], 'RLY9': RLYLIST2[0], 'RLY10': RLYLIST2[1],
                                        'RLY11': RLYLIST2[2], 'RLY12': RLYLIST2[3], 'RLY13': RLYLIST2[4],
                                        'RLY14': RLYLIST2[5]}}
                _dbg(f"getRelayData: output={json.dumps(output, ensure_ascii=False)}")
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                # ...existing error logging...
                break
        self.pause = False

    def getUserData(self):
        self.pause = True
        _dbg("getUserData: start")
        while True:
            try:
                B1 = modbusopen(16, 6, 1, 1)
                B2 = modbusopen(16, 6, 2, 1)
                B3 = modbusopen(16, 6, 3, 1)
                B4 = modbusopen(16, 6, 4, 1)
                B5 = modbusopen(16, 6, 5, 1)
                B5 = list(B5)
                B5[1] = (B5[1] + 50)
                B6 = modbusopen(16, 6, 6, 1)
                B10 = modbusopen(16, 6, 10, 1)
                B11 = modbusopen(16, 6, 11, 1)
                B12 = modbusopen(16, 6, 12, 1)
                B15 = modbusopen(16, 6, 15, 1)
                DVI40 = modbusopen(16, 6, 85, 1)
                PUMPSTATUS = modbuswrite(16, 6, 156, 1, 0)
                CURVETEMP = modbusopen(16, 6, 208, 1)

                _dbg(f"getUserData: raw B1..B15={B1,B2,B3,B4,B5,B6,B10,B11,B12,B15}, "
                     f"DVI40={DVI40}, PUMPSTATUS={PUMPSTATUS}, CURVETEMP={CURVETEMP}")

                if (PUMPSTATUS[1] == 2):
                    self.jobqueue.put((1, "getSystemBlocksData"))

                output = {'userdata': {'B1': B1[1], 'B2': B2[1], 'B3': B3[1], 'B4': B4[1], 'B5': B5[1], 'B6': B6[1],
                                       'B10': B10[1], 'B11': B11[1],
                                       'B12': B12[1], 'B15': B15[1], 'CURVETEMP': CURVETEMP[1]},
                          'admindata': {'DVI40': DVI40[1]}, 'PUMPSTATUS': PUMPSTATUS[1]}
                _dbg(f"getUserData: output={json.dumps(output, ensure_ascii=False)}")
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                # ...existing error logging...
                break
        self.pause = False

    def getMonteurData(self):
        self.pause = True
        global ModbusServer
        _dbg("getMonteurData: start")
        while True:
            try:
                M1 = modbusopen(16, 6, 21, 1)
                M2 = modbusopen(16, 6, 22, 1)
                M3 = modbusopen(16, 6, 23, 1)
                M4 = modbusopen(16, 6, 24, 1)
                M5 = modbusopen(16, 6, 25, 1)
                M6 = modbusopen(16, 6, 26, 1)
                M7 = modbusopen(16, 6, 27, 1)
                M8 = modbusopen(16, 6, 28, 1)
                M11 = modbusopen(16, 6, 31, 1)
                M12 = modbusopen(16, 6, 32, 1)
                M13 = modbusopen(16, 6, 33, 1)
                M16 = modbusopen(16, 6, 36, 1)
                M17 = modbusopen(16, 6, 37, 1)
                M19 = modbusopen(16, 6, 39, 1)
                M21 = modbusopen(16, 6, 41, 1)
                M22 = modbusopen(16, 6, 42, 1)

                raw_map = {"M1": M1, "M2": M2, "M3": M3, "M4": M4, "M5": M5, "M6": M6, "M7": M7, "M8": M8,
                           "M11": M11, "M12": M12, "M13": M13, "M16": M16, "M17": M17, "M19": M19, "M21": M21, "M22": M22}
                _dbg(f"getMonteurData: raw={raw_map}")

                if M17[1] == 0:
                    ModbusServer = 0
                else:
                    ModbusServer = M17[1]

                output = {'monteurdata': {'M1': M1[1], 'M2': M2[1], 'M3': M3[1], 'M4': M4[1], 'M5': M5[1], 'M6': M6[1],
                                          'M7': M7[1], 'M8': M8[1],
                                          'M11': M11[1], 'M12': M12[1], 'M13': M13[1], 'M16': M16[1], 'M17': M17[1],
                                          'M19': M19[1], 'M21': M21[1], 'M22': M22[1]}}
                _dbg(f"getMonteurData: output={json.dumps(output, ensure_ascii=False)}")
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                # ...existing error logging...
                break
        self.pause = False

    def getSystemStatusData(self, force: bool = False):
        """
        Læser systemstatusdata (INDA/SEDA/FABNR/SWBOT/SWTOP + OS/watchdog),
        som i den oprindelige kode.

        Hvis force=False og vi allerede har et cachet output i denne instans,
        genbruges det uden nye modbuskald. Brug force=True ved første scanning
        (fx i legacy_payload_builder) og force=False ved senere kald for at
        undgå ~16s modbus-timeouts.
        """
        self.pause = True
        global DVIversionBot
        global DVIversionTop
        global SpeedSettings
        global FabNR
        FABconv2 = []
        _dbg(f"getSystemStatusData: start (force={force})")

        # Brug cache hvis vi ikke er tvunget til at refreshe
        if not force and self._cached_systemstatus is not None:
            _dbg("getSystemStatusData: using cached systemstatusdata")
            jsonres = json.dumps(self._cached_systemstatus)
            self.sendqueue.put(jsonres)
            self.pause = False
            return

        t0 = time.time()
        while True:
            # 1) watchdog + OS info
            watchdogstate = getWatchdogStatus()
            if watchdogstate != 0:
                watchdogstatelog = getWatchdogLog()
            else:
                watchdogstatelog = ""
            t1 = time.time()
            osid = getOSId()
            systemuptime = getOSUptime()
            systemboottime = getOSBootTime(systemuptime)
            processuptime = getProcessUptime()
            processboottime = getProcessBootTime()
            t2 = time.time()

            _dbg(
                f"getSystemStatusData: timings watchdog+log={t1-t0:.3f}s, "
                f"os/process info={t2-t1:.3f}s"
            )

            try:
                # 2) Modbus system status registre
                t3 = time.time()
                INDA = modbusopen(16, 6, 151, 1)
                SEDA = modbusopen(16, 6, 152, 1)
                FABNR = modbusopen(16, 6, 153, 1)
                SWBOT = modbusopen(16, 6, 154, 1)
                SWTOP = modbusopen(16, 6, 155, 1)
                t4 = time.time()

                _dbg(
                    f"getSystemStatusData: modbus 151–155 took {t4-t3:.3f}s, "
                    f"raw INDA={INDA}, SEDA={SEDA}, FABNR={FABNR}, SWBOT={SWBOT}, SWTOP={SWTOP}"
                )

                SWBOT2 = float(chr(SWBOT[2]) + "." + chr(SWBOT[3]) + chr(SWBOT[4]))
                SWTOP2 = float(chr(SWTOP[2]) + "." + chr(SWTOP[3]) + chr(SWTOP[4]))
                DVIversionBot = SWBOT2
                DVIversionTop = SWTOP2
                FABconv = (hex(FABNR[3])[2:], hex(FABNR[4])[2:], hex(FABNR[5])[2:])
                for ea in FABconv:
                    if ea == "1":
                        ea = "01"
                    if ea == "2":
                        ea = "02"
                    if ea == "3":
                        ea = "03"
                    if ea == "4":
                        ea = "04"
                    if ea == "5":
                        ea = "05"
                    if ea == "6":
                        ea = "06"
                    if ea == "7":
                        ea = "07"
                    if ea == "8":
                        ea = "08"
                    if ea == "9":
                        ea = "09"
                    FABconv2.append(ea)
                FABarray = FABconv2[0] + FABconv2[1] + FABconv2[2]
                FABout = int(FABarray, 16)
                FabNR = FABout
                t5 = time.time()

                _dbg(
                    f"getSystemStatusData: version/FAB parsing took {t5-t4:.3f}s, "
                    f"total={t5-t0:.3f}s"
                )

                output = {
                    'systemstatusdata': {
                        'SWPI': Version,
                        'WD': watchdogstate,
                        'WDLOG': watchdogstatelog,
                        'OS': osid,
                        'SWUP': processuptime,
                        'SWBOOT': processboottime,
                        'PIUP': systemuptime,
                        'PIBOOT': systemboottime,
                        'INSTDA': {'DD': INDA[2], 'MM': INDA[3], 'YY': INDA[4]},
                        'SERVDA': {'DD': SEDA[2], 'MM': SEDA[3], 'YY': SEDA[4]},
                        'FABNR': FABout,
                        'SWBOT': SWBOT2,
                        'SWTOP': SWTOP2
                    }
                }
                _dbg(f"getSystemStatusData: output={json.dumps(output, ensure_ascii=False)}")

                # cache resultatet til senere ikke-force kald
                self._cached_systemstatus = output

                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                output = {'systemstatusdata': {'SWPI': Version, 'WD': watchdogstate, 'WDLOG': watchdogstatelog, 'OS': osid, 'SWUP': processuptime,
                                               'SWBOOT': processboottime, 'PIUP': systemuptime, 'PIBOOT': systemboottime,
                                               'INSTDA': {'DD': 0, 'MM': 0, 'YY': 0},
                                               'SERVDA': {'DD': 0, 'MM': 0, 'YY': 0}, 'FABNR': 000000,
                                               'SWBOT': 0.00, 'SWTOP': 0.00}}
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                self.jobqueue.put((1, "getSystemStatusData"))

                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  SystemStatusData Error\n")
                    dat.write(error)
                    dat.close()
                time.sleep(10)
                break
        self.pause = False

    def getSystemTimeData(self):
        self.pause = True
        _dbg("getSystemTimeData: start")
        while True:
            try:
                KOMT = modbusopen(16, 6, 161, 1)
                VARMVT = modbusopen(16, 6, 162, 1)
                TILSKT = modbusopen(16, 6, 163, 1)
                ENERGFT = modbusopen(16, 6, 164, 1)
                SOLVT = modbusopen(16, 6, 165, 1)
                SOLTJT = modbusopen(16, 6, 166, 1)
                KOELEFT = modbusopen(16, 6, 167, 1)

                _dbg(f"getSystemTimeData: raw KOMT..KOELEFT="
                     f"{KOMT,VARMVT,TILSKT,ENERGFT,SOLVT,SOLTJT,KOELEFT}")

                output = {
                    'systemtime': {'KOMT': KOMT[1], 'VARMVT': VARMVT[1], 'TILSKT': TILSKT[1], 'ENERGFT': ENERGFT[1],
                                   'SOLVT': SOLVT[1], 'SOLTJT': SOLTJT[1], 'KOELEFT': KOELEFT[1]}}
                _dbg(f"getSystemTimeData: output={json.dumps(output, ensure_ascii=False)}")
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  SystemTimeData Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False

    def getSpecialBlocksData(self):
        self.pause = True
        _dbg("getSpecialBlocksData: start")
        while True:
            try:
                BLOCK3 = modbusopen(16, 6, 180, 1)
                BLOCK5 = modbusopen(16, 6, 175, 1)
                BLOCK23 = modbusopen(16, 6, 176, 1)
                BLOCK25 = modbusopen(16, 6, 177, 1)
                BLOCK67 = modbusopen(16, 6, 178, 1)
                BLOCK115 = modbusopen(16, 6, 179, 1)

                _dbg(f"getSpecialBlocksData: raw "
                     f"BLOCK3={BLOCK3}, BLOCK5={BLOCK5}, BLOCK23={BLOCK23}, "
                     f"BLOCK25={BLOCK25}, BLOCK67={BLOCK67}, BLOCK115={BLOCK115}")

                output = {'specialblocks': {'BLOCK3': BLOCK3[1], 'BLOCK5': BLOCK5[1], 'BLOCK23': BLOCK23[1],
                                            'BLOCK25': BLOCK25[1], 'BLOCK67': BLOCK67[1], 'BLOCK115': BLOCK115[1]}}
                _dbg(f"getSpecialBlocksData: output={json.dumps(output, ensure_ascii=False)}")
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  SpecialBlocksData Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False

    def getSystemBlocksData(self):
        self.pause = True
        _dbg("getSystemBlocksData: start")
        while True:
            try:
                get_bin = lambda x, n: x >= 0 and str(bin(x))[2:].zfill(n) or "-" + str(bin(x))[3:].zfill(n)
                out = []
                out2 = []
                out3 = []
                out4 = []
                BLOCK1 = modbusopen(16, 6, 171, 1)
                BLOCK2 = modbusopen(16, 6, 172, 1)
                BLOCK3 = modbusopen(16, 6, 173, 1)
                BLOCK4 = modbusopen(16, 6, 174, 1)

                _dbg(f"getSystemBlocksData: raw BLOCK1={BLOCK1}, BLOCK2={BLOCK2}, "
                     f"BLOCK3={BLOCK3}, BLOCK4={BLOCK4}")

                i = 1
                while i <= 4:
                    out.append(get_bin(BLOCK1[1 + i], 8))
                    out2.append(get_bin(BLOCK2[1 + i], 8))
                    out3.append(get_bin(BLOCK3[1 + i], 8))
                    out4.append(get_bin(BLOCK4[1 + i], 8))
                    i = i + 1
                ALL = list(
                    out4[0] + out4[1] + out4[2] + out4[3] + out3[0] + out3[1] + out3[2] + out3[3] + out2[0] + out2[1] +
                    out2[2] + out2[3] + out[0] + out[1] + out[2] + out[3])
                o = list(map(int, ALL))
                output = {'systemblocks':
                              {'SBLOCK1': o[127], 'SBLOCK2': o[126], 'SBLOCK3': o[125], 'SBLOCK4': o[124],
                               'SBLOCK5': o[123], 'SBLOCK6': o[122], 'SBLOCK7': o[121], 'SBLOCK8': o[120],
                               'SBLOCK9': o[119], 'SBLOCK10': o[118], 'SBLOCK11': o[117], 'SBLOCK12': o[116],
                               'SBLOCK13': o[115], 'SBLOCK14': o[114], 'SBLOCK15': o[113], 'SBLOCK16': o[112],
                               'SBLOCK17': o[111], 'SBLOCK18': o[110], 'SBLOCK19': o[109], 'SBLOCK20': o[108],
                               'SBLOCK21': o[107], 'SBLOCK22': o[106], 'SBLOCK23': o[105], 'SBLOCK24': o[104],
                               'SBLOCK25': o[103], 'SBLOCK26': o[102], 'SBLOCK27': o[101], 'SBLOCK28': o[100],
                               'SBLOCK29': o[99], 'SBLOCK30': o[98], 'SBLOCK31': o[97], 'SBLOCK32': o[96],
                               'SBLOCK33': o[95], 'SBLOCK34': o[94], 'SBLOCK35': o[93], 'SBLOCK36': o[92],
                               'SBLOCK37': o[91], 'SBLOCK38': o[90], 'SBLOCK39': o[89], 'SBLOCK40': o[88],
                               'SBLOCK41': o[87], 'SBLOCK42': o[86], 'SBLOCK43': o[85], 'SBLOCK44': o[84],
                               'SBLOCK45': o[83], 'SBLOCK46': o[82], 'SBLOCK47': o[81], 'SBLOCK48': o[80],
                               'SBLOCK49': o[79], 'SBLOCK50': o[78], 'SBLOCK51': o[77], 'SBLOCK52': o[76],
                               'SBLOCK53': o[75], 'SBLOCK54': o[74], 'SBLOCK55': o[73], 'SBLOCK56': o[72],
                               'SBLOCK57': o[71], 'SBLOCK58': o[70], 'SBLOCK59': o[69], 'SBLOCK60': o[68],
                               'SBLOCK61': o[67], 'SBLOCK62': o[66], 'SBLOCK63': o[65], 'SBLOCK64': o[64],
                               'SBLOCK65': o[63], 'SBLOCK66': o[62], 'SBLOCK67': o[61], 'SBLOCK68': o[60],
                               'SBLOCK69': o[59], 'SBLOCK70': o[58], 'SBLOCK71': o[57], 'SBLOCK72': o[56],
                               'SBLOCK73': o[55], 'SBLOCK74': o[54], 'SBLOCK75': o[53], 'SBLOCK76': o[52],
                               'SBLOCK77': o[51], 'SBLOCK78': o[50], 'SBLOCK79': o[49], 'SBLOCK80': o[48],
                               'SBLOCK81': o[47], 'SBLOCK82': o[46], 'SBLOCK83': o[45], 'SBLOCK84': o[44],
                               'SBLOCK85': o[43], 'SBLOCK86': o[42], 'SBLOCK87': o[41], 'SBLOCK88': o[40],
                               'SBLOCK89': o[39], 'SBLOCK90': o[38], 'SBLOCK91': o[37], 'SBLOCK92': o[36],
                               'SBLOCK93': o[35], 'SBLOCK94': o[34], 'SBLOCK95': o[33], 'SBLOCK96': o[32],
                               'SBLOCK97': o[31], 'SBLOCK98': o[30], 'SBLOCK99': o[29], 'SBLOCK100': o[28],
                               'SBLOCK101': o[27], 'SBLOCK102': o[26], 'SBLOCK103': o[25], 'SBLOCK104': o[24],
                               'SBLOCK105': o[23], 'SBLOCK106': o[22], 'SBLOCK107': o[21], 'SBLOCK108': o[20],
                               'SBLOCK109': o[19], 'SBLOCK110': o[18], 'SBLOCK111': o[17], 'SBLOCK112': o[16],
                               'SBLOCK113': o[15], 'SBLOCK114': o[14], 'SBLOCK115': o[13], 'SBLOCK116': o[12],
                               'SBLOCK117': o[11], 'SBLOCK118': o[10], 'SBLOCK119': o[9], 'SBLOCK120': o[8],
                               'SBLOCK121': o[7], 'SBLOCK122': o[6], 'SBLOCK123': o[5], 'SBLOCK124': o[4],
                               'SBLOCK125': o[3], 'SBLOCK126': o[2], 'SBLOCK127': o[1], 'SBLOCK128': o[0]
                               }
                          }
                _dbg(f"getSystemBlocksData: first 16 bits={o[:16]}")
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                # ...existing error logging...
                break
        self.pause = False

    def setSettingData(self, desc2, dictSettingList):
        self.pause = True
        errorcounter = 0
        _dbg("setSettingData: start")
        while True:
            try:
                output = []
                dictUpdateList = json.loads(desc2)

                if "B5" in dictUpdateList:
                    dictUpdateList['B5']['set'] = (int(dictUpdateList['B5']['set']) - 50)
                if "DVI10" in dictUpdateList:
                    dictUpdateList['DVI10']['set'] = (int(dictUpdateList['DVI10']['set']) + 20)
                if "DVI22" in dictUpdateList:
                    dictUpdateList['DVI22']['set'] = (int(dictUpdateList['DVI22']['set']) + 10)
                if "DVI26" in dictUpdateList:
                    dictUpdateList['DVI26']['set'] = (int(dictUpdateList['DVI26']['set']) + 50)
                if "DVI27" in dictUpdateList:
                    dictUpdateList['DVI27']['set'] = (int(dictUpdateList['DVI27']['set']) + 5)
                if "DVI54" in dictUpdateList:
                    dictUpdateList['DVI54']['set'] = (int(dictUpdateList['DVI54']['set']) + 10)
                if "DVI55" in dictUpdateList:
                    dictUpdateList['DVI55']['set'] = (int(dictUpdateList['DVI55']['set']) + 20)
                if "DVI56" in dictUpdateList:
                    dictUpdateList['DVI56']['set'] = (int(dictUpdateList['DVI56']['set']) + 20)
                if "DVI57" in dictUpdateList:
                    dictUpdateList['DVI57']['set'] = (int(dictUpdateList['DVI57']['set']) + 20)
                if "DVI60" in dictUpdateList:
                    dictUpdateList['DVI60']['set'] = (int(dictUpdateList['DVI60']['set']) + 2)
                if "DVI64" in dictUpdateList:
                    dictUpdateList['DVI64']['set'] = (int(dictUpdateList['DVI64']['set']) + 5)
                if "DVI93" in dictUpdateList:
                    dictUpdateList['DVI93']['set'] = (int(dictUpdateList['DVI93']['set']) + 50)
                if "DVI94" in dictUpdateList:
                    dictUpdateList['DVI94']['set'] = (int(dictUpdateList['DVI94']['set']) + 50)
                if "DVI95" in dictUpdateList:
                    dictUpdateList['DVI95']['set'] = (int(dictUpdateList['DVI95']['set']) + 50)
                if "DVI96" in dictUpdateList:
                    dictUpdateList['DVI96']['set'] = (int(dictUpdateList['DVI96']['set']) + 50)
                keysUpdateList = list(dictUpdateList.keys())

                for ea in keysUpdateList:
                    out = dictSettingList.get(ea)
                    dictUpdateList[out] = dictUpdateList.pop(ea)

                for ea in dictUpdateList:
                    while True:
                        try:
                            a = modbuswrite(16, 6, int(ea), 1, int(dictUpdateList.get(ea)[u'set']))

                            if a[1] == int(dictUpdateList.get(ea)[u'set']):
                                output.append(dictUpdateList.get(ea)[u'id'])
                                break
                            else:
                                errorcounter = errorcounter + 1
                                if errorcounter >= 3:
                                    output.append("E" + str(dictUpdateList.get(ea)[u'id']))
                                    break

                        except Exception as e:
                            output.append("E" + str(dictUpdateList.get(ea)[u'id']))
                            break

                out = {'id': output}

                jsonres = json.dumps(out)
                if (out['id'][0] == "1000") or (out['id'][0] == "E1000"):
                    self.slavesendequeue.put(jsonres)
                    break
                else:
                    confirmationQueue.put(jsonres)
                    break

            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  setSettingData Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False

    def getPing(self):
        self.pause = True
        while True:
            try:
                output = {"Ping": 0}
                jsonres = json.dumps(output)
                self.sendqueue.put(jsonres)
                break
            except:
                if debug == 1:
                    dat = open(ErrorLog, 'a')
                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  Ping Error\n")
                    dat.write(error)
                    dat.close()
                break
        self.pause = False


"""
#This class is a thread who send all data to the server
"""


def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'a').close()


class PostingThread(threading.Thread):

    # This Thread is waiting for work and $_POST them to the server.

    def __init__(self, jobqueue, sendqueue, ModbusSlaveQueue):

        # Get the queue with the work.

        threading.Thread.__init__(self)
        self.jobqueue = jobqueue
        self.sendqueue = sendqueue
        self.ModbusSlaveQueue = ModbusSlaveQueue
        self.FABnrANDToken = getConfigFile()

    def run(self):
        global online
        global ServerConnection
        count = 0
        countAccess = 0

        session = openSession()

        self.timestamp = time.time() + float(3)

        self.buffer = {}
        send_now = False

        while True:

            if not self.FABnrANDToken:
                time.sleep(1)
                if FabNR != '000000':
                    jsonOut = {"pumpid": FabNR, "accesstoken": ""}

                    try:
                        se = post(session, WebserviceURL, jsonOut)
                        ServerConnection = True

                        JSONrequest = se.json()
                        if se.status_code == requests.codes.ok:
                            if ('accesstoken' in JSONrequest):
                                jsonOut['accesstoken'] = se.json()['accesstoken']
                                jsonOut = json.dumps(jsonOut)
                                subprocess.call(['mount -o remount,rw /'], shell=True)
                                f = open(ConfigFile, 'w')
                                f.write(jsonOut)
                                f.close()

                                f2 = open(FabnrFile, 'w')
                                f2.write(str(FabNR))
                                f2.close()
                                subprocess.call(['mount -o remount,ro /'], shell=True)
                                self.FABnrANDToken = json.loads(jsonOut)
                            else:
                                pass
                        touch(PostTimePath)
                    except:
                        ServerConnection = False

            while not confirmationQueue.empty():
                cq = confirmationQueue.get()
                self.buffer.update(dict(json.loads(cq)))
                send_now = True

            while not self.sendqueue.empty():
                postque = self.sendqueue.get()
                # print(postque)
                if ModbusServer != 0:
                    self.ModbusSlaveQueue.put(postque)
                self.buffer.update(dict(json.loads(postque)))

            if self.FABnrANDToken:
                time.sleep(1)
                if self.timestamp < time.time() or send_now == True:
                    send_now = False

                    # test weise deaktivieren
                    # obj.update(add)

                    self.buffer.update(self.FABnrANDToken)
                    # self.buffer = json.dumps(self.buffer)
                    # print(self.buffer)
                    try:
                        se = post(session, WebserviceURL, self.buffer)
                        ServerConnection = True
                        touch(PostTimePath)
                    except:
                        ServerConnection = False

                    if ServerConnection == True:
                        if se.status_code == requests.codes.ok:
                            try:
                                if se.json()['Access'] == "Denied":
                                    if countAccess == 10:
                                        try:
                                            # muss mir was neues ausdenken damit er ikke bare så sletter
                                            subprocess.call(['mount -o remount,rw /'], shell=True)
                                            os.remove(ConfigFile)
                                            os.remove(FabnrFile)
                                            subprocess.call(['mount -o remount,ro /'], shell=True)
                                            subprocess.call(['systemctl restart DVI-net'], shell=True)
                                        except:
                                            subprocess.call(['systemctl restart DVI-net'], shell=True)
                                    countAccess += 1
                                else:
                                    if (se.json()['update'] == 1):
                                        jo = se.json()['up']
                                        jo2 = json.dumps(jo)

                                        if 'PISWup' in jo2:
                                            jo = se.json()['up']['PISWup']
                                            a = jo['set']
                                            if a == "1":
                                                b = jo['id']
                                                output = {"id": [b]}
                                                obj = dict(output)
                                                obj.update(self.FABnrANDToken)
                                                se = post(session, WebserviceURL, obj)
                                                subprocess.call(['mount -o remount,rw /'], shell=True)
                                                subprocess.call(['./home/code/dvi-net3/update.sh'], shell=True)
                                                subprocess.call(['mount -o remount,ro /'], shell=True)
                                                subprocess.call(['systemctl restart DVI-net'], shell=True)

                                        self.jobqueue.put((1, "setSettingData", jo2))

                                    if (se.json()['online'] == 1):
                                        if count == 0:
                                            setTimer(2, self.jobqueue, LoginSpeedSettings)
                                            online = 1
                                            count = 1
                                    if (se.json()['online'] == 0):
                                        if count == 1:
                                            online = 0
                                            count = 0
                            except:
                                if debug == 1:
                                    dat = open(ErrorLog, 'a')
                                    error = str(time.strftime("%d.%m.%y %H:%M:%S") + " ->  Unable to parse\n")
                                    dat.write(error)
                                    dat.close()

                    self.timestamp = time.time() + float(59)
                    self.buffer = {}
