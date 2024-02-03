import RPi.GPIO as GPIO
import gpiozero
from time import sleep
import datetime
from tkinter import *
import tkinter
from tkinter import font
from tkinter import filedialog
import firebase_admin
from firebase_admin import credentials, db
import threading
import serial
port='/dev/ttyUSB0'
arduino = serial.Serial(port, 9600)
serialNumber = "100000009c590c10"

def get_raspberry_pi_serial():
    try:
        with open('/proc/cpuinfo', 'r') as file:
            for line in file:
                if line.startswith('Serial'):
                    serial_number = line.split(':')[-1].strip()
                    return serial_number
    except Exception as e:
        print(e)
        return None

cred = credentials.Certificate("personnelstatusplate-firebase-adminsdk-ggqlo-35d50549fa.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': databaseURL
})
refUsers = db.reference('/users/')
refCardKey = db.reference('/cardKey/')
refPanel = db.reference('/panel/')
refRFID = db.reference('/readRFID')

serial_number = get_raspberry_pi_serial()
check = refRFID.get()
print(check)
def handle_event(event):
    global check
    check = refRFID.get()

event_stream = refRFID.listen(handle_event)

while True:
    if(check == "1"):
        a=arduino.readline()
        a = a.decode()
        a = a[:12]
        print("A", a, "B", sep='')

        users = refUsers.get()
        cardKey = refCardKey.get()
        panel = refPanel.get()

        if users == None:
            users = dict()
        if cardKey == None:
            cardKey = dict()
        if panel == None:
            panel = dict()

        if (serialNumber in panel) and (a in cardKey):
            pos = panel[serialNumber]
            card = cardKey[a]
            if card in users:
                user = users[card]

                leftPos = users[card]['pos']
                users[card]['pos'] = pos
                refUsers.set(users)

                print("변경전 :", leftPos, "변경후 :", pos, "변경 완료", sep=' ')
            else:
                print("Error")
        else:
            print("Error")

        a = " "
