#!/usr/bin/python
# -*- encoding: utf8 -*-
##
#
# Class sensors manager

import threading
import logging, subprocess, re, time
import sqlite3
import traceback
from collections import defaultdict
LEVEL_LOGGING=logging.DEBUG
logging.basicConfig( level=LEVEL_LOGGING, format='[%(levelname)s] - %(threadName)-10s : %(message)s')

#Data constants
MAX_RETRYS=10
PERIOD=120
DATABASE="ic3KDB/ic3KDB.db"
DATABASE_CREATE="ic3KDB/ic3KDB.sql"
SAMPLE_SENSOR= "Using pin \#4\
                Data (40): 0x1 0xd8 0x0 0xe2 0xbb\
                Temp =  22.6 *C, Hum = 47.2 %"


def nesteddict():
  '''Multidimensional dictionaries'''
  return defaultdict(nesteddict)

class DHTManager:
  
  DHT_GPIO_PINS=(4,17)
  d =defaultdict(dict)
  lock = threading.Lock()
  
  def setTempHum(self, sensor, temp, hum):
    '''Set temperature, humidity in cache variables and db'''
    with self.lock:
      self.d[sensor]["temp"    ] = temp
      self.d[sensor]["hum"     ] = hum
      self.d[sensor]["datetime"] = datetime = time.strftime("%Y-%m-%d %H:%M:%S") # var datetime to be able to separate lock and db
    logging.debug("Values of sensor %s updated in cache with lock"%sensor)
    with DBConnection() as cursor:
      cursor.execute("INSERT INTO Temp (event_time, sensor, value) VALUES(?,?,?)", (datetime, sensor, temp))
      cursor.execute("INSERT INTO Hum (event_time, sensor, value) VALUES(?,?,?)", (datetime, sensor, hum))
    logging.debug("Values of sensor %s updated in DB without lock"%sensor)
  
  def getTemp(self, sensor=None): # Not ready for humidity
    ''' Return a list of tuples (sensor, date, temp)'''
    with self.lock:
      if sensor and sensor in self.d.keys(): #TODO-Futuro: Igualar el tipo de salida, dict o tupla segun convenga
        return [(sensor, self.d[sensor]["datetime"], self.d[sensor]["temp"])]
      else:
        return [(s, self.d[s]["datetime"], self.d[s]["temp"]) for s in self.d.keys()]
    
  def getLastTemps(self, minutes, sensor=None): # Not ready for humidity
    ''' Return a list of tuples (sensor, date, temp) with data within last minutes'''
    with DBConnection() as cursor:
      if sensor:
        cursor.execute("SELECT sensor, event_time, value FROM Temp WHERE sensor = %d AND event_time between\
                      datetime('now', 'localtime', '-%d minute') and datetime('now', 'localtime')"%(sensor, minutes))
      else:
        cursor.execute("SELECT sensor, event_time, value FROM Temp WHERE event_time between\
                      datetime('now', 'localtime', '-%d minute') and datetime('now', 'localtime')"%minutes)
      return sorted(cursor.fetchall(), key=lambda row: (-row[0], row[1]), reverse=True)
  
  def reader(self, terminate):
    '''Thread-friendly. Read the sensors, posibly blocking until right reading'''
    
    logging.info("Starting %s"%threading.currentThread().getName())
    while not terminate.is_set():
      for sensor in self.DHT_GPIO_PINS:
        logging.debug("Reading DHT sensor %s"%sensor)
        retry = MAX_RETRYS
        
        # Read temperature
        matches = None
        while not matches and retry:
          ##DEL:output = subprocess.check_output(["./Adafruit_DHT", "22", str(sensor)])
          output  = SAMPLE_SENSOR
          matches = re.search("Temp =\s+([0-9.]+)", output)
          if matches:
            temp = float(matches.group(1))
            matches = re.search("Hum =\s+([0-9.]+)", output)
            hum  = float(matches.group(1))
            
            self.setTempHum(sensor, temp, hum)
            logging.debug("Saved on db and cache - (%s>time: %s, temp: %s) "%self.getTemp(sensor)[0])
            logging.debug("Temperature: %.1f C" % temp)
            logging.debug("Humidity:    %.1f %%" % hum)
          else:
            time.sleep(2)
            retry -=1
      terminate.wait(PERIOD)
    logging.debug("Finishing")
  

class DBConnection:
  ''' Provide transactional connexion and clean use'''
  connection = None
  def __enter__(self):
    self.connection = sqlite3.connect(DATABASE)
    #self.connection.row_factory = sqlite3.Row
    cursor = self.connection.cursor()
    logging.debug("Conexion opened")
    return cursor
  
  def __exit__(self, type=None, value=None, tracebac=None):
    if type:
      logging.warning("Exception accessing Database")
      print traceback.format_exc()
      self.connection.rollback()
    else:
      self.connection.commit()
    self.connection.close()
    logging.debug("Conexion closed")
    return True


####Testing purpose
if __name__ == '__main__':
  DATABASE="../ic3KDB/ic3KDB.db"
  DATABASE_CREATE="../ic3KDB/ic3KDB.sql"
  if LEVEL_LOGGING==logging.DEBUG:
  # Initialize database
    with open(DATABASE_CREATE,'r') as f:
      with DBConnection() as cursor:
        cursor.executescript(f.read())
  
  dhtm = DHTManager()
  print dhtm.getLastTemps(600)

  
  
  
  
  
  
  
  
