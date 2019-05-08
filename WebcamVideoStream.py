from __future__ import print_function
from threading import Thread
import threading
import numpy as np
import cv2
import sys
import datetime
import time
import People
import math

personSize = 400
persons = []
pid = 1
entered = 0
exited = 0

def draw_detections(img, rects, thickness = 2):
    for x, y, w, h in rects:  
        if w > 400 and h > 400:  	
            pad_w, pad_h = int(0.15*w), int(0.05*h)
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), thickness)

class WebcamVideoStream(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        codec = 1196444237.0 # MJPG
        #print 'fourcc:', decode_fourcc(codec)
        self.video.set(cv2.CAP_PROP_FOURCC, codec)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.video.set(cv2.CAP_PROP_FPS, 30)
        self.w = self.video.get(3) #CV_CAP_PROP_FRAME_WIDTH
        self.h = self.video.get(4) #CV_CAP_PROP_FRAME_HEIGHT
        self.rangeLeft = int(1*(self.w/6))
        self.rangeRight = int(5*(self.w/6))
        self.midLine = int(2.5*(self.w/6))

        _, self.rawImage = self.video.read()
        self.firstFrame = cv2.cvtColor(self.rawImage, cv2.COLOR_BGR2GRAY)
        ret, jpeg = cv2.imencode('.jpg', self.rawImage)
        self.frameDetections = jpeg.tobytes()

        self.contours= []

        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def __del__(self):
        self.video.release()

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        t2 = Thread(target=self.updateContours, args=())
        t2.daemon = True
        t2.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        count = 1 
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            # otherwise, read the next frame from the stream
            (self.grabbed, self.rawImage) = self.video.read()
            img = self.rawImage.copy()
            #draw rectangles around the people
            draw_detections(img,self.contours)
            #visually show the counters
            cv2.putText(img, "Entered: " + str(entered) ,(10,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),2,cv2.LINE_AA)
            cv2.putText(img, "Exited: " + str(exited) ,(10,50),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),2,cv2.LINE_AA)
            ret, jpeg = cv2.imencode('.jpg', img)
            self.frameDetections = jpeg.tobytes()

    def updateContours(self):
        # keep looping infinitely until the thread is stopped
        global personSize
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            #get the current frame and look for people
            total = datetime.datetime.now()
            img = cv2.cvtColor(self.rawImage, cv2.COLOR_BGR2GRAY)
            total = datetime.datetime.now()
            frameDelta = cv2.absdiff(self.firstFrame, img)
            ret, thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)
            (allContours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            personContours = []
            for c in allContours:
                # only look at contours larger than a certain size
                #if cv2.contourArea(c) > 1:
                    #print(cv2.contourArea(c))
                if cv2.contourArea(c) > personSize:
                    personContours.append(cv2.boundingRect(c))
            self.contours = personContours
            # track the people in the frame
            self.people_tracking(self.contours)


    def readDetections(self):
        # return the frame with people detections
        return self.frameDetections 

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
    
    def people_tracking(self, rects):
        global pid
        global entered
        global exited
        for x, y, w, h in rects:
            new = True
            xCenter = x + w/2
            yCenter = y + h/2
            inActiveZone= xCenter in range(self.rangeLeft,self.rangeRight)
            for index, p in enumerate(persons):
                dist = math.sqrt((xCenter - p.getX())**2 + (yCenter - p.getY())**2)
                if dist <= w/2 and dist <= h/2:
                    if inActiveZone:
                        new = False
                        if p.getX() < self.midLine and     xCenter >= self.midLine:
                            print("[INFO] person going left " + str(p.getId()))
                            entered += 1
                        if p.getX() > self.midLine and     xCenter <= self.midLine:
                            print("[INFO] person going right " + str(p.getId()))
                            exited += 1
                        p.updateCoords(xCenter,yCenter)
                        break
                    else: 
                        print("[INFO] person removed " + str(p.getId()))
                        persons.pop(index)
            if new == True and inActiveZone:
                print("[INFO] new person " + str(pid))
                p = People.Person(pid, xCenter, yCenter)
                persons.append(p)
                pid += 1
