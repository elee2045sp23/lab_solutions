import serial
num_trials=3
s = serial.Serial("COM3",115200)


with open("reactions.csv","w") as reactions:
    for trial in range(num_trials):
        line = s.readline().decode().strip()
        if trial != 0:
            reactions.write("\n") #new line
        reactions.write(line)
        
s.close() #serial port should be closed after being opened


