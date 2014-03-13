#!/usr/bin/python
# -*- encoding: utf8 -*-
##
#
# IC3 Server


from flask import Flask, render_template,request,abort,redirect,url_for
import threading
import signal
import logging
import sys
import lib.ic3KDHTReader as SEN
import lib.ic3KCamReader as CAM


# Config constants
app = Flask(__name__)
DEBUG=True

# Data constants
dhtManager = SEN.DHTManager()
camManager = CAM.CamManager()
IMAGES = ["http://plazadelapelicula.com/imgs/files/DAVID%20EL%20GNOMO.jpg", "http://aquidice.com/wp-content/uploads/2013/01/las-web-cam-hackeadas.jpg"]
HISTORIC_MIN = 1440 # A day


## Entry routes
@app.route('/')
def index():
  i = IMAGES[:1]
  return render_template('index.html', idsImages = camManager.getImagesPath(), dataSen=dhtManager.getTemp())


@app.route('/historic/')
@app.route('/historic/<int:minutes>')
def historic(minutes=None):
  if minutes:
    min = minutes
  else:
    min = HISTORIC_MIN
  return render_template('historic.html', idsImages = camManager.getImagesPath(minutes=HISTORIC_MIN), dataSen=dhtManager.getLastTemps(min))
  

@app.route('/sensors/')
@app.route('/sensors/<int:sensor>')
def getSensorsData(sensor=None):
  if sensor:
    ret = str(dhtManager.getTemp(sensor)[0])
  else:
    ret = str(dhtManager.getTemp())
  return ret


@app.route("/img/<path:image>")
def images(image):
  ''' Return a image from path'''
  ret = app.make_response(camManager.getImage(image))
  ret.content_type = "image/jpeg"
  return ret


def main():
  terminate = threading.Event()
  
  sensors = threading.Thread(target=dhtManager.reader, name="sensors", args=(terminate,))
  cameras = threading.Thread(target=camManager.reader, name="cameras", args=(terminate,))
  sensors.start()
  cameras.start()
  app.run(host="0.0.0.0", debug=False)#DEBUG)
  
  terminate.set()
  logging.debug("Exiting")
  sensors.join()
  cameras.join()
  logging.info("Exit")

if __name__ == '__main__':
  main()

