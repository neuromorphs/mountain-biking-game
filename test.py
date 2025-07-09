# from psychopy import visual, core
import subprocess

# Define the command to run the Python script. Eventually, add args as new elements of the list
base_command = ['python3', 'mountain_biking.py']

participant = 'Test'
trail = './trails/trail_1.csv'
# Check if it exists
import os
if not os.path.exists(trail):
    print(f"Trail {trail} does not exist.")


condition = 'play'

base_command = ['python3', 'mountain_biking_all_conds.py']


# Construct the command
command = base_command + [
    f'--driver_name={participant}',
    f'--trail={trail}',
    f'--condition={condition}'
]
print(f"Command to execute: {' '.join(command)}")

# Run the command and capture the output
try:
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    print("Subprocess output:", result.stdout)
except subprocess.CalledProcessError as e:
    print("Subprocess error:", e)
    print("Output:", e.output)

# win = visual.Window()
# text = visual.TextStim(win, text='Hello, PsychoPy!')
# text.draw()
# win.flip()

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