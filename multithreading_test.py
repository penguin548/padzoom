from ast import Pass
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from inputs import get_gamepad
import cv2
import time
import threading
import queue


# USB camera setup
src = 'v4l2src device=/dev/video0 ! video/x-raw, width=3840, height=2160, format=NV12 ! appsink'

widowWidth = 1920
windowHeight = 1080
imageWidth = 3840
imageHeight = 2160


class ThreadingVideoCaptureConverter:
    def __init__(self, src, max_queue_size=8):
        self.video = cv2.VideoCapture(src,cv2.CAP_GSTREAMER)
        self.q = queue.Queue(maxsize=max_queue_size)
        self.stopped = False

    def start(self):
        thread = threading.Thread(target=self.update, daemon=True)
        thread.start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            if not self.q.full():
                ok, frame = self.video.read()
                frame = cv2.cvtColor(frame,cv2.COLOR_YUV2RGB_NV12)
                self.q.put((ok, frame))
                if not ok:
                    self.stop()
                    return

    def read(self):
        return self.q.get()

    def stop(self):
        self.stopped = True

    def release(self):
        self.stopped = True
        self.video.release()

    def isOpened(self):
        return self.video.isOpened()

    def get(self, i):
        return self.video.get(i)

def draw():
    display_start_time = time.time()
    ret, img = cap.read() #read camera image
    if ret == False:
         sys.exit()

    img = cv2.resize(img, dsize=(widowWidth, windowHeight))

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
    
    print("Display FPS = ", round((1.0 / (time.time() - display_start_time)),1))


def init():
    glClearColor(0.7, 0.7, 0.7, 0.7)

def idle():
    glutPostRedisplay()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glLoadIdentity()
    glOrtho(-w / widowWidth, w / widowWidth, -h / windowHeight, h / windowHeight, -1.0, 1.0)

def keyboard(key, x, y):
    # convert byte to str
    key = key.decode('utf-8')
    # press q to exit
    if key == 'q':
        cap.release()
        print('Exit...')
        sys.exit()


cap = ThreadingVideoCaptureConverter(src)
if not cap.isOpened():
    raise RuntimeError
cap.start()

if __name__ == "__main__":
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(widowWidth, windowHeight)
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE )

    #glutEnterGameMode()
    #glutSetCursor(GLUT_CURSOR_NONE)
    glutCreateWindow("Display")

    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    init()
    glutIdleFunc(idle)
    glutMainLoop()
