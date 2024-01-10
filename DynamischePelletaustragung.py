#-*- coding:utf-8 -*-

#Version 0.1.7

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
    if ImmerLoggen:
        global pfadFuerLogs
        log = open(pfadFuerLogs + "Log_" + Datum + ".txt", "a+")
        log.write(message)
        log.close()

def write_times(message):
    if AenderungenLoggen:
        global pfadFuerLogs
        times = open(pfadFuerLogs + "Zeitpunkte.txt", "a+")
        times.write(Datum + " - " + Uhrzeit + "\n" + message + "\n")
        times.close()

reload(sys)
sys.setdefaultencoding('utf-8')

Datum = time.strftime("%Y-%m-%d", time.localtime())
Uhrzeit = time.strftime("%H:%M:%S", time.localtime())

# Hier den Pfad zum Script eintragen (wird auch für temporäre Daten genutzt)
pfadZumScript = "/home/pi/script/"
# Hier gewünschten Pfad für die logs eintragen
pfadFuerLogs = "/home/pi/script/logs/"
    
# Hier die eigenen MQTT-Daten eintragen
broker_address= "127.0.0.1"
port = 1883
username = ""
password = ""

# Adressen bitte mit 'sudo p4 menu | grep "Start der"' herausfinden.
# Den Hexwert der ganz vor bei Address angezeigt wird in Dezimal umrechen und hier eintragen
AdresseZeit1 = 60
AdresseZeit2 = 516

# Gewünschte Standard-Zeiten hier eintragen. Format : (Stunde, Minute, Sekunde)
# Wird hier jeweils 0:00 Uhr eingetragen wird nur geladen wenn der Wert "MinPelletstandZumFuellen" unterschritten wird
ResetT1 = datetime.time(0, 0, 0)
ResetT2 = datetime.time(0, 0, 0)

# Unter diesem %-Wert wird im Zustand "Betriebsbereit" gefüllt
MinPelletstandZumFuellen = 30
# Nach dieser Anzahl an Tagen wird der Pelletbehälter auf 0 % gefahren.
TageFuer0Prozent = 30

# Hier einstellen ob bei jedem Aufruf geloggt werden soll
ImmerLoggen = True
# Hier Einstelen ob Änderungen an den Ladezeiten geloggt werden sollen
AenderungenLoggen = False

# In diesen Betriebszuständen wird die Pelletbefüllung verzögert
KeineFuellungStatusList = ["Vorbereitung", "Vorwärmen", "Zünden", "Heizen"]

# Topics sollten so passen
TopicStatus = "p4d2mqtt/sensor/Status/state"
TopicPelletstand = "p4d2mqtt/sensor/FuellstandimPelletsbehaelter_0x71/state"
TopicCommand = "p4d2mqtt/s3200/request"
CommandText = "parset"
#p4d Version < 0.9.54
#TopicCommand = "p4d2mqtt/command" - 
#CommandText = "parstore"

if not os.path.exists(pfadFuerLogs):
    os.mkdir(pfadFuerLogs)
    
Connected = False
Status = "Keiner"
Pelletstand = int(-1)
write_log(Uhrzeit + "\n")

now = time.localtime()
minutesnow = int(time.strftime("%H", now))*60 + int(time.strftime("%M",now))
zerotime = datetime.datetime(2021, 1, 1,0,0,0)
t1Minutes = int(datetime.time.strftime(ResetT1, "%H"))*60 + int(datetime.time.strftime(ResetT1, "%M"))
t2Minutes = int(datetime.time.strftime(ResetT2, "%H"))*60 + int(datetime.time.strftime(ResetT2, "%M"))

ersteBefuellung = int(os.popen('p4 getp -a ' + str(AdresseZeit1) + ' | grep Value | cut -d " " -f3').read())
zweiteBefuellung = int(os.popen('p4 getp -a ' + str(AdresseZeit2) + ' | grep Value | cut -d " " -f3').read())

client = mqttClient.Client("DynamicScript")
client.on_connect = on_connect
client.on_message = on_message
if username != "":
    client.username_pw_set(username, password)
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

FMT = '%Y-%m-%d %H:%M:%S'
nowStr = str(datetime.datetime.now())
nowStr = nowStr[0:19]
nowDT = datetime.datetime.strptime(nowStr, FMT)
if not os.path.exists(pfadZumScript + "LastZero.txt"):
    lastZeroFile = open(pfadZumScript + "LastZero.txt", 'wt')
    lastZeroFile.write(str(nowDT))
    lastZeroFile.close()
if Pelletstand < 1:
    write_times("Pelletbehälter auf 0% gefallen. Setze LastZero.txt auf " + str(nowDT) + "\n")
    if (os.path.exists(pfadZumScript + "ToZero.txt")):
        write_times("Lösche ToZero.txt\n")
        os.remove(pfadZumScript + "ToZero.txt")
    lastZeroFile = open(pfadZumScript + "LastZero.txt", 'wt');
    lastZeroFile.write(str(nowDT))
    lastZeroFile.close()
lastZeroFile2 = open(pfadZumScript + "LastZero.txt", 'rt');
lastZeroDT = lastZeroFile2.readline().strip();
lastZeroFile2.close()
tDelta = nowDT - datetime.datetime.strptime(lastZeroDT, FMT)
if tDelta.days > TageFuer0Prozent and TageFuer0Prozent != 0:
    write_log("Seit über " + str(TageFuer0Prozent) + " Tagen Behälter nicht leer gefahren.\n")
    write_log("Script wird abgebrochen um Behälter komplett zu leeren\n\n")
    if not os.path.exists(pfadZumScript + "ToZero.txt"):
        write_times("Lasse Pelletbehälter auf 0% fallen\n")
        open(pfadZumScript + "ToZero.txt", 'aw').close()
        write_log("Schreibe ToZero.txt-Datei\n")
    exit()
    
if not os.path.exists(pfadZumScript + "ResetTmp.txt"):
    open(pfadZumScript + "ResetTmp.txt", 'aw').close()
resetFile = open(pfadZumScript + "ResetTmp.txt", 'rt');
lastResetDay = resetFile.readline();
resetFile.close()
today = time.strftime("%d", time.localtime())
if lastResetDay != today:
    write_log("Schreibe Standard-Zeiten\n")
    write_log("Zeit 1: " + datetime.time.strftime(ResetT1, "%H:%M") + " Uhr\n")
    write_log("Zeit 2: " + datetime.time.strftime(ResetT2, "%H:%M") + " Uhr\n")

    message_set1 = {"command": CommandText, "address": AdresseZeit1, "value" : str(t1Minutes)}
    message_set2 = {"command": CommandText, "address": AdresseZeit2, "value" : str(t2Minutes)}

    message = json.dumps(message_set1)
    client.publish(TopicCommand, message)
    time.sleep(1)
    message = json.dumps(message_set2)
    client.publish(TopicCommand, message)
    resetFile = open(pfadZumScript + "ResetTmp.txt", 'wt');
    resetFile.write(today)
    resetFile.close()    

if Status == "Betriebsbereit" and Pelletstand < MinPelletstandZumFuellen:
    WasGeandert = True
    
    if (os.path.exists(pfadZumScript + "laden.txt")):
        value = int((minutesnow + 5)) % 1440
        address = 0
        if value <= 720:
            address = AdresseZeit1
            logtext = "1."
        
        if value > 720:
            address = AdresseZeit2
            logtext = "2."
        
        message_set = {"command": CommandText, "address": address, "value" : str(value)}
        
        
        message = json.dumps(message_set)
        client.publish(TopicCommand, message)

        settime = (zerotime + datetime.timedelta(minutes = value)).time()
        logtext = logtext + " Zeit auf " + datetime.time.strftime(settime, "%H:%M") + " Uhr (" + str(value) + ") gesetzt, da Pelletstand " + str(Pelletstand) + "% und Status " + str(Status) + "\n"
        write_times(logtext)
        write_log(logtext)
        os.remove(pfadZumScript + "laden.txt")

    else:
        open(pfadZumScript + "laden.txt", 'aw').close()
        write_log("Schreibe laden.txt-Datei\n")

abstandZuErsterBefuellung = ersteBefuellung-minutesnow
abstandZuZweiterBefuellung = zweiteBefuellung-minutesnow

if any(Status in s for s in KeineFuellungStatusList) and Pelletstand > 1 and Pelletstand < 80 and abstandZuErsterBefuellung > 0 and abstandZuErsterBefuellung < 15:
    WasGeandert = True
    value = minutesnow + 30
    
    message_set = {"command": CommandText, "address": AdresseZeit1, "value" : str(value)}
    
    message = json.dumps(message_set)
    client.publish(TopicCommand, message)
    settime = (zerotime + datetime.timedelta(minutes = value)).time()
    logtext = "1. Zeit auf " + datetime.time.strftime(settime, "%H:%M") + " Uhr (" + str(value) + ") gesetzt, da Heizung heizt, Zeit zu 1. Befuellung " + str(abstandZuErsterBefuellung) + "min, Pelletstand " + str(Pelletstand) + "% (Status: " + str(Status) + ")\n"
    write_times(Uhrzeit + ":\n" + logtext + "\n")
    write_log(logtext)

if any(Status in s for s in KeineFuellungStatusList) and Pelletstand > 1 and Pelletstand < 80 and abstandZuZweiterBefuellung > 0 and abstandZuZweiterBefuellung < 15:   
    WasGeandert = True
    value = minutesnow + 30
    
    message_set = {"command": CommandText, "address": AdresseZeit2, "value" : str(value)}
    
    message = json.dumps(message_set)
    client.publish(TopicCommand, message)
    settime = (zerotime + datetime.timedelta(minutes = value)).time()
    logtext = "2. Zeit auf " + datetime.time.strftime(settime, "%H:%M") + " Uhr (" + str(value) + ") gesetzt, da Heizung heizt, Zeit zu 2. Befuellung " + str(abstandZuZweiterBefuellung) + "min, Pelletstand " + str(Pelletstand) + "% (Status: " + str(Status) + ")\n"
    write_times(Uhrzeit + ":\n" + logtext + "\n")
    write_log(logtext)

client.disconnect()
client.loop_stop()
if WasGeandert == False:
    if (os.path.exists(pfadZumScript + "laden.txt")):
        write_log("Lösche laden-Datei\n")
        os.remove(pfadZumScript + "laden.txt")
    write_log("Keine Änderungen vorgenommen\n")
write_log("\n")
