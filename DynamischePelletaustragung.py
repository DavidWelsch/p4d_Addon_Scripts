#-*- coding:utf-8 -*-

import os
import time
import datetime
import paho.mqtt.client as mqttClient
import sys
import json

def on_connect(client, userdata, flags, rc):
 
    if rc == 0:
        global Connected                #Use global variable
        Connected = True                #Signal connection 
 

def on_message(client, userdata, message):
    if "Status" in message.topic:
        global Status
        Status = json.loads(message.payload)["value"]
        
    if "Fuellstand" in message.topic:
        global Pelletstand
        Pelletstand = int(round(json.loads(message.payload)["value"],0))
	
def write_log(message):  
    log = open("/home/pi/logs/Log_" + Datum + ".txt", "a+")
    log.write(message)
    log.close()

def write_times(message):
    times = open("/home/pi/logs/Zeitpunkte_" + Datum + ".txt", "a+")
    log.write(message)
    log.close()

reload(sys)
sys.setdefaultencoding('utf-8')

Datum = time.strftime("%Y-%m-%d", time.localtime())
Uhrzeit = time.strftime("%H:%M:%S", time.localtime())

# Hier die eigenen Daten eintragen
broker_address= "127.0.0.1"
port = 1883

# Topics sollten so passen
TopicStatus = "p4d2mqtt/sensor/Status/state"
TopicPelletstand = "p4d2mqtt/sensor/FuellstandimPelletsbehaelter_0x71/state"
TopicCommand = "mqtt2p4d/command"

# Adressen bitte mit 'sudo p4 menu | grep "Start der"' herausfinden.
# Den Hexwert der ganz vor bei Address angezigt wird in Dezimal umrechen und hier eintragen
AdresseZeit1 = 60
AdresseZeit2 = 516

# Unter diesem %-Wert wird im Zustand "Betriebsbereit" gefüllt
MinPelletstandZumFuellen = 35

# In diesen Betriebszuständen wird die Pelletbefüllung verzögert
KeineFuellungStatusList = ["Vorbereitung", "Vorwärmen", "Zünden", "Heizen"]

Connected = False
Status = "Keiner"
Pelletstand = int(-1)
write_log(Uhrzeit + "\n")

now = time.localtime()
minutesnow = int(time.strftime("%H", now))*60 + int(time.strftime("%M",now))
zerotime = datetime.datetime(2021, 1, 1,0,0,0)

ersteBefuellung = int(os.popen('sudo p4 getp -a 0x003c | grep Value | cut -d " " -f3').read())
zweiteBefuellung = int(os.popen('sudo p4 getp -a 0x0204 | grep Value | cut -d " " -f3').read())

client = mqttClient.Client("DynamicScript")
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker_address, port=port)
client.loop_start()
countConnectionTries = 0
while Connected != True:    #Wait for connection
    time.sleep(0.1)
    countConnectionTries = countConnectionTries+1
    if countConnectionTries > 200:
        client.disconnect()
        client.loop_stop()
        write_log("Verbindung zum Broker fehlgeschlagen! Verlasse Script\n\n")
        sys.exit()

client.subscribe(TopicStatus)
client.subscribe(TopicPelletstand)

countWaitingTime = 0
while Status == "Keiner" or Pelletstand == -1:
    time.sleep(1)
    countWaitingTime = countWaitingTime+1
    if countWaitingTime > 10:
        break

write_log("Status: " + str(Status) + ", Pelletstand: " + str(Pelletstand) + "%\n") 

WasGeandert = False

if Status == "Betriebsbereit" and Pelletstand < MinPelletstandZumFuellen:
    WasGeandert = True
    value = int((minutesnow + 5)) % 1440
    address = AdresseZeit1
    
    if value <= 720:
        address = AdresseZeit1
    
    if value > 720:
        address = AdresseZeit2
    
    message_set = {"command": "parstore", "address": address, "value" : str(value)}
    message = json.dumps(message_set)
    client.publish(TopicCommand, message)
    
    if address == AdresseZeit1:
        logtext = "1."
    else:
        logtext = "2."
    
    settime = (zerotime + datetime.timedelta(minutes = value)).time()
    logtext = logtext + " Zeit auf " + datetime.time.strftime(settime, "%H:%M") + " Uhr (" + str(value) + ") gesetzt, da Pelletstand " + str(Pelletstand) + " und Status " + str(Status) + "\n"
    write_times(Uhrzeit + ":\n" + logtext + "\n")
    write_log(logtext)

abstandZuErsterBefuellung = ersteBefuellung-minutesnow
abstandZuZweiterBefuellung = zweiteBefuellung-minutesnow


if any(Status in s for s in KeineFuellungStatusList) and Pelletstand > 1 and abstandZuErsterBefuellung > 0 and abstandZuErsterBefuellung < 15:
    WasGeandert = True
    value = minutesnow + 30
    message_set = {"command": "parstore", "address": AdresseZeit1, "value" : str(value)}
    message = json.dumps(message_set)
    client.publish(TopicCommand, message)
    settime = (zerotime + datetime.timedelta(minutes = value)).time()
    logtext = "1. Zeit auf " + datetime.time.strftime(settime, "%H:%M") + " Uhr (" + str(value) + ") gesetzt, da Heizung heizt, Zeit zu 1. Befuellung " + str(abstandZuErsterBefuellung) + "min, Pelletstand " + str(Pelletstand) + "% (Status: " + str(Status) + ")\n"
    write_times(Uhrzeit + ":\n" + logtext + "\n")
    write_log(logtext)

if any(Status in s for s in KeineFuellungStatusList) and Pelletstand > 1 and abstandZuZweiterBefuellung > 0 and abstandZuZweiterBefuellung < 15:   
    WasGeandert = True
    value = minutesnow + 30
    message_set = {"command": "parstore", "address": AdresseZeit2, "value" : str(value)}
    message = json.dumps(message_set)
    client.publish(TopicCommand, message)
    settime = (zerotime + datetime.timedelta(minutes = value)).time()
    logtext = "2. Zeit auf " + datetime.time.strftime(settime, "%H:%M") + " Uhr (" + str(value) + ") gesetzt, da Heizung heizt, Zeit zu 2. Befuellung " + str(abstandZuZweiterBefuellung) + "min, Pelletstand " + str(Pelletstand) + "% (Status: " + str(Status) + ")\n"
    write_times(Uhrzeit + ":\n" + logtext + "\n")
    write_log(logtext)
   
client.disconnect()
client.loop_stop()
if WasGeandert == False:
    write_log("Keine Änderungen vorgenommen\n")
write_log("\n")