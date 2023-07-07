####################
#### __ IMPORTS ____
####################
# General libraries
import os	
import numpy as np
import pandas as pd
from datetime import datetime
import subprocess
from psychopy import visual, event, core
from psychopy.hardware import keyboard
defaultKeyboard = keyboard.Keyboard(backend='iohub') 

# Special functions
def countdown_timer(duration, window):
    countdown_text = visual.TextStim(window, text='', pos=(0, 0), height=50)
    for time_remaining in range(duration, 0, -1):
        countdown_text.text = str(time_remaining)
        countdown_text.draw()
        window.flip()
        core.wait(1)
    
    countdown_text.text = '0'
    countdown_text.draw()
    window.flip()
    core.wait(1)

##############################
#### __ EXPERIMENT CONFIG ____
##############################
# PARTICIPANT INFO
participant = 'Test           ' # 12 characters ALWAYS
output_path = os.path.join('./results', participant + '_' + datetime.now().strftime("%d_%m_%Y_%H_%M"))
os.makedirs(output_path, exist_ok=True)

# PARAMETERS DEBUGGING
full_screen = True 
ACCUMLATED_RESULTS_FILENAME = 'accumulated_results.csv'

# PARAMETERS EXP
# presentation
nr_trials = 1
do_rest = False
rest_time = 10
countdown_duration = rest_time
# Define the command to run the Python script. Eventually, add args as new elements of the list
base_command = ['python3', 'mountain_biking.py', participant, output_path]
# visual
ratio_text_size = 60
ratio_text_width=2
ratio_cross = 40
contrast = 0.1

############################
#### __ PSYCHOPY CONFIG ____
############################ 
win = visual.Window(
	size=[800, 600],
	units="pix",
	fullscr=full_screen,
	color=[-1, -1, -1]
)

win.mouseVisible = False

fixation = visual.shape.ShapeStim(win=win, 
								  vertices="cross", 
								  color='white', 
								  fillColor='white', 
								  contrast=contrast, 
								  size=max(win.size)/ratio_cross)

############################
#### __ EXPERIMENT ____
############################ 

# INTRODUCTION
# Slide 1
text = visual.TextStim(win=win, text="Hi "+ str(participant) + "!\
	\n\nDuring the experiment, you will have to play a mountain bike game.\
	\n\nYou will have to control a mountain bike and keep it on track on a downhill pathway.\
	\n\nEach game lasts ~3 minutes and you can play up to 10 games.\
	\n\nPress a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
if defaultKeyboard.getKeys(keyList=["escape"]):
	core.quit()
text.autoDraw = False

# Slide 2
text = visual.TextStim(win=win, text="You can use the left and right arrows of the keyboard to play.\
	\n\nWihile playing, please minimize unnecessary movements (eye blinks, face or any other unnecessary body movement).\
	\n\nYou will be able to move (but not stand up!) between trials before pressing the key to go on with the new game.\
	\n\nIf you need to get up, please call the experimenter who will help you as the electrodes are very fragile.\
	\n\nPress a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
if defaultKeyboard.getKeys(keyList=["escape"]):
	core.quit()
text.autoDraw = False

# Slide 3
text = visual.TextStim(win=win, text="We are almost ready!\
    \n\nPhones can interfere with the recording, so we invite you to leave it outside the cabin or switch it off.\
	\n\nRemember that the experimenter is always outside the cabin, ready to help you in case you need it.\
	\n\nPress a key on the keyboard to continue!", 
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
if defaultKeyboard.getKeys(keyList=["escape"]):
	core.quit()
text.autoDraw = False

# Slide 5
text = visual.TextStim(win=win, text="The experiment is about to start."\
	"\n\nIf you need to move or to take a break, that's the time!"
	"\n\nWhen you're ready, press a key to start the experiment.", 
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
if defaultKeyboard.getKeys(keyList=["escape"]):
	core.quit()
text.autoDraw = False

# Stimuli presentation begins
for i in range(nr_trials):

	# Slide intro of each trial
	text = visual.TextStim(win=win, text="Trial " + str(i+1) + "/" + str(nr_trials) +\
							"\n\nPress a key when you are ready to play!",  
							color="white",
							contrast=contrast,
							wrapWidth=max(win.size)/ratio_text_width,
							height= max(win.size)/ratio_text_size)
	text.autoDraw = True
	win.flip()
	event.waitKeys()
	if defaultKeyboard.getKeys(keyList=["escape"]):
		core.quit()
	text.autoDraw = False	

	# PLAY GAME
	# Draw fixaxtion cross
	fixation.autoDraw = True
	win.flip()

	# Run the command and capture the output
	traial_name = "trial_" + str(i+1)
	command = base_command + [traial_name]
	output = subprocess.run(command, capture_output=True, text=True)

	# Check the return code to see if the script ran successfully
	if output.returncode == 0:
		print("Script executed successfully.")
		print(output.stdout)
	else:
		print("Script execution failed.")

	# Remove fixaxtion cross
	fixation.autoDraw = False
	win.flip()

	# Slide with leaderboard
	d = pd.read_csv(ACCUMLATED_RESULTS_FILENAME, comment='#')
	drivers = d['driver']
	errors = d['error']
	epoch_times=d['epoch_time']
	# get the last element of the leaderboard
	avg_err=errors.iloc[-1]
	idxs_error= np.argsort(errors)
	sorted_errors=errors[idxs_error]
	sorted_drivers=drivers[idxs_error]
	sorted_epoch_times=epoch_times[idxs_error]
	rank=np.searchsorted(sorted_errors.to_numpy(),avg_err)+1
	
	# Slide intro of each trial
	text = visual.TextStim(win=win, text=f"Your error of {avg_err:.3f} ranks you #{rank} out of {len(sorted_errors)}" +\
							"\n\nPress a key when you are ready to continue!",  
							color="white",
							contrast=contrast,
							wrapWidth=max(win.size)/ratio_text_width,
							height= max(win.size)/ratio_text_size)
	text.autoDraw = True
	win.flip()
	event.waitKeys()
	if defaultKeyboard.getKeys(keyList=["escape"]):
		core.quit()
	text.autoDraw = False	

	## REST
	if do_rest:
		# Slide for the breaks
		text = visual.TextStim(win=win, text="Trial " + str(i+1) + "/" + str(nr_trials) + ' has ended.'\
								"\n\nYou can rest now for a minute, but please look at the countdown and minimize your movements." + \
								"\n\nPress a key on the keyboard to continue!",
								color="white",
								contrast=contrast,
								wrapWidth=max(win.size)/ratio_text_width,
								height= max(win.size)/ratio_text_size)
		text.autoDraw = True
		win.flip()
		event.waitKeys()
		if defaultKeyboard.getKeys(keyList=["escape"]):
			core.quit()
		text.autoDraw = False	

		# Call the countdown_timer function
		countdown_timer(countdown_duration, win)

leaderboard_text='Leaderboard (Rank-Driver-Error-When)'
top10_counter=1
for d,e,t in zip(sorted_drivers,sorted_errors,sorted_epoch_times):
	datetime_obj = datetime.utcfromtimestamp(t)
	when=datetime_obj.strftime('%Y-%m-%d %H:%M')
	txt=f'{top10_counter}\t\t{d}\t\t{e:.3f}\t\t\t{when}'
	leaderboard_text+=txt+'\n'
	top10_counter+=1
	if top10_counter>10:
		break


### LEADERBOARD
text = visual.TextStim(win=win, text=leaderboard_text + \
					   "\n\nPress one final time a key to end the experiment!", 
					   color="white",
					   contrast=contrast,
					   wrapWidth=max(win.size)/ratio_text_width,
					   height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False
win.close()


### END EXPERIMENT
text = visual.TextStim(win=win, text="Thank you "+ str(participant) + " for your participation!\
					   \n\nIf you'd like, we can keep you updated on the experiment's outcomes.\
					   \n\nPress one final time a key to end the experiment!", 
					   color="white",
					   contrast=contrast,
					   wrapWidth=max(win.size)/ratio_text_width,
					   height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False
win.close()