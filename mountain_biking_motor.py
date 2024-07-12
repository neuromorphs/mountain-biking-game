# mountain biking game simplified and written in pure python for Telluride 2023
# Tobi Delbruck and Giorgia Cantisani
# MIT license

#################
## IMPORTS
#################
import sys
import os.path
import argparse
import pygame
import numpy as np
from time import time
# import debugpy # uncommment to attach to this process if running as subprocess from experiment_mtb.py

#################
## PARAMS
#################
DRIVE_TIME_LIMIT_S = 10 # experiment terminates after this time in seconds
FPS = 60 # changed to 60 for algorithmic trails
SX = 800  # window width, 'size x'
SY = int(3 * SX / 4)  # window height (size y)
STEERING_RATE = .01  # keyboard steering rate
USE_MOUSE=False # true to control position directly by mouse x position in window
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

parser = argparse.ArgumentParser()
parser.add_argument('--driver_name','-n', type=str, help='name of driver, e.g. tobi', default=None)
parser.add_argument('--output_path', '-o', type=str, help='output folder', default='./results')
parser.add_argument('--trial_name','-t', type=str, help='Trial name to append to results CSV file name', default='0')
args=parser.parse_args() 

if len(sys.argv)>1:
    driver_name = args.driver_name  #'01'
    output_path = args.output_path  #'./results'
    trial_name = args.trial_name    #'1'
else:
    driver_name = 'Test'
    output_path = os.path.join('./results', driver_name)
    trial_name = '0'
    os.makedirs(os.path.join(output_path, driver_name), exist_ok=True)

#################
# General settings
#################
sx2 = int(SX / 2)  # half window width

driving = True # flag True during a drive
playing_game=True # flag True while doing multiple drives
while playing_game: # run games until we quit or if game_mode==False then we quit after one run

    # set up pygame
    pygame.init()
    window_size = [SX, SY]  # width and height
    screen = pygame.display.set_mode(window_size)
    font = pygame.font.SysFont(None, 36) # font used for overlay text
    clock = pygame.time.Clock()

    # data file
    data_file_name = os.path.join(output_path, driver_name + '_' + trial_name +'_motor.csv')
    data_file = open(data_file_name,'w')
    data_file.write('time(s),steering,\n')

    # game loop
    steering11 = 0  # steering angle -1 to 1
    steering11_inertia = 0
    start_time=None
    driving=True

    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    frame_counter = 0
    trigger_frame_counter = 0
    elapsed_time=0
    driving_started=False # set True when path crosses current time line

    time_now=time()
    time_start=time_now
    time_last=time_now
    while driving:
        frame_counter += 1
 
        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            steering11_inertia -= STEERING_RATE * (abs(steering11_inertia) * 5 + 0.05)
        elif keys[pygame.K_RIGHT]:
            steering11_inertia += STEERING_RATE * (abs(steering11_inertia) * 5 + 0.05)
        steering11 += steering11_inertia
        steering11_inertia *= 0.9
        steering11 = np.clip(steering11, a_min=-1, a_max=1)

        if USE_MOUSE:
            mx,my=pygame.mouse.get_pos()
            steering11=(2.*(mx-sx2))/SX

        time_now=time()
        time_delta=time_now-time_last
        time_last=time_now

        # all rendering below here, no data updates
        screen.fill(BLACK)

        # error measurements start here
        SYNC_BOX_SIZE=50
        if trigger_frame_counter<100:  # detect first time that trail crosses current time line
            trigger_frame_counter += 1
            if start_time is None:
                start_time=time() # only set start_time once
            pygame.draw.rect(screen, WHITE, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height
        else:
            pygame.draw.rect(screen, BLACK, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height

        elapsed_time= time() - start_time
        data_file.write(f'{elapsed_time:.6f},{steering11:.4f}\n')
        driving_started=True

        if elapsed_time>DRIVE_TIME_LIMIT_S or keys[pygame.K_ESCAPE] or keys[pygame.K_x]:
            driving=False
            playing_game=False

        # draw text
        time_left=DRIVE_TIME_LIMIT_S-elapsed_time
        img = font.render(f'Time left: {time_left:.1f}s', True, WHITE)
        screen.blit(img, (20, 20))

        # update screen
        pygame.display.flip()
        ms_since_last_frame=clock.tick(FPS) 

# close window on quit
pygame.quit()
