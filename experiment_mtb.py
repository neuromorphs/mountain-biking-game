####################
#### __ IMPORTS ____
####################
# General libraries
import os
import sys	
import numpy as np
import pandas as pd
from datetime import datetime
import subprocess
from psychopy import visual, event, core
from psychopy.hardware import keyboard

from get_logger import get_logger
log = get_logger() # tobi's logger for printing more informative logging messsages

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
participant = 'Test'  # name of subject
output_path = os.path.join('./results', participant + '_' + datetime.now().strftime("%d_%m_%Y_%H_%M"))
os.makedirs(output_path, exist_ok=True)

# PARAMETERS DEBUGGING
full_screen = False # set to True for real experiment 
ACCUMULATED_RESULTS_FILENAME = 'accumulated_results.csv'

# PARAMETERS EXP
# presentation
driving_time_limit = 120
nr_trials = 10
do_rest = False
time_slide_intro_trial = 1
time_slide_outro_trial = 3
countdown_duration = 3
difficulty=3 # 1-5 difficulty, 1 is easiest
# Define the command to run the Python script. Eventually, add args as new elements of the list
base_command = ['python3', 'mountain_biking.py', f'--driver_name={participant}', f'--output_path={output_path}', f'--difficulty={difficulty}']
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
text = visual.TextStim(win=win, text="Hi "+ str(participant) + "\
	\n\nDuring you will have to control a mountain bike and keep it on track on a downhill pathway.\
	\n\nEach game lasts " + str(driving_time_limit) + " seconds and you can play up to " + str(nr_trials) + " games.\
	\n\nPress a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
if defaultKeyboard.getKeys(keyList=["escape"]):
	sys.exit("terminated early with ESC")
text.autoDraw = False

# Slide 2
text = visual.TextStim(win=win, text="You can use the left and right arrows of the keyboard to play.\
	\n\nWihile playing, please minimize unnecessary movements (eye blinks, face or any other unnecessary body movement).\
	\n\nPress a key on the keyboard to continue!",\
	color="white",
	contrast=contrast,
	wrapWidth=max(win.size)/ratio_text_width,
	height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
if defaultKeyboard.getKeys(keyList=["escape"]):
	sys.exit("terminated early with ESC")
text.autoDraw = False

# Slide 3
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
	sys.exit("terminated early with ESC")
text.autoDraw = False

# Stimuli presentation begins
for i in range(nr_trials):

	# Slide intro of each trial
	text = visual.TextStim(win=win, text="Game " + str(i+1) + "/" + str(nr_trials),  
							color="white",
							contrast=contrast,
							wrapWidth=max(win.size)/ratio_text_width,
							height= max(win.size)/ratio_text_size)
	text.autoDraw = True
	win.flip()
	core.wait(time_slide_intro_trial)
	text.autoDraw = False

	# COUNTDOWN
	countdown_timer(countdown_duration, win)	

	# PLAY GAME
	# Draw fixaxtion cross
	fixation.autoDraw = True
	win.flip()

	# Run the command and capture the output
	trial_name = "--trial_name=trial_" + str(i+1)
	command = base_command + [trial_name]
	log.info(f'running subprocess "{command}"')
	output = subprocess.run(command, capture_output=True, text=True)

	# Check the return code to see if the script ran successfully
	if output.returncode == 0:
		log.info("Script executed successfully.")
		log.info(output.stdout)
	else:
		log.error("Script execution failed.")
		sys.exit("terminated early with escape")

	# Remove fixaxtion cross
	fixation.autoDraw = False
	win.flip()

	# Slide with leaderboard
	d = pd.read_csv(ACCUMULATED_RESULTS_FILENAME, comment='#')
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
	text = visual.TextStim(win=win, text=f"Your error of {avg_err:.3f} ranks you #{rank} out of {len(sorted_errors)}",  
							color="white",
							contrast=contrast,
							wrapWidth=max(win.size)/ratio_text_width,
							height= max(win.size)/ratio_text_size)
	text.autoDraw = True
	win.flip()
	event.waitKeys()
	if defaultKeyboard.getKeys(keyList=["escape"]):
		sys.exit("terminated early with ESC")
	core.wait(time_slide_outro_trial)
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
			sys.exit("terminated early with ESC")
		text.autoDraw = False	

		# Call the countdown_timer function
		countdown_timer(countdown_duration, win)

leaderboard_text='Leaderboard (Rank-Driver-Error-When)\n\n'
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
					   "\n\nThank you for your participation!",
					   color="white",
					   contrast=contrast,
					   wrapWidth=max(win.size)/ratio_text_width,
					   height= max(win.size)/ratio_text_size)
text.autoDraw = True
win.flip()
event.waitKeys()
text.autoDraw = False
win.close()