import csv
import os

# This program reads an OpenFace csv output, and copies desired data into a new CSV file
# It also adds columns for time between blinks, user presence, working time, and break time
# What results is a very accurate estimate of user presence, based on a 45 second time delay

# ------------------------------------------------------------------------------------------
blink_threshold = 45    # number of seconds w/out blinking until the user is considered away
mdp_sec = 15            # number of seconds to recalculate mdp state
# ------------------------------------------------------------------------------------------

print("Welcome! This is an OpenFace Processor created by Carson Gray.")
print("This program reads, condenses, and processes OpenFace CSV output files to prepare them for analysis.")
print("It also tracks emotions, determines user presence and work times, and decides a Markov State.")
print("\nFirst, identify the csv file you want to process. Be sure to use double back slashes (\\\\) in the Filepath.")

# User inputs their file
file_found = False
while file_found == False:
    file_path = input("Filepath: ")
    try:
        with open(file_path, encoding='utf-8') as f:
            file_found = True
    except FileNotFoundError:
        print(f"Sorry, the file {file_path} wasn't found.")

# A list of all the columns we want from OpenFace output
desired_indeces = [
    0, 2, 4, 11, 12, 
    293, 294, 295, 
    296, 297, 298
    ]
my_index = 679
max_index = 714
while (my_index < max_index):
    desired_indeces.append(my_index)
    my_index += 1

# initialize our variables
user_present = 1            # is the user present?
work_length = 0             # clock tracking working time
break_length = 0            # clock tracking break time

work_list = []              # these lists store above variables
break_list = []
user_presence = []

last_blink = 0              # seconds since the user last blinked (au45_c = 1)
temp_au45 = 0               # blink value (au45_c) at this instant

happy_c = 0
angry_c = 0
surprised_c = 0
disgust_c = 0
sad_c = 0

happy_r = 0
angry_r = 0
surprised_r = 0
disgust_r = 0
sad_r = 0

last_happy = 0
last_angry = 0
last_surprised = 0
last_disgust = 0
last_sad = 0

temp_timestamp = 0          # timestamp value (timestamp) at this instant
time_inc = 0.033            # time increment for OpenFace (30 fps)

first_time = True           # used for logic later on
second_time = False
my_row = []
lines_parsed = 0
successful = True

frame_30min = 0              # track frame by frame
frame_unfocused = 0
frame_unhappy = 0

mdp_30min = 0               # based on 15 sec increments
mdp_unfocused = 0
mdp_unhappy = 0

mdp_state = 1               # determined by mdp_X

min30_list = []
unfocused_framelist = []
unfocused_mdplist = []
unhappy_mdplist = []

# We are copying select columns from the OpenFace file and adding a column that tracks time between blinks
# As we do this, we will internally track user presence, time spent working, and time on break
with open(file_path) as file_object:                                    # Reading the OpenFace csv file...
    csv_reader = csv.reader(file_object)
    print("\nExtracting From File")

    with open('temp_output.csv', 'w', newline = '') as new_file:        # ...and writing desired data into a temporary csv file
        csv_writer = csv.writer(new_file)
        mdp_counter = 0
        frame3_counter = 1

        for line in csv_reader:                     # iterate through each row of the OpenFace file          
            
            del my_row[:]                           # every pass, we add to this list and write it to the new csv file
            for index in desired_indeces:           # copying the data from the desired OpenFace columns
                try:
                    my_row.append(line[index])
                except IndexError:                  # if a datapoint is missing, it copies a 0
                    my_row.append(0)

            if first_time:
                my_row.append("last_blink")         # on the first pass, we title any columns we want to add
                my_row.append("happy_c")
                my_row.append("angry_c")
                my_row.append("surprised_c")
                my_row.append("disgust_c")
                my_row.append("sad_c")
                my_row.append("happy_r")
                my_row.append("angry_r")
                my_row.append("surprised_r")
                my_row.append("disgust_r")
                my_row.append("sad_r")
                my_row.append("last_happy")
                my_row.append("last_angry")
                my_row.append("last_surprised")
                my_row.append("last_disgust")
                my_row.append("last_sad")
                first_time = False
                second_time = True
                
            
            elif second_time:                       # on the second pass, we initialize the custom columns
                work_list.append(0)                 # we initialize our lists as well (used for internal logic)
                break_list.append(0)
                user_presence.append(1)
                unfocused_mdplist.append(0)
                unhappy_mdplist.append(0)
                count = 1
                while count < 17:
                    my_row.append(0)
                    count += 1
                second_time = False
            
            else:
                try:
                    temp_au45 = float(line[713])    # we retrieve the user's blink state (AU45_c)
                    

                    # retrieving focus state, x gaze is 5, y gaze is 6
                    if frame3_counter == 3:
                        frame3_counter = 1
                        if float(line[5]) < (-0.3) or float(line[5]) > 0.3 or float(line[6]) < 0.1 or float(line[6]) > 0.7:
                            frame_unfocused = 1
                        else:
                            frame_unfocused = 0
                        unfocused_framelist.append(frame_unfocused)     # writing to a temp list, which will be used to determine real list
                    frame3_counter += 1

                    # retrieving emotional states
                    if float(line[700]) == 1 and float(line[704]) == 1:     # happy
                        # AU06_c, AU12_c
                        happy_c = 1         # set emotion as present
                        last_happy = 1      # set as most recent emotional expression
                        last_angry = 0
                        last_surprised = 0
                        last_disgust = 0
                        last_sad = 0
                    else:
                        happy_c = 0
                    
                    if float(line[698]) == 1 and float(line[699]) == 1 and float(line[701]) == 1 and float(line[709]) == 1: # angry
                        # AU04_c, AU05_c, AU07_c, AU23_c
                        angry_c = 1
                        last_happy = 0
                        last_angry = 1
                        last_surprised = 0
                        last_disgust = 0
                        last_sad = 0
                    else:
                        angry_c = 0
                    
                    if float(line[711]) == 1 and float(line[699]) == 1 and float(line[697]) == 1 and float(line[696]) == 1: # surprised
                        # AU01_c, AU02_c, AU05_c, AU26_c
                        surprised_c = 1
                        last_happy = 0
                        last_angry = 0
                        last_surprised = 1
                        last_disgust = 0
                        last_sad = 0
                    else:
                        surprised_c = 0

                    if float(line[702]) == 1 and float(line[706]) == 1:     # disgusted
                        # AU09_c, AU15_c
                        disgust_c = 1
                        last_happy = 0
                        last_angry = 0
                        last_surprised = 0
                        last_disgust = 1
                        last_sad = 0
                    else:
                        disgust_c = 0

                    if float(line[696]) == 1 and float(line[698]) == 1 and float(line[706]) == 1:       # sad
                        # AU01_c, AU04_c, AU15_c
                        sad_c = 1
                        last_happy = 0
                        last_angry = 0
                        last_surprised = 0
                        last_disgust = 0
                        last_sad = 1
                    else:
                        sad_c = 0

                    # averaging the AU_r values respective to above AU_c values
                    happy_r = (float(line[683]) + float(line[687])) / 2
                    angry_r = (float(line[681]) + float(line[682]) + float(line[684]) + float(line[692])) / 4
                    surprised_r = (float(line[679]) + float(line[680]) + float(line[682]) + float(line[694])) / 4
                    disgust_r = (float(line[685]) + float(line[689])) / 2
                    sad_r = (float(line[679]) + float(line[681]) + float(line[689])) / 3

                    # determining markov states every 15 sec
                    if mdp_counter == (30 * mdp_sec):
                        mdp_counter = 0
                        count_1 = 0
                        count_0 = 1
                        for frame in unfocused_framelist:        # finding number of unfocused states in last 15 sec
                            if frame == 1:
                                count_1 += 1
                            else:
                                count_0 += 1
                        if count_1 / (count_1 + count_0) >= 0.2:         #if distracted for 3+ of 15 seconds
                            mdp_unfocused = 1
                        else:
                            mdp_unfocused = 0
                        del unfocused_framelist[:]               # reset list for next 15 sec
                    
                        count = 0
                        while count < (30 * mdp_sec):                   # every 15 sec, fill in the chosen mdp value for those 15 sec
                            unfocused_mdplist.append(mdp_unfocused)
                            unhappy_mdplist.append(mdp_unhappy)
                            count += 1
                    
                    mdp_counter += 1
                
                except IndexError:
                    print("Extraction Complete")            # it goes one past the end

                if temp_au45 == 1:                          # if the user blinked, we know they are present
                    last_blink = 0
                    user_present = 1
                    break_length = 0
                    work_length += time_inc
                    work_list.append(work_length)           # and we note this presence in our lists
                    break_list.append(break_length)
                    user_presence.append(user_present)

                else:                                       # if the user didn't blink
                    last_blink += time_inc                  # we add to our blink increment
                    if user_present == 1: 
                        work_length += time_inc
                        work_list.append(work_length)
                        break_list.append(break_length)
                        user_presence.append(user_present)
                    else:
                        break_length += time_inc
                        break_list.append(break_length)
                        work_list.append(work_length)
                        user_presence.append(user_present)
                
                if last_blink < (blink_threshold + (time_inc / 2)) and last_blink > (blink_threshold - (time_inc / 2)):
                    user_present = 0    # if the user doesn't blink for 45 seconds, we know they are away
                    
                    if (len(work_list) - (blink_threshold * 30) - 1) > 0:           # we go back 45 seconds worth of data (45 sec x 30 fps)
                        my_index = (len(work_list) - (blink_threshold * 30) - 1)    # the ' - 1' is because index readings start at 0
                    else:
                        my_index = 0
                    end_index = len(work_list)
                    
                    while my_index < end_index:                                         # for each data point in the last 45 seconds...
                        work_list[my_index] = 0                                         # we remove the point from user's working clock
                        break_list[my_index] = (break_list[my_index - 1] + time_inc)    # we start tracking their break clock
                        user_presence[my_index] = 0                                     # and we note that they were away
                        my_index += 1
                    
                    work_length = 0
                    break_length = blink_threshold      # finally, we set the current value of their break clock to 45 seconds

                my_row.append(last_blink)   # after the logic is through, we add last_blink to my_row, as well as the emotional states
                
                my_row.append(happy_c)
                my_row.append(angry_c)
                my_row.append(surprised_c)
                my_row.append(disgust_c)
                my_row.append(sad_c)
                
                my_row.append(happy_r)
                my_row.append(angry_r)
                my_row.append(surprised_r)
                my_row.append(disgust_r)
                my_row.append(sad_r)
                
                my_row.append(last_happy)
                my_row.append(last_angry)
                my_row.append(last_surprised)
                my_row.append(last_disgust)
                my_row.append(last_sad)
            
            csv_writer.writerow(my_row)     # and we write my_row into the new csv file

# The OpenFace csv is closed, and the file we wrote to is saved
# Now we read from the new file, and write it to the final output
# We turn our user_presence, work_list, and break_list data into columns
with open('temp_output.csv') as file_object:                        
    csv_reader_2 = csv.reader(file_object)
    print("\nProcessing File")

    try:
        with open('detector_output.csv', 'w', newline = '') as new_file:      
            csv_writer_2 = csv.writer(new_file)
            first_time = True
            lines_parsed = 0
            mdp_counter = 0
        
            for line in csv_reader_2:   
                my_index = 0
                del my_row[:]
                while my_index < len(line):
                    my_row.append(line[my_index])       # copy each line
                    my_index += 1

                if first_time:
                    my_row.append("user_present")       # on the first pass, title the new columns
                    my_row.append("work_length")
                    my_row.append("break_length")
                    
                    my_row.append("mdp_30min")
                    my_row.append("mdp_unfocused")
                    my_row.append("mdp_unhappy")
                    my_row.append("mdp_state")
                    first_time = False
                
                else:
                    if lines_parsed < len(user_presence):
                        my_row.append(user_presence[lines_parsed])  # and finally, copy our lists into the final file
                        my_row.append(work_list[lines_parsed])
                        my_row.append(break_list[lines_parsed])
                        
                        if work_list[lines_parsed] >= (1800):   # testing 30 min working time for mdp
                            frame_30min = 1
                        else:
                            frame_30min = 0
                        min30_list.append(frame_30min)

                        if mdp_counter == (30 * mdp_sec):      # 30 fps * # seconds set at top (15 default)
                            mdp_counter = 0

                            # determine if working for 30
                            count_1 = 0
                            for frame in min30_list:
                                if frame == 1:
                                    count_1 += 1
                            if count_1 >= 1:        # if they've hit 30 min, working check built in
                                mdp_30min = 1
                            else:
                                mdp_30min = 0
                            del min30_list[:]       # reset list for next 15 sec

                            # determine mdp state
                            if user_presence[lines_parsed] == 0:
                                mdp_state = 0
                            elif mdp_30min == 0 and unfocused_mdplist[lines_parsed] == 0 and unhappy_mdplist[lines_parsed] == 0:                  
                                mdp_state = 1
                            elif mdp_30min == 0 and unfocused_mdplist[lines_parsed] == 1 and unhappy_mdplist[lines_parsed] == 0:
                                mdp_state = 2
                            elif mdp_30min == 0 and unfocused_mdplist[lines_parsed] == 0 and unhappy_mdplist[lines_parsed] == 1:
                                mdp_state = 3
                            elif mdp_30min == 0 and unfocused_mdplist[lines_parsed] == 1 and unhappy_mdplist[lines_parsed] == 1:
                                mdp_state = 4
                            elif mdp_30min == 1 and unfocused_mdplist[lines_parsed] == 0 and unhappy_mdplist[lines_parsed] == 0:
                                mdp_state = 5
                            elif mdp_30min == 1 and unfocused_mdplist[lines_parsed] == 1 and unhappy_mdplist[lines_parsed] == 0:
                                mdp_state = 6
                            elif mdp_30min == 1 and unfocused_mdplist[lines_parsed] == 0 and unhappy_mdplist[lines_parsed] == 1:
                                mdp_state = 7
                            else:
                                mdp_state = 8

                        my_row.append(mdp_30min)
                        try:  
                            my_row.append(unfocused_mdplist[lines_parsed])
                            my_row.append(unhappy_mdplist[lines_parsed])
                        except IndexError:
                            my_row.append(0)
                            my_row.append(0)
                        my_row.append(mdp_state)
                        
                        mdp_counter += 1
                        lines_parsed += 1

                csv_writer_2.writerow(my_row)
    except PermissionError:
        successful = False

os.remove('temp_output.csv')    # delete the intermediate file, keeping only the final output

if successful:
    print("Processing Complete")
    print("\nThe processed file can be accessed at detector_output.csv")
    print("I hope this program was helpful!")
else:
    print("Processing Failed")
    print("\nIt looks like your output file is still open from last time. Close it and try again!")
