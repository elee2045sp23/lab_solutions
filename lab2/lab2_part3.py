import matplotlib.pyplot as plt

with open("reactions.csv","r") as reactions:
    data = reactions.readlines()

# book keeping variables
delay_times = []
reaction_times = []
good_or_bad = [] # will store colors for plot
average_good_time = 0
num_good = 0

# Our data is string of the format string1,string2\n representing two integers
# The below code converts that format into two integers representing the 
# delay time and the reaction time. It also adds those to their respective lists
for line in data:
    parts = line.split(",")
    delay_time = int(parts[0])
    reaction_time = int(parts[1])
    delay_times.append(delay_time)
    reaction_times.append(reaction_time)
    # the graph requires that we compute an average good time
    # this is an appropriate place to calculate that, and to compute
    # some colors for good and bad reaction times
    if reaction_time >= delay_time:
        average_good_time += reaction_time
        num_good += 1 
        good_or_bad.append("blue") 
    else:
        good_or_bad.append("red") 

# Now we have all of the data for the graph
xticks = list(range(0,len(delay_times)))
plt.bar(xticks, height=reaction_times, color=good_or_bad)
plt.xticks(xticks, labels=xticks)
plt.xlabel("Trial")
plt.ylabel("Time (ms)")
if num_good > 0: # we need to guard against a divide by zero
    plt.title(f"Average Time For Valid Trials={(average_good_time/num_good):.2f} ms")
plt.savefig("reactions.png")
plt.show()
