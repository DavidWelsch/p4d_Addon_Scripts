#-*- coding:utf-8 -*-

import datetime

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

Test = "Hallo Welt"