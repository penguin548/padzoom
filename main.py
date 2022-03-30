import cv2
import time
import threading
import math
import sys
import numpy
import os
from ast import Pass
from inputs import get_gamepad
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# USB camera setup
src = 'v4l2src device=/dev/video0 ! video/x-raw, width=3840, height=2160, format=NV12 ! appsink'
cap = cv2.VideoCapture(src,cv2.CAP_GSTREAMER)
if cap.isOpened() is False:
    raise("IO Error")

crop_factor = 1
crop_dest_y = 0
crop_dest_x = 0
widowWidth = 1920
windowHeight = 1080
fps_flag = 0
disp_fps = 0
cvt_fps = 0
fhd_flag = False
reset_flag = False

class Gamepad(object):
    # for 8bit normalize
    MAX_JOY_VAL = math.pow(2, 8)

    def __init__(self):
        self.init_flag = False
        self.LeftJoystickY = 0.0
        self.LeftJoystickX = 0.0
        self.A = 0
        self.B = 0
        self.X = 0
        self.Y = 0
        self.HatY = 0
        self.HatX = 0
        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()


    def read(self):
        stickx = self.LeftJoystickX
        sticky = self.LeftJoystickY
        a = self.A
        b = self.B
        hy = self.HatY
        hx = self.HatX 
        return [stickx, sticky, a, b, hy, hx]
    
    def cropZoom(self):
        global crop_factor
        global crop_dest_y
        global crop_dest_x
        global fps_flag
        global fhd_flag

        fps_flag = self.B

        if self.Y:
            fhd_flag = not fhd_flag

        # X axis
        if self.LeftJoystickX < 0.01 and self.LeftJoystickX > -0.01:
            Pass
        else:
            crop_dest_x = (int)(crop_dest_x + round((self.LeftJoystickX * 10)/2,-1))

        # Y axis
        if self.LeftJoystickY < 0.01 and self.LeftJoystickY > -0.01:
            Pass
        else:
            crop_dest_y = (int)(crop_dest_y + round((self.LeftJoystickY * 10)/2,-1))

        # Zoom
        if self.HatY < 0:
            crop_factor = crop_factor + 0.1
        elif self.HatY > 0:
            crop_factor = crop_factor - 0.1
        else:
            Pass
        if self.HatX < 0:
            crop_factor = crop_factor + 1
        elif self.HatX > 0:
            crop_factor = crop_factor - 1
        else:
            Pass
        
        # Reset
        if self.A == 1:
            crop_factor = 1
            crop_dest_y = 0
            crop_dest_x = 0
        
        if crop_factor <= 1:
            crop_factor = 1

        return


    def _monitor_controller(self):
        while not self.init_flag:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y': #HORI Main Stick Y
                    self.LeftJoystickY = (event.state*10 / Gamepad.MAX_JOY_VAL)-5 # normalize between -5 and 5
                elif event.code == 'ABS_X': #HORI Main Stick X
                    self.LeftJoystickX = (event.state*10 / Gamepad.MAX_JOY_VAL)-5 # normalize between -5 and 5
                elif event.code == 'BTN_SOUTH': #HORI Y
                    self.Y = event.state
                elif event.code == 'BTN_NORTH': #HORI X
                    self.X = event.state
                elif event.code == 'BTN_C': #HORI A
                    self.A = event.state
                elif event.code == 'BTN_EAST': #HORI B
                    self.B = event.state
                elif event.code == 'ABS_HAT0Y': #HORI Hat Y
                    self.HatY = event.state
                elif event.code == 'ABS_HAT0X': #HORI Hat X
                    self.HatX = event.state


def draw():
    display_start_time = time.time()
    ret, img = cap.read()
    if ret == False:
         sys.exit()
    
    img = cv2.cvtColor(img,cv2.COLOR_YUV2RGB_NV12)

    ########## ROI Cropping ##########
    gamepad.cropZoom()
    imageh, imagew = img.shape[:2]
    crop_height = imageh * (1/crop_factor)
    crop_width = imagew * (1/crop_factor)
    global crop_dest_y
    global crop_dest_x
    global disp_fps
    global cvt_fps

    if abs(crop_dest_y) > imageh/2-(imageh/crop_factor)/2:
        crop_dest_y = (int)((imageh/2-(imageh/crop_factor)/2)*numpy.sign(crop_dest_y))
    if abs(crop_dest_x) > imagew/2-(imagew/crop_factor)/2:
        crop_dest_x = (int)((imagew/2-(imagew/crop_factor)/2)*numpy.sign(crop_dest_x))
   
    y1 = (int)((crop_height/2)*(crop_factor-1)) + crop_dest_y
    y2 = (int)((crop_height/2)*(crop_factor+1)) + crop_dest_y
    x1 = (int)((crop_width/2)*(crop_factor-1)) + crop_dest_x
    x2 = (int)((crop_width/2)*(crop_factor+1)) + crop_dest_x

    if y1 < 0: y1 = 0
    if y2 < 0: y2 = 0
    if x1 < 0: x1 = 0
    if x2 < 0: x2 = 0

    img = img[y1:y2,x1:x2]
    ########## ROI Cropping END ##########

    if fhd_flag:
        img = cv2.resize(img, dsize=(1920, 1080), interpolation=cv2.INTER_NEAREST)
    else:
        img = cv2.resize(img, dsize=(1440, 810), interpolation=cv2.INTER_NEAREST)

    cvt_fps = round((1.0 / (time.time() - display_start_time)),1)
    if fps_flag:
        cv2.putText(img,
            "CFPS:"+str(cvt_fps)+" DFPS:"+str(disp_fps)+" CropF:"+str(round(crop_factor,2))+" DstXY:"+str(crop_dest_x)+","+str(crop_dest_y),
            org=(10, 50),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.0,
            color=(0, 170, 0),
            thickness=2,
            lineType=cv2.LINE_4)

    h, w = img.shape[:2]
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)

    glEnable(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glBegin(GL_QUADS) 
    glTexCoord2d(0.0, 1.0)
    glVertex3d(-1.0, -1.0,  0.0)
    glTexCoord2d(1.0, 1.0)
    glVertex3d( 1.0, -1.0,  0.0)
    glTexCoord2d(1.0, 0.0)
    glVertex3d( 1.0,  1.0,  0.0)
    glTexCoord2d(0.0, 0.0)
    glVertex3d(-1.0,  1.0,  0.0)
    glEnd()

    glFlush()
    glutSwapBuffers()
    disp_fps = round((1.0 / (time.time() - display_start_time)),1)


def init():
    glClearColor(0.7, 0.7, 0.7, 0.7)

def idle():
    glutPostRedisplay()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glLoadIdentity()
    glOrtho(-w / widowWidth, w / widowWidth, -h / windowHeight, h / windowHeight, -1.0, 1.0)

def keyboard(key, x, y):
    key = key.decode('utf-8')
    # press q to exit
    if key == 'q':
        print('exit...')
        sys.exit()

gamepad = Gamepad()

if __name__ == "__main__":
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(widowWidth, windowHeight)
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB)

    glutEnterGameMode()
    glutSetCursor(GLUT_CURSOR_NONE)
    #glutCreateWindow("Display")

    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    init()
    glutIdleFunc(idle)
    glutMainLoop()
