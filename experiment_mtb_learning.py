####################
####################
#### __ IMPORTS ____
####################
# General libraries
import os
from datetime import datetime
import pandas as pd
import numpy as np
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
participant = 'Giorgia'  # name of subject
output_path = os.path.join('./results', participant)
os.makedirs(output_path, exist_ok=True)

# PARAMETERS DEBUGGING
full_screen = True # set to True for real experiment 
ACCUMULATED_RESULTS_FILENAME = 'accumulated_results.csv'

# PARAMETERS EXP
# presentation
driving_time_limit = 60
nr_trials = 10
do_rest = False
time_slide_intro_trial = 1
time_slide_outro_trial = 1
countdown_duration = 3
conditions = ['play', 'motor', 'playback']
base_command = ['python', 'mountain_biking_all_conds.py']
# visual
ratio_text_size = 40
ratio_text_width=2
ratio_cross = 40
contrast = 0.1

# # Command to activate Conda environment on Windows
# activate_cmd = f'conda activate mtb'
# subprocess.run(activate_cmd, shell=True)
# print('Conda environment activated!')

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
	core.quit()
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
	core.quit()
text.autoDraw = False

# Slide 3
text = visual.TextStim(win=win, text="You will also have to other two conditions:\
	\n\n- motor: where you press left and right arrows as if you where playin.\
	\n\n- sensory: where you will just watch the game",\
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

# Slide 4
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
	for cond in conditions:

		# Slide intro of each trial
		text = visual.TextStim(win=win, text="Game " + str(i+1) + "/" + str(nr_trials) + '\n' 
						 							 + " condition: " + cond,  
								color="white",
								contrast=contrast,
								wrapWidth=max(win.size)/ratio_text_width,
								height= max(win.size)/ratio_text_size)
		text.autoDraw = True
		win.flip()
		core.wait(time_slide_intro_trial)
		if defaultKeyboard.getKeys(keyList=["escape"]):
			core.quit()
		text.autoDraw = False

		# # COUNTDOWN
		# countdown_timer(countdown_duration, win)	

		# PLAY GAME
		fixation.autoDraw = True
		win.flip()
		win.winHandle.set_visible(False)  # Hide the PsychoPy window

		# Run the command and capture the output
		trial_str = "trial_" + str(i)
		command = base_command + [f'--driver_name={participant}',
								  f'--trial={trial_str}',
								  f'--condition={cond}']
		print(f"Command to execute: {' '.join(command)}")
		output = subprocess.run(command, capture_output=True, text=True)
		if defaultKeyboard.getKeys(keyList=["escape"]):
			core.quit()
		win.winHandle.set_visible(True)  # Show the PsychoPy window

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
		if cond == "play":
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
				core.quit()
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
				core.quit()
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