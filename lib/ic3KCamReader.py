#!/usr/bin/python
# -*- encoding: utf8 -*-
##
#
# Class cameras manager

import threading
import logging, subprocess, re, time, os
import time
import datetime as DT
import traceback
from collections import defaultdict
from urllib2     import urlopen, URLError, HTTPError

LEVEL_LOGGING=logging.DEBUG
logging.basicConfig( level=LEVEL_LOGGING, format='[%(levelname)s] - %(threadName)-10s : %(message)s')

#Data constants
MAX_RETRYS      = 10
PERIOD          = 120
PHOTO_PATH      = "static/img/"
PHOTO_PREFIX    = "cam"
PHOTO_SUFIX     = ".jpeg"
SAMPLE_CAM      = "http://aquidice.com/wp-content/uploads/2013/01/las-web-cam-hackeadas.jpg"


class CamManager:
  
  CAMERAS={1:["http://aquidice.com/wp-content/uploads/2013/01/las-web-cam-hackeadas.jpg"],
           2:["http://aquidice.com/wp-content/uploads/2013/01/las-web-cam-hackeadas.jpg"]}
  lock = threading.Lock()
  lastCamPath = {}
  
  def getCameras(self):
    return self.CAMERAS
    
  def getImage(self, image):
    with self.lock:
      with open(PHOTO_PATH + image, "rb") as img:
        return img.read()
  
  def getImagesPath(self, minutes=None, id=None):
    ''' Return a dict with camera id and list of images within last minutes or last one if minutes not given'''
    if id:
      ids = [id]
    else:
      ids = self.CAMERAS.keys()
    with self.lock:
      if minutes: # In this case, read files and filter by date
        dateBeginning = time.time() - DT.timedelta(minutes=minutes).total_seconds()
        #datetime = time.strftime("%Y%m%d%H%M%S")DT.datetime.strptime(time.strftime("%Y%m%d%H%M%S"), "%Y%m%d%H%M%S") - m
        dict = {}
        for i in ids:
          dict[i] = []
          filenames = os.listdir(PHOTO_PATH)
          for fn in filenames:
            if self.checkImagePath(fn, dateBeginning, i):
              dict[i].append(fn)
        return dict
        #return {i:[fn] for i in ids for fn in filenames if self.checkImagePath(fn, dateBeginning, i)}
    return {i:[self.lastCamPath[i]] for i in ids} # TODO: Preparar para historico
  
  def checkImagePath(self, filename, dateBeginning, id): # WIP: Ninguno en la lista, mirar si es porque el filtro esta mal
    pattern = '%s%i_(\\d*)_(\\d*)%s'%(PHOTO_PREFIX, id, PHOTO_SUFIX)
    date = re.sub(pattern, r'\1\2', filename)
    if date[0].isdigit():
      return time.strptime(date, "%Y%m%d%H%M%S") >= dateBeginning
    return False
    
  def reader(self, terminate):
    '''Thread-friendly. Read cameras '''
    
    logging.info("Starting %s"%threading.currentThread().getName())
    while not terminate.is_set():
      datetime = time.strftime("%Y%m%d_%H%M%S")
      for camera in self.CAMERAS.keys():
        logging.debug("Reading camera %s"%camera)
        
        # Filename composition
        filename = PHOTO_PREFIX + str(camera) + "_" + datetime + PHOTO_SUFIX
        # Get and store image
        image = urlopen(SAMPLE_CAM)
        with open(PHOTO_PATH + filename, 'wb') as f:
          f.write(image.read())
        logging.debug("Saved image to file  - (%s -> file:%s) "%(camera, PHOTO_PATH + filename))
        # Update last image path
        with self.lock:
          self.lastCamPath[camera] = filename
        logging.debug("Saved image to cache - (%s) "%camera)
        print image.info()
      terminate.wait(PERIOD)
      #terminate.set() #DEL
    logging.debug("Finishing")
  

####Testing purpose
if __name__ == '__main__':
  PHOTO_PATH = "../" + PHOTO_PATH
  camMan = CamManager()
  print camMan.reader(threading.Event())


