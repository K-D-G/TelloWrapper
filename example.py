from tello import Tello
from threading import Thread
import cv2

def main():
    drone=Tello()
    frame_read=drone.get_frame_read()
    print(f'Battery level:{drone.get_battery_level()}')
    while True:
        frame=frame_read.frame
        cv2.imshow("Tello feed", frame)
        drone.update()
    drone.end()

if __name__=='__main__':
    main()
