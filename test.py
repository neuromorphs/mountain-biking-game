from psychopy import visual, core
import subprocess

# Define the command to run the Python script. Eventually, add args as new elements of the list
command = ['python3', 'mountain_biking.py']

win = visual.Window()
text = visual.TextStim(win, text='Hello, PsychoPy!')
text.draw()
win.flip()

# PLAY GAME
# Run the command and capture the output
output = subprocess.run(command, capture_output=True, text=True)

# Check the return code to see if the script ran successfully
if output.returncode == 0:
    print("Script executed successfully.")
else:
    print("Script execution failed.")

# Print the output of the script if needed
print(output.stdout)

# core.wait(10)
# win.close()
# core.quit()