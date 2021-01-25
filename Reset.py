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

def write_log(message):  
    log = open("/home/pi/logs/LogReset.txt", "a+")
    log.write(message)
    log.close()	
    
    
# Hier die eigenen Daten eintragen
broker_address= "127.0.0.1"
port = 1883

# Adressen bitte mit 'sudo p4 menu | grep "Start der"' herausfinden.
# Den Hexwert der ganz vor bei Address angezigt wird in Dezimal umrechen und hier eintragen
AdresseZeit1 = 60
AdresseZeit2 = 516

# Gewünschte Standard-Zeiten hier eintragen. Format : (Stunde, Minute, Sekunde)
t1 = datetime.time(6, 0, 0)
t2 = datetime.time(17, 0, 0)

# Topic sollte passen
TopicCommand = "mqtt2p4d/command"

t1Minutes = int(datetime.time.strftime(t1, "%H"))*60 + int(datetime.time.strftime(t1, "%M"))
t2Minutes = int(datetime.time.strftime(t2, "%H"))*60 + int(datetime.time.strftime(t2, "%M"))

write_log(time.strftime("%d.%m.%Y, %H:%M:%S", time.localtime()) + "\n")
Connected = False
client = mqttClient.Client("MeinResetScript")
client.on_connect = on_connect
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

write_log("Verbindung zum Broker hergestellt! Schreibe Standard-Zeiten\n")
write_log("Zeit 1: " + datetime.time.strftime(t1, "%H:%M") + " Uhr\n")
write_log("Zeit 2: " + datetime.time.strftime(t2, "%H:%M") + " Uhr\n")

message_set1 = {"command": "parstore", "address": AdresseZeit1, "value" : str(t1Minutes)}
message_set2 = {"command": "parstore", "address": AdresseZeit2, "value" : str(t2Minutes)}

message = json.dumps(message_set1)
client.publish(TopicCommand, message)
time.sleep(1)
message = json.dumps(message_set2)
client.publish(TopicCommand, message)

client.disconnect()
client.loop_stop()
write_log("Beende\n\n")