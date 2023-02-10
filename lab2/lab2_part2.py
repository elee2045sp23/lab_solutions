import serial
num_trials=3 # modify this line to read more lines
s = serial.Serial("COM3",115200) # this line may need to be modified for your port

# our data comes through as string1,string2\n
# we'll wait for a line, then write it directly to the file
with open("reactions.csv","w") as reactions:
    for trial in range(num_trials):
        line = s.readline().decode().strip()
        if trial != 0: # this code ensures that we don't add a blank newline at the end
            reactions.write("\n")
        reactions.write(line)

s.close() #serial port should be closed after being opened


