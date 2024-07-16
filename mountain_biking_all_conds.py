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
import csv
#import debugpy # uncommment to attach to this process if running as subprocess from experiment_mtb.py

print('subprocess started!')

#################
## PARAMS
#################
DRIVE_TIME_LIMIT_S = 120 # experiment terminates after this time in seconds
SPEED = 2  # how many rows to shift image per pygame tick
FPS = 60 # changed to 60 for algorithmic trails
SX = 800  # window width, 'size x'
SY = int(3 * SX / 4)  # window height (size y)
STEERING_RATE = .01  # keyboard steering rate
USE_MOUSE = False # true to control position directly by mouse x position in window
base_path = './results'

parser = argparse.ArgumentParser()
parser.add_argument('--driver_name','-n', type=str, help='name of driver, e.g. tobi', default='Test')
parser.add_argument('--trial','-t', type=str, help="trial number", default='trial_0')
parser.add_argument('--condition','-c', type=str, help="condition can be play, playback or motor", default='play')
args=parser.parse_args()

if len(sys.argv)>1:
    debugging = False
    cond = args.condition
    driver_name = args.driver_name  
    output_path = os.path.join(base_path, driver_name)
    os.makedirs(os.path.join(output_path), exist_ok=True)
    trial_name = args.trial
    TRAIL_CSV_FILE_NAME = 'trails/Action Delay.csv' # args.trail #'trails/trail_' + str(diff) + '.csv'
    STEERING_CSV_FILE_NAME = os.path.join(output_path, driver_name + '_' + args.trial + '_play.csv')
else:
    debugging = True
    cond = 'playback'
    driver_name = 'last_test'
    output_path = os.path.join('./results', driver_name)
    trial_name = 'trial_0'
    TRAIL_CSV_FILE_NAME ='trails/Action Delay.csv'
    STEERING_CSV_FILE_NAME = os.path.join(output_path, driver_name + '_' + trial_name + '_play.csv')
    os.makedirs(os.path.join(output_path), exist_ok=True)

#################
# General settings
#################
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

sx2 = int(SX / 2)       # half window width
st_y = int(3 * SY / 4)  # y position of steering line from top
st_h = int(SY / 10)     # height of steering line
st_line_width = 3       # width of steering stuff

playing_game = True 
while playing_game: # run games until we quit or if game_mode==False then we quit after one run
    pygame.init()
    window_size = [SX, SY]  # width and height
    screen = pygame.display.set_mode(window_size)
    font = pygame.font.SysFont(None, 36) # font used for overlay text
    clock = pygame.time.Clock()

    # set up trail
    trail = np.empty(SY) * np.nan  # locations of trail by row (from top) range -1 to 1
    trail_csvfile = None
    trail_reader = None
    trail_pos_current = 0.
    trail_angle_current = 0

    csv.register_dialect('skip-comments', skipinitialspace=True)
    trail_csvfile = open(TRAIL_CSV_FILE_NAME, 'r')
    trail_reader = csv.DictReader(filter(lambda row: row[0] != '#', trail_csvfile), dialect='skip-comments')

    if cond == 'playback':
        steering_csv_file = open(STEERING_CSV_FILE_NAME, 'r')
        steering_reader = csv.DictReader(filter(lambda row: row[0] != '#', steering_csv_file), dialect='skip-comments')

    # data file
    data_file_name = os.path.join(output_path, driver_name + '_' + trial_name +'_' + cond + '.csv') 
    data_file = open(data_file_name,'w')
    data_file.write('time,error, trail_pos, steering, trail_time\n')

    # game loop
    steering11 = 0  # steering angle -1 to 1
    steering11_inertia = 0
    running_score = 0
    frame_counter = 0
    accumulated_err=0
    trigger_frame_counter = 0
    elapsed_time=0
    driving_started = False # set True when path crosses current time line
    trail_pos_current = 0 # current location of trail

    driving = True
    while driving:
        frame_counter += 1
 
        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        # read keyboard and mouse
        keys = pygame.key.get_pressed()
        if cond != 'playback':
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

        # read or generate trail info
        try:
            current_row = next(trail_reader)
        except StopIteration:
            done = True

        trail_time = float(current_row['time'])
        trail_pos_current = float(current_row['trail_pos']) / 10  # range in file is -10 to +10, map to -1 to +1

        trail[1:] = trail[0:-1]  # shift all the star rows down one
        trail[0] = trail_pos_current  # show trail from top of image
        current_trail_pos = trail[st_y]  # the trail at the current timeline, target for user -1 to 1

        # drawing
        if frame_counter%SPEED!=0:
            continue

        # all rendering below here, no data updates
        screen.fill(BLACK)

        if cond != 'motor':
            # draw line where we are
            pygame.draw.line(screen, BLUE, [0, st_y], [SX, st_y], st_line_width)  # the base line where we are and where we show current steering line

            # draw trail pixels
            for i in range(SY):
                if not np.isnan(trail[i]):
                    l = (1 + trail[i]) * sx2 - 2
                    w = 5
                    t = i
                    h = 5
                    r = pygame.Rect(l, t, w, h)
                    pygame.draw.rect(screen, WHITE, r)

            # draw steering wheel position
            st_pos_px = sx2 + steering11 * sx2
            pygame.draw.line(screen, GREEN, [st_pos_px, st_y - st_h / 2], [st_pos_px, st_y + st_h / 2], st_line_width)

        # compute error
        err = (current_trail_pos - steering11) / 2  # steering error, range -1 to 1, ideally zero
        if not np.isnan(err): # measurement starts here, path has crossed line of driving

            # error measurements start here
            SYNC_BOX_SIZE=50
            if trigger_frame_counter<100:  # detect first time that trail crosses current time line
                trigger_frame_counter += 1
                start_time = time() # only set start_time once
                pygame.draw.rect(screen, WHITE, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height
            else:
                pygame.draw.rect(screen, BLACK, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height

            # if playback, start reading steering data
            if cond == 'playback':
                current_row_steering = next(steering_reader)
                steering11 = float(current_row_steering['steering'])
                st_pos_px = sx2 + steering11 * sx2
                pygame.draw.line(screen, GREEN, [st_pos_px, st_y - st_h / 2], [st_pos_px, st_y + st_h / 2], st_line_width)
                # trail_time = float(current_row_steering['trail_time'])


            elapsed_time = time() - start_time
            data_file.write(f'{elapsed_time:.6f},{err:.4f},{current_trail_pos:.4f},{steering11:.4f},{trail_time:.4f},\n')
            if cond != 'motor':
                pygame.draw.line(screen, RED, [sx2 + current_trail_pos * sx2, st_y], [sx2 + steering11 * sx2, st_y], width=st_line_width)

            # accumulate total error
            accumulated_err+=np.abs(err)
            avg_err=accumulated_err/frame_counter
            running_score=1/avg_err
            driving_started=True

            # maybe terminate
            if elapsed_time > DRIVE_TIME_LIMIT_S or keys[pygame.K_ESCAPE]:
                driving=False
                playing_game=False

        # draw text
        if debugging:
            time_left=DRIVE_TIME_LIMIT_S - elapsed_time
            img = font.render(f'Time left: {time_left:.1f}s score={running_score:.0f}', True, WHITE)
            screen.blit(img, (20, 20))

        # update screen
        pygame.display.flip()
        ms_since_last_frame = clock.tick(FPS) 

# close window on quit
pygame.quit()