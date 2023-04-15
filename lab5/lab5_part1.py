import cv2 # cv2 is a newer interface to opencv
import mediapipe as mp
import time
from dataclasses import dataclass
from bleak import BleakClient, BleakScanner # get button state from the m5stickc
import threading
import asyncio
import struct

mp_pose = mp.solutions.pose 
pose = mp_pose.Pose(min_detection_confidence=.5) # raise to have less false detections
target_landmark_index = 0 # nose

#this class will hold everything we need to keep track of in our system
@dataclass
class SystemState:
    rep_count: int = 0 # how many repetitions of the exercise have been recorded
    button_presses: int = 0 # how many time the button has been pressed
    state_num: int = 0 # 0 - start, 1 - Top, 2 - bottom
    target: any = None # where the nose is at any given time
    top_y: float = None # where the top target will be set
    bottom_y: float = None # where the bottom target will be set
    start_time: float = 0.0 # when they started (to calculate reps/s)
    end_time: float = 0.0 # when they ended
    running = True # for bluetooth
state = SystemState() 

# this will hold an M5 sticks sensor values (re-used, partially from lab 4)
@dataclass 
class M5Input: 
    acc: tuple
    button: int #only using this for now
    battery: int
    connected: bool=False
m5 = M5Input((0,0,0),0,0) # note, could have 2 of these! 

# this is a thread for async bluetooth, it will update m5
def run_controller(m5, address):
    # attempt a connection to the bluetooth device
    def callback(sender,data:bytearray):
        ax,ay,az,button,battery=struct.unpack("<fffbh",data)
        if button == 0 and m5.button == 1:
            buttonPressed()

        m5.acc = (ax,ay,az)
        m5.button = button
        m5.battery = battery
        m5.connected = True


    async def run():

        while state.running: # we'll keep doing this until the program ends
            devices = await BleakScanner.discover(1) # short discovery time so it starts quickly
            for d in devices:
                if d.name == "M5StickCPlus-Kyle": # this approach should work on windows or mac
                    async with BleakClient(d) as client:
                        await client.start_notify("5e8be540-13b8-49bf-af35-63b725c5c066",callback)
                        while state.running:
                            await asyncio.sleep(1)
                        break #we are done

    asyncio.run(run())
    m5.connected = False
t = threading.Thread(target=run_controller, args = (m5, "e8:9f:6d:00:a7:52")) # in theory, multiple m5 sticks would work
t.start() 

def main():
    cap = cv2.VideoCapture(0) # 0 is an index to the first camera
    while cap.isOpened():
        res, frame = cap.read() # ret will indicate success or failure, frame is a numpy array
        if not res:
            continue # no frame read
        process_frame(frame)
        cv2.imshow("my window", frame) # quick gui
        key = cv2.waitKey(1)
        if key == ord('q'):
            break #exit this loop
        if key == ord('g'): # this is convenient for testing the system
            buttonPressed()

    cap.release()  # stop the camera
    cv2.destroyAllWindows() # closes the open gui window 
    state.running = False
    t.join()
    # done!

# a utility function to display a prompt in a frame
def promptText(frame, info:str):
    cv2.putText(frame, info, (5,30) , cv2.FONT_HERSHEY_COMPLEX, .5, (0,0,255))

def process_frame(frame):

    pose_results = pose.process(frame) # find any bodies

    # if we don't find anything, there's nothing to do this frame
    if pose_results.pose_landmarks == None: 
        return 
    
    state.target = pose_results.pose_landmarks.landmark[target_landmark_index]

    # note that (0,0) is the top left of the image
    if state.button_presses == 0: # we are waiting for a button press
        promptText(frame, "stand up and hit the button to set your high mark")
    if state.button_presses == 1:
        promptText(frame, "squat to your target position to set your low mark")
    if state.button_presses == 2: # we are in the active counting state
        if state.state_num == 0 and state.target.y < state.top_y: # substate 0, where we are waiting for the top target to be reached to begin the counting process
            state.state_num = 1
        elif state.state_num == 1 and state.target.y > state.bottom_y: # substate 1, where we are waiting for the bottom target to be reached
            state.state_num = 2
        elif state.state_num == 2 and state.target.y < state.top_y: # substate 2, where we count a repetition (back to the top)
            state.state_num = 1
            state.rep_count += 1

        # this draws a line at the bottom marker to hit    
        cv2.line(frame,(0,int(frame.shape[0]*state.bottom_y)),(frame.shape[1],int(frame.shape[0]*state.bottom_y)),(0,0,255),2)
        promptText(frame, f"Reps: {state.rep_count}, Reps/s: {state.rep_count/(time.perf_counter()-state.start_time):.2f}")
    
    if state.button_presses == 1 or state.button_presses == 2:
        # this draws a line at the top marker to hit
        cv2.line(frame,(0,int(frame.shape[0]*state.top_y)),(frame.shape[1],int(frame.shape[0]*state.top_y)),(0,0,255),2)
    
    if state.button_presses == 3:
        promptText(frame, f"Reps: {state.rep_count}, Reps/s: {state.rep_count/(state.end_time-state.start_time):.2f}.  Hit the button to start again.")
    
    # this draws the tracked body
    for l in pose_results.pose_landmarks.landmark: # iterate through each landmark
        loc = (int(l.x*frame.shape[1]),int(l.y*frame.shape[0])) # convert to image coordinates
        cv2.circle(frame,center=loc,radius=2,color=(255,0,0),thickness=2) # draw

    

def buttonPressed():

    if state.button_presses == 0 and state.target != None:
        state.top_y = state.target.y + .01 # shift down by 5% because otherwise, it's hard to reach
        state.button_presses = 1
        print(state.top_y)
    elif state.button_presses == 1 and state.target.y > (state.top_y+.01): # must have a lower target
        state.bottom_y = state.target.y - .01 # shift up by 5% because otherwise, it's hard to reach
        state.start_time = time.perf_counter()
        state.button_presses = 2
        print(state.bottom_y)
    elif state.button_presses == 2:
        # finish workout
        state.end_time = time.perf_counter()
        state.button_presses = 3
    elif state.button_presses == 3:
        # reset
        state.button_presses = 0
        state.rep_count = 0
        state.start_time = 0.0
        state.end_time = 0.0

if __name__=="__main__":
    main()