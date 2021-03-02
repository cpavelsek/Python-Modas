from gpiozero import MotionSensor, LED, Button
from picamera import PiCamera
from time import sleep
import datetime as dt
import random
import requests
import json

class Modas:
    def __init__(self):
        # init PiCamera
        self.camera = PiCamera()
        # set camera resolution
        #self.camera.rotation = 180
        self.camera.resolution = (800,600)
        # init green, red LEDsimport random 
        self.green = LED(24)
        self.red = LED(23)
        # init button
        self.button = Button(8)
        # init PIR
        self.pir = MotionSensor(25)
        
        # when button  is released, toggle system arm / disarm
        self.button.when_released = self.toggle
        
        # system is disarmed by default
        self.armed = False 
        self.disarm_system()
        
    def init_alert(self):
        self.green.off()
        self.red.blink(on_time=.25, off_time=.25, n=None, background=True)
        print("motion detected")
        
        # create a new event - replace with your API
        url = 'https://modas-jsg.azurewebsites.net/api/event/'
        headers = { 'Content-Type': 'application/json'}
        #random number to determine location
        randomLocation = random.randint(0,2)
        # get current date / time
        t = dt.datetime.now()
        # format date in json format for RESTful API
        t_json = "{0}-{1}-{2}T{3}:{4}:{5}".format(t.strftime("%Y"), t.strftime("%m"), t.strftime("%d"), t.strftime("%H"), t.strftime("%M"), t.strftime("%S"))
        payload = { 'timestamp': t_json, 'flagged': False, 'locationId': randomLocation }
        # post the event
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        print(r.status_code)
        print(r.json())
        
        #log entries to file
        today = dt.datetime.today().strftime('%Y-%m-%d')

        filename = today + ".log"
        f = open(filename, "a")
        f.write( str(t_json) + ", False ," + str(randomLocation) +", " + str(r.status_code) +"\n")
        f.close()
        
        
        # Take photo
        self.snap_photo()
        # delay
        sleep(2)
    def snap_photo(self):
        # determine current date/time
        t = dt.datetime.now()
        # determine the number of seconds that have elapsed since midnight
        s = t.second + (t.minute * 60) + (t.hour * 60 * 60)
        # use the date/time to generate a unique file name for photos (1/1/2018~21223.png)
        self.camera.capture("/home/pi/Desktop/{0}~{1}.jpg".format(t.strftime("%Y-%m-%d"), s))

    def reset(self):
        self.red.off()
        self.green.on()
        
    def toggle(self):
        self.armed = not self.armed
        if self.armed:
            self.arm_system()
        else:
            self.disarm_system()
            
    def arm_system(self):
        print("System armed in 3 seconds")
        self.red.off()
        # enable camera
        self.camera.start_preview()
        # 3 second delay
        self.green.blink(on_time=.25, off_time=.25, n=6, background=False)
        # enable PIR
        self.pir.when_motion = self.init_alert
        self.pir.when_no_motion = self.reset
        self.green.on()
        print("System armed")
        
    def disarm_system(self):
        # disable PIR
        self.pir.when_motion = None
        self.pir.when_no_motion = None
        # disable camera
        self.camera.stop_preview()
        self.red.on()
        self.green.off()
        print("System disarmed")

m = Modas()

try:
    # program loop
    while True:
        sleep(.001)
# detect Ctlr+C
except KeyboardInterrupt:
    if m.armed:
        m.disarm_system()
