from ast import Pass
from inputs import get_gamepad
from multiprocessing import Process,Queue,Pool
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import cv2
import time
import sys


# USB camera setup
src = 'v4l2src device=/dev/video0 ! video/x-raw, width=3840, height=2160, format=NV12 ! appsink'

crop_factor = 1
crop_dest_y = 0
crop_dest_x = 0
widowWidth = 1920
windowHeight = 1080
image_queue = Queue(maxsize=8)

def read_frames(src,queue):
    cap = cv2.VideoCapture(src,cv2.CAP_GSTREAMER)
    try:
        while True:
            if cap.isOpened():
                display_start_time = time.time()
                ret, img = cap.read()
                if ret == False:
                    sys.exit()
                #img = cv2.resize(img, dsize=(1920, 1620))
                img = cv2.cvtColor(img,cv2.COLOR_YUV2RGB_NV12)
                #img = cv2.resize(img, dsize=(widowWidth, windowHeight))
                #img = cv2.resize(img, dsize=(widowWidth, windowHeight), interpolation=cv2.INTER_NEAREST)
                print("Capt FPS = ", round((1.0 / (time.time() - display_start_time)),1))
                queue.put(img)
            else:
                cap.release()
                raise("IO Error")
    except KeyboardInterrupt:
        print('stop!')
        sys.exit()


def draw():
    if not image_queue.empty():
        display_start_time = time.time()
        img = image_queue.get()

        img = cv2.resize(img, dsize=(widowWidth, windowHeight))
        print("Prcs FPS = ", round((1.0 / (time.time() - display_start_time)),1))
        h, w = img.shape[:2]
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glColor3f(1.0, 1.0, 1.0)

        # Enable texture map
        glEnable(GL_TEXTURE_2D)
        # Set texture map method
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # draw square
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
        print("Draw FPS = ", round((1.0 / (time.time() - display_start_time)),1))
    else:
        return


def init():
    glClearColor(0.7, 0.7, 0.7, 0.7)

def idle():
    glutPostRedisplay()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glLoadIdentity()
    #Make the display area proportional to the size of the view
    glOrtho(-w / widowWidth, w / widowWidth, -h / windowHeight, h / windowHeight, -1.0, 1.0)

def keyboard(key, x, y):
    # convert byte to str
    key = key.decode('utf-8')
    # press q to exit
    if key == 'q':
        print('draw exit.')
        sys.exit()

def draw_frames():
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(widowWidth, windowHeight)
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB)

    #glutEnterGameMode()
    #glutSetCursor(GLUT_CURSOR_NONE)
    glutCreateWindow("Display")

    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    init()
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    
    p1 = Process(target=read_frames, args=(src,image_queue))
    p2 = Process(target=draw_frames, args=())
    
    p1.start()
    p2.start()
    
    while True:
        if not p2.is_alive():
            p1.terminate()
            print("Capture Process is Terminated.")
            sys.exit()

