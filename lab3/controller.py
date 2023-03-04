import tkinter as tk
import paho.mqtt.client as mqtt
import time
broker = "info8000.ga"
topic_status = "ugaelee2045sp23/kjohnsen/light_status"
topic_control_color = "ugaelee2045sp23/kjohnsen/light_control_color"
topic_control_status = "ugaelee2045sp23/kjohnsen/light_control_status"


def toggleLight():
    light_status = 0 if light_status_var.get() == "ON" else 1
    client.publish(topic_control_status,bytearray([light_status]))

#this is a little more advanced validation
def tryGetColorValue(Entry:tk.Entry):
    try:
        v = int(Entry.get())
        if v > 255:
            v = 255
        elif v < 0:
            v = 0
        return v
    except:
        Entry.delete(0,tk.END)
        Entry.insert(0,"0")
        return 0

def sendColor():
    r = tryGetColorValue(R_Entry)
    g = tryGetColorValue(G_Entry)
    b = tryGetColorValue(B_Entry)
    to_send = bytearray([r,g,b])
    client.publish(topic_control_color,to_send)
    
def setColor(r,g,b):
    color_frame.config(bg=f"#{r:02x}{g:02x}{b:02x}")

def pumpMQTT():
    client.loop(0)
    root.after(10,pumpMQTT) #repeat this

def onMessageFromLight(client_obj, userdata, message:mqtt.MQTTMessage):
    if message.topic == topic_status:
        on = int(message.payload[0])
        r = int(message.payload[1])
        g = int(message.payload[2])
        b = int(message.payload[3])
        setColor(r,g,b)
        if on:
            light_status_var.set("ON") 
        else:
            light_status_var.set("OFF") 
        light_time_var.set(time.ctime())

client = mqtt.Client()
client.username_pw_set("giiuser","giipassword")
client.on_message = onMessageFromLight
client.connect(broker)
client.subscribe(topic_status)
# current state of the lightbulb
root = tk.Tk()
root.title("Light Controller")
status_frame = tk.LabelFrame(root,text="Light Status")
status_frame.pack(fill=tk.X, expand=1,padx=10)
light_status_var = tk.StringVar(root,"unknown")
light_time_var = tk.StringVar(root,"No update yet")
light_status_label = tk.Label(status_frame,textvariable=light_status_var).pack()
light_time_label = tk.Label(status_frame,textvariable=light_time_var).pack()
color_frame = tk.Frame(status_frame,width=50,height=50)
color_frame.pack(fill=tk.X, expand=1,padx=10,pady=10)
setColor(r=0,b=0,g=0)

# control widgets
control_frame = tk.LabelFrame(root,text="Light Control")
control_frame.pack(fill=tk.X, expand=1,padx=10)
tk.Button(control_frame,text="Toggle Light",command=toggleLight).grid(row=0,column=0,columnspan=2)
tk.Label(control_frame,text="R:").grid(row=1,column=0)
tk.Label(control_frame,text="G:").grid(row=2,column=0)
tk.Label(control_frame,text="B:").grid(row=3,column=0)
R_Entry = tk.Entry(control_frame,width=20)
G_Entry = tk.Entry(control_frame,width=20)
B_Entry = tk.Entry(control_frame,width=20)
R_Entry.grid(row=1,column=1)
G_Entry.grid(row=2,column=1)
B_Entry.grid(row=3,column=1)
tk.Button(control_frame,text="Set Color",command=sendColor).grid(row=4,column=0,columnspan=2)

pumpMQTT()
root.mainloop()

