# p4d_Addon_Scripts
Scripts zur Verbesserung der Pelletaustragung bei Fröling-Kesseln

## Einsatzzweck
Da die standardmäßige Steuerung der Fröling-Pelletkessel bei der Pelletaustragung (Füllung des Pelletbehälters im Kessel) an sehr wenige Parameter gebunden ist ergeben sich einige unschöne Nebeneffekte.
Diese sind:
  * Die Füllung des Behälters erfolgt ungeachtet des aktuellen Kesselzustandes. Wird also gerade geheizt, wird der Kessel heruntergefahren und der Behälter gefüllt. Diese Füllung geschieht nach 2 Kriterien:
    1. Der Füllstand im Behälter erreicht einen eingestellten Wert (im Standardfall 0%, also leer)
    2. Die aktuelle Uhrzeit entspricht einer der beiden einstellbaren Uhrzeiten zum "Start der x. Pelletsbefüllung"
  * Vor dem Start einer Heizphase wird der aktuelle Füllstand des Behälters ignoriert. Das heißt, auch bei einem Füllstand von 2% wird angefangen zu heizen, jedoch dann nur für sehr kurze Zeit.

Dadurch ergibt sich, dass es unnötige Aufheizphasen gibt, die zum einen unnötig Strom und Pellets verbrauchen und zum anderen die Temperatur im Puffer zum Teil sehr weit fallen lässt.
Dies ist vor allem dann der Fall, wenn die Wärmeanforderung sehr hoch, der Behälter aber nur noch wenig gefüllt ist.

## Lösungsansatz

Unter Verwendung des Tools [p4d](https://github.com/horchi/linux-p4d#linux---p4-daemon-p4d) von "horchi" sollen diese Scripts dafür sorgen, dass dieses Verhalten verbessert wird.
Hierfür werden unter Auswertung des aktuellen Betriebszustandes und der Füllmenge des Behälters dynamisch die Startzeiten der Befüllungen angepasst, sodass bei geringen Füllständen rechtzeitig gefüllt wird
und im anderen Fall, wenn die Heizung noch heizt, die Füllung hinausgezögert wird, solange noch genügend Pellets vorhanden sind.

Eingebaut ist auch ein Reset, sodass die Befüllungszeiten auf die Standard-Zeiten zurückgesetzt werden, wenn man das möchte.

Neu in Version 0.1.2: Das Script lässt den Pelletbehälter alle x Tage (voreingestellt sind 10) auf 0% fallen um einer übermäßigen Staubansammlung im Behälter entgegen zu wirken.

### "Installation"
#### Voraussetzungen
* Für die Verwendung des Scripts muss ein MQTT-Broker laufen, der sowohl im Script als auch im p4d angegeben ist. Am Einfachsten ist hier die Verwendung eines lokalen MQTT-Brokers, wie 
[hier](https://www.holzheizer-forum.de/index.php?thread/50090-fr%C3%B6ling-announce-p4d-visualisierung-und-einstellung-der-s-3200-via-com1/&postID=182495#post182495)
ebenfalls von horchi beschrieben. Auf diese Verwendung ist das Script auch ausgelegt, natürlich kann aber die URL des Brokers angepasst werden.

* Zudem muss für die Verwendung von MQTT in python paho-mqtt installiert sein.
```sh
$ sudo pip install paho-mqtt
```

#### Einrichtung des Scripts
##### Adressen auslesen
Zur korrekten Ausführung des Scripts müssen anschließend noch die Adressen des Pelletbefüllzeiten herausgefunden werden.
Dies kann durch den Befehl
```sh
$ sudo p4 menu | grep "Start der"
```
Anschließend sollte eine solche Ausgabe kommen:
```sh
181) Address: 0x003c, parent: 0x0387, child: 0x0000; 'Start der 1. Pelletsbefüllung'
182) Address: 0x0204, parent: 0x0387, child: 0x0000; 'Start der 2. Pelletsbefüllung'
```
Hier interessieren uns die Adressen: Address: **0x003c** und **Address: 0x0204**. Diese müssen in Dezimal umgerechnet werden und im Script entsprechend bei *AdresseZeit1* und *AdresseZeit2* am Anfang des Scripts eingetragen werden.

##### Parameter
* Mit dem Parameter *MinPelletstandZumFuellen* kann festgelegt werden, unter welchem Füllstand des Behälters im Modus "Betriebsbereit" gefüllt wird.
* Der Parameter *TageFuer0Prozent* legt fest, nach welcher Anzahl an Tagen der Behälter auf 0% Füllung fallen gelassen wird.
* Die Parameter *ResetT1* und *ResetT2* legen fest, auf welche Zeiten die Befüllung standardmäßig eingestellt werden soll. Bei jeder ersten Ausführung des Scripts pro Tag werden diese Zeiten geschrieben. 
* *ImmerLoggen* und *AenderungenLoggen*: Hier kann festgelegt werden wie viel geloggt werden soll.

#### (Zyklische) Ausführung

Es wird davon ausgegangen dass das Script im Order "home/pi/script" liegt.
Zuvor muss noch sichergestellt werden dass die Scrips ausführbar sind:
```sh
$ cd /home/pi/script
$ sudo chmod +x DynamischePelletaustragung.py
```
Nun kann erstmals das Script ausgeführt werden:
```sh
$ python /home/pi/script/DynamischePelletaustragung.py
```
Sollte keine Ausgabe (also auch kein Fehler) kommen ist die Ausführung geglückt.

Zur zyklischen Ausführung des Scripts habe ich einen CRON-Task verwendet. Die Einrichtung ist denkbar einfach:
```sh
$ crontab -e
```
Am Ende der Datei folgenden Eintrag machen:
```
*/5 * * * * python /home/pi/script/DynamischePelletaustragung.py
```
Dadurch wird das Script alle 5 Minuten, 7 Tage die Woche ausgeführt.
