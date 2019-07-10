import socket
import time
import threading
from threading import Thread
import cv2

#Make sure we can get the video stream and add a way (if there isn't one) of accessing
#it
#Do tests on all of the functions
#Upload to github

#Help from: https://ubuntuforums.org/showthread.php?t=2394609
import sys, termios, tty, os, time
def getch():
    fd=sys.stdin.fileno()
    old_settings=termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch=sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

class Tello:
    def __init__(self, log=True):
        self.UDP_IP='192.168.10.1'
        self.UDP_PORT_COMMAND=8889
        self.UDP_PORT_STATE=8890
        self.UDP_IP_VIDEO='0.0.0.0'
        self.UDP_PORT_VIDEO=11111

        self.TIME_OUT=0.5 #seconds
        self.TIME_BETWEEN_COMMANDS=0.5
        self.TIME_BETWEEN_RC_CONTROL_COMMANDS=0.5

        self.log=log
        self.override=False
        self.can_rc=False
        self.last_rc_control_sent=0

        self.left_right_velocity=0
        self.forward_backward_velocity=0
        self.up_down_velocity=0
        self.yaw_velocity=0
        self.override_speed=1
        self.drone_speed=20

        self.last_received_command=time.time()
        self.capture=None #For cv2
        self.background_frame_read=None
        self.stream_on=False

        self.address=(self.UDP_IP, self.UDP_PORT_COMMAND)
        self.client_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('', self.UDP_PORT_COMMAND))
        self.response=None

        self.thread=Thread(target=self.run_udp_receiver, args=())
        self.thread.daemon=True
        self.thread.start()

        self.thread_override=Thread(target=self.override_check, args=())
        self.thread_override.daemon=True
        self.thread_override.start()

        self.send_command_return('command')


    def run_udp_receiver(self):
        while True:
            try:
                self.response, _=self.client_socket.recvfrom(1024)
            except Exception as e:
                print(e)
                break

    def override_check(self):
        while True:
            override=getch()
            if override==chr(27):
                self.land()
                quit()
            if override==' ':
                self.override=True
                if self.log:
                    print('User override')

            if self.override:
                if override=='w': #Forward
                    self.forward_backward_velocity=int(self.drone_speed*self.override_speed)
                elif override=='s': #Backward
                    self.forward_backward_velocity=-int(self.drone_speed*self.override_speed)
                else:
                    self.forward_backward_velocity=0

                if override=='a': #Left
                    self.left_right_velocity=-int(self.drone_speed*self.override_speed)
                elif override=='d': #Right
                    self.left_right_velocity=int(self.drone_speed*self.override_speed)
                else:
                    self.left_right_velocity=0

                if override=='z': #Rotate counter clockwise
                    self.yaw_velocity=-int(self.drone_speed*self.override_speed)
                elif override=='c': #Rotate clockwise
                    self.yaw_velocity=int(self.drone_speed*self.override_speed)
                else:
                    self.yaw_velocity=0

                if override=='q': #Up
                    self.up_down_velocity=-int(self.drone_speed*self.override_speed)
                elif override=='e': #Down
                    self.up_down_velocity=int(self.drone_speed*self.override_speed)
                else:
                    self.up_down_velocity=0

                if override=='t': #Takeoff
                    self.takeoff()

                if override=='l': #Land
                    self.land()

    def update(self):
        if self.can_rc:
            self.send_rc_control(self.left_right_velocity, self.forward_backward_velocity, self.up_down_velocity, self.yaw_velocity)

    def get_udp_video_address(self):
        return 'udp://@'+self.UDP_IP_VIDEO+':'+str(self.UDP_PORT_VIDEO)

    def get_video_capture(self):
        if self.capture is None:
            self.capture=cv2.VideoCapture(self.get_udp_video_address())
        if not self.capture.isOpened():
            self.capture.open(self.get_udp_video_address())
        return self.capture

    def get_frame_read(self):
        if self.background_frame_read is None:self.background_frame_read=BackgroundFrameRead(self, self.get_udp_video_address()).start()
        return self.background_frame_read

    def stop_video_capture(self):
        return self.streamoff()

    def end(self):
        if self.stream_on:
            self.streamoff()
        if self.background_frame_read is not None:
            self.background_frame_read.stop()
        if self.capture is not Nonr:
            self.cap.release()

    def send_command_without_return(self, command):
        if not isinstance(command, str):
            raise ValueError('Command must be a string')
            return
        difference=time.time()*1000-self.last_received_command
        if difference<self.TIME_BETWEEN_COMMANDS:
            time.sleep(difference)
        timestamp=int(time.time()*1000)
        self.client_socket.sendto(command.encode('utf-8'), self.address)

    def send_command_return(self, command):
        if not isinstance(command, str):
            raise ValueError('Command must be a string')
            return
        difference=time.time()*1000-self.last_received_command
        if difference<self.TIME_BETWEEN_COMMANDS:
            time.sleep(difference)
        timestamp=int(time.time()*1000)
        self.client_socket.sendto(command.encode('utf-8'), self.address)

        while self.response is None:
            if time.time()*1000-timestamp>self.TIME_OUT*1000:
                return False
        self.last_received_command=time.time()*1000
        response=self.response
        self.response=None
        if response.decode('utf-8')=='error' and self.log:
            print(f'Command {command} returned ERROR, please take control')

        return response.decode('utf-8')

    #Control commands
    def takeoff(self):
        self.can_rc=True
        return self.send_command_return('takeoff')

    def land(self):
        self.can_rc=False
        return self.send_command_return('land')

    def streamon(self):
        return self.send_command_return('streamon')

    def streamoff(self):
        return self.send_command_return('streamoff')

    def emergency(self):
        return self.send_command_return('emergency')
    def panic(self):
        return self.emergency()

    def up(self, dist):
        return self.send_command_return(f'up {dist}')
    def down(self, dist):
        return self.send_command_return(f'down {dist}')
    def left(self, dist):
        return self.send_command_return(f'left {dist}')
    def right(self, dist):
        return self.send_command_return(f'right {dist}')
    def forward(self, dist):
        return self.send_command_return(f'forward {dist}')
    def back(self, dist):
        return self.send_command_return(f'back {dist}')
    def rotate_clockwise(self, deg):
        return self.send_command_return(f'cw {deg}')
    def rotate_counter_clockwise(self, deg):
        return self.send_command_return(f'ccw {deg}')
    def flip(self, direction):
        if len(direction)>1:
            direction=direction[0]
            if direction not in ['l', 'r', 'f', 'b']:
                return 'error'
        return self.send_command_return(f'flip {direction}')
    def go(self, x, y, z, speed):
        return self.send_command_return(f'go {x} {y} {z} {speed}')
    def curve(self, x1, y1, z1, x2, y2, z2, speed):
        return self.send_command_return(f'curve {x1} {y1} {z1} {x2} {y2} {z2} {speed}')


    #Setter commands
    def set_speed(self, s):
        return self.send_command_return(f'speed {s}')
    def send_rc_control(self, left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity):
        if not(int(time.time()*1000)-self.last_rc_control_sent<self.TIME_BETWEEN_RC_CONTROL_COMMANDS):
            self.last_rc_control_sent=int(time.time()*1000)
            return self.send_command_without_return('rc %s %s %s %s'%(left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity))
    def set_wifi_password(self, password):
        return self.send_command_return(f'wifi ssid {password}')

    #Getter functions (receive data about the drone)
    def get_speed(self):
        return self.send_command_return('speed?')
    def get_battery_level(self):
        return self.send_command_return('battery?')
    def get_fly_time(self):
        return self.send_command_return('time?')
    def get_height(self):
        return self.send_command_return('height?')
    def get_temperature(self):
        return self.send_command_return('temp?')
    def get_attitude(self):
        return self.send_command_return('attitude?')
    def get_barometer(self):
        return self.send_command_return('baro?')
    def get_acceleration(self):
        return self.send_command_return('acceleration?')
    def get_tof(self):
        return self.send_command_return('tof?')
    def get_wifi_snr(self):
        return self.send_command_return('wifi?')


class BackgroundFrameRead:
    def __init__(self, tello, address):
        tello.capture=cv2.VideoCapture(address)
        self.capture=tello.capture

        if not self.capture.isOpened():
            self.capture.open(address)

        self.grabbed, self.frame=self.capture.read()
        self.stopped=False
    def start(seld):
        Thread(target=self.update_frame, args=())
        return self
    def update_frame(self):
        while not self.stopped:
            if not self.grabbed or not self.capture.isOpened():
                self.stop()
            else:
                self.grabbed, self.frame=self.capture.read()
    def stop(self):
        self.stopped=True
