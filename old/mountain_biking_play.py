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
# import debugpy # uncommment to attach to this process if running as subprocess from experiment_mtb.py

#################
## PARAMS
#################
DRIVE_TIME_LIMIT_S = 10 # experiment terminates after this time in seconds
SPEED = 2  # how many rows to shift image per pygame tick
FPS = 60 # changed to 60 for algorithmic trails
SX = 800  # window width, 'size x'
SY = int(3 * SX / 4)  # window height (size y)
STEERING_RATE = .01  # keyboard steering rate
USE_MOUSE = False # true to control position directly by mouse x position in window

parser = argparse.ArgumentParser()
parser.add_argument('--driver_name','-n', type=str, help='name of driver, e.g. tobi', default=None)
parser.add_argument('--output_path', '-o', type=str, help='output folder', default='./results')
parser.add_argument('--trial_name','-t', type=str, help='Trial name to append to results CSV file name', default='0')
parser.add_argument('--difficulty','-d', help="trail difficulty, range 1-5", default=1,type=int)
args=parser.parse_args()

if len(sys.argv)>1:
    driver_name = args.driver_name  
    output_path = args.output_path 
    trial_name = args.trial_name
    diff = args.difficulty
    TRAIL_CSV_FILE_NAME ='trails/trail_' + str(diff) + '.csv'
else:
    driver_name = 'Test'
    output_path = os.path.join('./results', driver_name)
    trial_name = '0'
    diff = str(1)
    TRAIL_CSV_FILE_NAME ='trails/Action Delay.csv'
    os.makedirs(os.path.join(output_path, driver_name), exist_ok=True)

#################
# General settings
#################
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

sx2 = int(SX / 2)  # half window width
st_y = int(3 * SY / 4)  # y position of steering line from top
st_h = int(SY / 10)  # height of steering line
st_line_width = 3  # width of steering stuff

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
    if not TRAIL_CSV_FILE_NAME is None:
        csv.register_dialect('skip-comments', skipinitialspace=True)
        trail_csvfile = open(TRAIL_CSV_FILE_NAME, 'r')
        trail_reader = csv.DictReader(filter(lambda row: row[0] != '#', trail_csvfile), dialect='skip-comments')

    # data file
    data_file_name = os.path.join(output_path, driver_name + '_' + trial_name +'_play.csv') 
    data_file = open(data_file_name,'w')
    data_file.write('time(s),error,trail_pos, steering\n')

    # game loop
    steering11 = 0  # steering angle -1 to 1
    steering11_inertia = 0
    start_time=None
    running_score = 0

    frame_counter = 0
    accumulated_err=0
    trigger_frame_counter = 0
    elapsed_time=0
    driving_started=False # set True when path crosses current time line
    trail_pos_current=0 # current location of trail

    time_now=time()
    time_start=time_now
    time_last=time_now

    driving = True
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

        # read or generate trail info
        if not TRAIL_CSV_FILE_NAME is None:
            try:
                current_row = next(trail_reader)
            except StopIteration:
                showed_trigger_flash = False
                trail[:] = np.nan
                frame_counter=0

                trail_csvfile.close()
                trail_csvfile = open(TRAIL_CSV_FILE_NAME, 'r')
                trail_reader = csv.DictReader(filter(lambda row: row[0] != '#', trail_csvfile), dialect='skip-comments')  # https://stackoverflow.com/questions/14158868/python-skip-comment-lines-marked-with-in-csv-dictreader
                current_row = next(trail_reader)

                time_start=time.time()
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
                if start_time is None:
                    start_time=time() # only set start_time once
                pygame.draw.rect(screen, WHITE, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height
            else:
                pygame.draw.rect(screen, BLACK, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height

            elapsed_time= time() - start_time
            data_file.write(f'{elapsed_time:.6f},{err:.4f},{current_trail_pos:.4f},{steering11:.4f},\n')
            pygame.draw.line(screen, RED, [sx2 + current_trail_pos * sx2, st_y], [sx2 + steering11 * sx2, st_y], width=st_line_width)

            # accumulate total error
            accumulated_err+=np.abs(err)
            avg_err=accumulated_err/frame_counter
            running_score=1/avg_err
            driving_started=True

            # maybe terminate
            if elapsed_time>DRIVE_TIME_LIMIT_S or keys[pygame.K_ESCAPE] or keys[pygame.K_x]:
                driving=False
                playing_game=False

        # draw text
        time_left=DRIVE_TIME_LIMIT_S-elapsed_time
        img = font.render(f'Time left: {time_left:.1f}s score={running_score:.0f}', True, WHITE)
        screen.blit(img, (20, 20))

        # update screen
        pygame.display.flip()
        ms_since_last_frame=clock.tick(FPS) 

# close window on quit
pygame.quit()
