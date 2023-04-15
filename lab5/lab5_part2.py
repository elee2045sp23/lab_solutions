import cv2
import numpy as np
import time
import sys
targets = ['person','cell phone','cup']

# start by reading our pre-trained model
net = cv2.dnn.readNet('yolov5s.onnx')
# and the strings that correspond to each class ID (0-79)
with open("classes.txt") as f:
    classes = [s.strip() for s in f.readlines()]

def main():
    cap = cv2.VideoCapture(0) # 0 is an index to the first camera
    while cap.isOpened():
        res, frame = cap.read() # ret will indicate success or failure, frame is a numpy array
        if not res:
            continue # no frame read
        process_frame(frame)
        cv2.imshow("my window", frame) # quick gui
        if cv2.waitKey(1) == ord('q'):
            break #exit this loop
    cap.release()  # stop the camera
    cv2.destroyAllWindows() # closes the open gui window 

# a utility function to display a prompt in a frame
def promptText(frame, info:str):
    cv2.putText(frame, info, (5,30) , cv2.FONT_HERSHEY_COMPLEX, .5, (0,0,255))

def process_frame(frame):
    blob = format_yolov5(frame) # convert to yolo input
    net.setInput(blob) 
    predictions = net.forward() # run the network
    output=predictions[0] # we only provided one frame, so we get the first prediction
    # these three will hold
    boxes = []
    confidences = []
    class_ids = [] # we'll fill these up below
    for row in output: # each row in the output is one box, xc,yc,w,h,conf,80 class probabilities
        if row[4] > .5: # we only keep boxes with good confidence
            xc, yc, w, h = row[0], row[1], row[2], row[3] # note, these are in 640x640 space
            max_index = cv2.minMaxLoc(row[5:])[3][1] # this will figure out the highest probability class
            class_ids.append(max_index) 
            # figure out the location of the box
            left = int(xc-w/2) # the boxes are in center coordinates, so move by half width                                       
            top = int(yc-h/2)                                       
            width = int(w)                                             
            height = int(h)     
            # append the confidence and the box, because well need it
            confidences.append(row[4])                                                                                   
            boxes.append([left,top,width,height]) 
    
    # eliminate duplicate boxes with non-maximum suppression (gives best box indexes)
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.25, 0.45) 

    draw_boxes(frame,boxes,indexes,class_ids)
    
    # this will determine if any objects are missing
    targets_missing = [] #we'll determine if they are missing one at a time
    for c in targets:
        found = False # assume it won't be found
        for i in indexes:
            if classes[class_ids[i]] == c: 
                found = True
        if not found:
            targets_missing.append(c) 
    # successful if there are no missing targets        
    if len(targets_missing) == 0:
        cv2.imwrite(f"{time.time()}.png",frame)
        promptText(frame,"All found")
        cv2.imshow("my window", frame) # quick gui
        cv2.waitKey(1000)
        sys.exit()
    else: # let the user know what's missing
        promptText(frame,",".join(targets_missing))

def draw_boxes(frame,boxes,indexes,class_ids):
    # now we draw (in the original frame) the best boxes
    sf = int(max(frame.shape[0],frame.shape[1])/640) # determine the scale factor to convert back
    for i in indexes:
        x,y,w,h = [v*sf for v in boxes[i]] # extract the box values multiplied by the scale factor
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2) # draw a blue box
        cv2.putText(frame, # draw the class label in red
                    classes[class_ids[i]],
                    (x,y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))
        
# this function converts a typical opencv color frame to the yolov5 format
def format_yolov5(frame):
    # put the image in square big enough
    col, row, _ = frame.shape 
    _max = max(col, row) # get the maximum dimension
    resized = np.zeros((_max, _max, 3), np.uint8) # create a new square frame
    resized[0:col, 0:row] = frame # insert the original image at the top left
    # yolo works with images that have float pixels between 0 and 1, 640x640, RGB channels
    # opencv has byte pixels, BGR channels (by default)
    # the below function converts to the required format
    result = cv2.dnn.blobFromImage(resized, 1/255.0, (640, 640), swapRB=True)
    return result

if __name__=="__main__":
    main()


