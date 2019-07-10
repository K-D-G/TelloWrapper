from tello import Tello
import time

def main():
    drone=Tello()
    print(f'Battery level:{drone.get_battery_level()}')

    while True:
        drone.update()

if __name__=='__main__':
    main()
