from tello import Tello
import cv2

def main():
    drone=Tello()
    #frame_read=drone.get_frame_read()
    print(f'Battery level:{drone.get_battery_level()}')
    while True:
        #img=frame_read.frame
        #cv2.imshow('Tello Feed', img)
        drone.update()
    drone.end()
    cv2.destroyAllWindows()

if __name__=='__main__':
    main()
