# mountain biking game simplified and written in pure python for Telluride 2023
# Tobi Delbruck and Giorgia Cantisani
# MIT license

import sys
import os.path

from get_logger import get_logger

log = get_logger()
from prefs import prefs
prefs=prefs()

import pygame
import logitechG27_wheel
# import socket
import numpy as np
import csv
from datetime import datetime
from time import time
from easygui import  enterbox
import pandas as pd
import matplotlib as plt

try:
    import vlc
except Exception as e:
    log.error(f'{e}: pip install python-vlc and install VLC (https://www.videolan.org/vlc/) to your system. Y'
                    f'ou may need to restart your python IDE. See also https://stackoverflow.com/questions/59014318/filenotfounderror-could-not-find-module-libvlc-dll ;'
                    f'you might need 64 bit version of VLC since default installs 32-bit version')

#################
## PARAMS
#################

ACCUMULATED_RESULTS_FILENAME='accumulated_results.csv'

DRIVE_TIME_LIMIT_S=60 # experiment terminates after this time in seconds

# following trail files are taken from  https://github.com/neuromorphs/WheelCon which is forked from https://github.com/Doyle-Lab/WheelCon
# header line added here
# TRAIL_CSV_FILE_NAME = 'trails/trail.csv' # starts with small angles, goes to big angles
# TRAIL_CSV_FILE_NAME ='trails/Vision Delay.csv' # has only big angles
TRAIL_CSV_FILE_NAME ='trails/Action Delay.csv' # used for actual demo, has lots of sharp turns

# if TRAIL_CSV_FILE_NAME=None, then we generate the track 
# algorithmically according to following parameters. 
# The trail always turns back when reaching edge
TRAIL_SEED=0 # random seed to fix the track
TRAIL_TURN_INTERVAL_S=3 # Poisson interval, i.e. Poisson rate is 1/TRAIL_TURN_INTERVAL
TRAIL_ANGLE_LIMIT_DEG=60 # trail angle from vertical limit, sampled uniformly


USE_TRIGGER_SOUND = False
TRIGGER_SOUND_FILE=None

FPS = 100 # target rendering frames per second

# Cedrus XID trigger box
USE_XID = False
# COM port for CGX dry electrode
USE_CGX = False
CGX_COM_PORT = 'COM4'

# window settings
SX = 800  # window width, 'size x'
SY = int(3 * SX / 4)  # window height (size y)

SPEED = 2  # how many rows to shift image per pygame tick
LIGHT_SPEED = 3  # how fast stars wiggle their brightness

STEERING_RATE = .01  # keyboard steering rate
USE_MOUSE=True # true to control position directly by mouse x position in window

# sound
DRIVING_SONG= 'media/Sookie_ Sookie.mp3'
GET_READY_TO_DRIVE_SOUND= 'media/GetReady.wav'

############ end params

# data file has this header
driver_name=prefs.get('last_driver', '')

game_mode=True # start assuming we run in demo game mode that continues forever
output_path='results'
trial_name='0'
arguments = sys.argv[1:]
if len(arguments)==3:
    game_mode=False # only run once
    driver_name = arguments[0]  #'Karan'
    output_path = arguments[1]  #'./results'
    trial_name = arguments[2]
    log.info(f'running in EEG experiment mode with driver_name={driver_name} output_path={output_path} trial_name={trial_name}')
elif len(arguments)!=0:
    print(f'arguments {arguments} not valid.\nUsage: python mountain_biking.py driver_name output_path trail_name\nZero arguments starts game mode')
    quit(1)


#################
## TRIGGERS
#################
# None of those is used at the moment
# as we are using photodiode to trigger EEG

# Trigger sound
if USE_TRIGGER_SOUND:
    from playsound import playsound
    TRIGGER_SOUND_FILE='cowbell3.wav'

if USE_CGX:
    import serial
    from serial import serial


if USE_XID:
    try:
        import pyxid2
    except FileNotFoundError as e:
        log.error(
            f'cannot load driver DLL for USB serial port? {e}\n You may need to install drivers from https://ftdichip.com/drivers/d2xx-drivers/')

#################
# General settings
#################
# define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARKBLUE = (0, 0, 128)

sx2 = int(SX / 2)  # half window width
st_y = int(3 * SY / 4)  # y position of steering line from top
st_h = int(SY / 10)  # height of steering line
st_line_width = 3  # width of steering stuff

br_th_y = int(SY * .9)  # from top, y starts with 0 at top of pygame display
br_th_x = int(SX * .2)
brake_pos = [br_th_x, br_th_y]
throttle_pos = [SX - br_th_x, br_th_y]


driving_song_player:vlc.MediaPlayer = None
get_ready_sound_player:vlc.MediaPlayer=None
if vlc:
    driving_song_player: vlc.MediaPlayer = vlc.MediaPlayer(DRIVING_SONG)
    log.debug(f'loaded song {DRIVING_SONG}')

driving = True # flag True during a drive
playing_game=True # flag True while doing multiple drives

while playing_game: # run games until we quit or if game_mode==False then we quit after one run
    if game_mode: # not collecting data
        driver_name=prefs.get('last_driver','')
        driver_name = enterbox(msg='Enter driver name', title='Start a new drive', default=driver_name, strip=True)
        if driver_name is None:
            log.info('cancelled, quitting now')
            pygame.quit()
            quit(0)
        prefs.put('last_driver', driver_name)
        DRIVE_TIME_LIMIT_S = 45
    log.info(f'starting a drive with driver_name={driver_name}')

    pygame.init()
    window_size = [SX, SY]  # width and height
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Mountain biking")

    font = pygame.font.SysFont(None, 36) # font used for overlay text

    stars = np.empty(
        SY * LIGHT_SPEED) * np.nan  # locations by row of image (from top) of background 'stars' (to show movement through space), range -1 to 1
    blink = np.empty(
        SY * LIGHT_SPEED) * np.nan
    star_creation_prob = .25  # chance of having a star in each row of image
    trail = np.empty(SY) * np.nan  # locations of trail by row (from top) range -1 to 1

    FPS = 100

    clock = pygame.time.Clock()

    # make a controller
    controller = None
    try:
        controller = logitechG27_wheel.Controller(0)
    except Exception as e:
        log.error(f'cannot open steering wheel: {e}')

    trigger_device = None
    if USE_XID:
        log.info('configured to use Cedrus XID trigger box')
        try:
            # get a list of all attached XID devices
            devices = pyxid2.get_xid_devices()

            if devices:
                print(devices)
            else:
                log.error("No Cedrus XID trigger devices detected")

            trigger_device = devices[0]  # get the first device to use
            log.info("Using ", trigger_device)
        except Exception as e:
            log.error(f'cannot open EEG trigger device: {e}')

    cgx_serial = None
    if USE_CGX:
        log.info(f'using CGX dry electrode USB serial port on CGX_COM_PORT {CGX_COM_PORT}')
        try:
            cgx_serial = serial.Serial(CGX_COM_PORT, 1152003, timeout=5)
        except serial.serialutil.SerialException as e:
            log.error(f'will not be able to send steering errors on COM port: {e}')

    # trail CSV file
    trail_csvfile=None
    trail_reader=None
    
    trail_pos_current=0.
    trail_angle_current=0

    if not TRAIL_CSV_FILE_NAME is None:
        csv.register_dialect('skip-comments', skipinitialspace=True)
        trail_csvfile = open(TRAIL_CSV_FILE_NAME, 'r')
        trail_reader = csv.DictReader(filter(lambda row: row[0] != '#', trail_csvfile),
                                    dialect='skip-comments')  # https://stackoverflow.com/questions/14158868/python-skip-comment-lines-marked-with-in-csv-dictreader
        # row_iterator = reader.__iter__()
    else: # algorithmic trail
        np.random.seed(TRAIL_SEED)

    # data file
    data_file_name=os.path.join(output_path, driver_name + '_' + trial_name +'.csv')  # datetime.now().strftime('%Y-%m %d-%H-%M')
    data_file=open(data_file_name,'w')
    data_file.write('# Mountain biking error Telluride 2023\n')
    data_file.write('time(s),error,trail_pos\n')
    log.info(f'opened {data_file_name} for data')

    # game loop

    throttle01 = 0  # throttle 0-1 range
    brake01 = 0  # brake 0-1 range
    steering11 = 0  # steering angle -1 to 1
    steering11_inertia = 0
    reversed = 0
    jsInputs = None
    start_time=None
    running_score = 0
    driving=True
    # todo add sync rect to trigger trigger box with photodiode

    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    frame_counter = 0
    accumulated_err=0
    trigger_frame_counter = 0
    elapsed_time=0
    driving_started=False # set True when path crosses current time line

    if vlc and game_mode:
        get_ready_sound_player=vlc.MediaPlayer(GET_READY_TO_DRIVE_SOUND)
        get_ready_sound_player.play()


    while driving:
        frame_counter += 1
        time_now=()

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

        if not USE_MOUSE and not controller is None:
            # handle joysticks
            # jsButtons = controller.get_buttons()
            jsInputs = controller.get_axis()
            #
            steering11 = controller.get_steer()
            reversed = controller.get_reverse()
            # print(f'reversed={reversed}')
            throttle01 = controller.get_throttle()
            brake01 = controller.get_brake()

        if USE_MOUSE:
            mx,my=pygame.mouse.get_pos()
            steering11=(2.*(mx-sx2))/SX
            

        # msgX = bytes([126 + int(steerPos* 126)])
        # msgY = bytes([126 + int(throtPos* 126)])
        # msgZ = bytes([126 + int(breakPos* 126)])
        # sock.sendto(msgX + msgY + msgZ,("127.0.0.1", 5005))

        # read trail info
        try:
            current_row = next(trail_reader)
        except StopIteration:
            log.info(f'reached end of trail after {frame_counter} frames, rewinding')
            showed_trigger_flash = False
            trail[:] = np.nan
            frame_counter=0
            trail_csvfile.close()
            trail_csvfile = open(TRAIL_CSV_FILE_NAME, 'r')
            trail_reader = csv.DictReader(filter(lambda row: row[0] != '#', trail_csvfile),
                                          dialect='skip-comments')  # https://stackoverflow.com/questions/14158868/python-skip-comment-lines-marked-with-in-csv-dictreader
            current_row = next(trail_reader)
            done = True

        trail_time = float(current_row['time'])
        newest_trail_pos = float(current_row['trail_pos']) / 10  # range in file is -10 to +10, map to -1 to +1

        # update background stars
        stars[1:] = stars[0:-1]  # shift all the star rows down one
        blink[1:] = blink[0:-1]
        if np.random.uniform(0, 1) < star_creation_prob:
            stars[0] = np.random.uniform(-1, 1)  # make a new star with low probability
            blink[0] = np.random.uniform(-1, 1)
        else:
            stars[0] = np.nan
            blink[0] = np.nan

        trail[1:] = trail[0:-1]  # shift all the star rows down one
        trail[0] = newest_trail_pos  # show trail from top of image
        current_trail_pos = trail[st_y]  # the trail at the current timeline, target for user -1 to 1

        # drawing
        if frame_counter%SPEED!=0:
            continue

        # all rendering below here, no data updates
        screen.fill(BLACK)

        # draw stars
        # draw the stars
        for i in range(SY):
            if not np.isnan(stars[i]):
                l = stars[i] * SX - 2
                w = 5
                t = i
                h = 5
                r = pygame.Rect(l, t, w, h)
                #c = np.sin(np.sin(stars[i]*1235)+np.sin(time()))*128+128
                c = np.sin(blink[i])*128+128
                blink[i] = blink[i] + 0.1
                pygame.draw.rect(screen, (c, c, c*0.5), r)

        # draw line where we are
        pygame.draw.line(screen, BLUE, [0, st_y], [SX, st_y],
                         st_line_width)  # the base line where we are and where we show current steering line

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
        # print(f'error={err:.3f}')
        if not np.isnan(err): # measurement starts here, path has crossed line of driving
            if not driving_started:
                if vlc and game_mode:
                    driving_song_player: vlc.MediaPlayer = vlc.MediaPlayer(DRIVING_SONG)
                    log.debug(f'loaded song {DRIVING_SONG} and starting it')
                    driving_song_player.play()

            # error measurements start here
            SYNC_BOX_SIZE=50
            if trigger_frame_counter<100:  # detect first time that trail crosses current time line
                trigger_frame_counter += 1
                if start_time is None:
                    start_time=time() # only set start_time once
                pygame.draw.rect(screen, WHITE, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height
                if not TRIGGER_SOUND_FILE is None:
                    playsound(TRIGGER_SOUND_FILE)
            else:
                pygame.draw.rect(screen, BLACK, (SX - SYNC_BOX_SIZE, 0, SYNC_BOX_SIZE, SYNC_BOX_SIZE))  # rect is left top width height

            elapsed_time= time() - start_time
            data_file.write(f'{elapsed_time:.6f},{err:.4f},{current_trail_pos:.4f}\n')
            pygame.draw.line(screen, RED, [sx2 + current_trail_pos * sx2, st_y], [sx2 + steering11 * sx2, st_y],
                             width=st_line_width)
            if USE_XID and trigger_device is not None:
                pass  # todo write the error to EEG trigger device
                # trigger_device.enable_usb_output()
            if USE_CGX and cgx_serial is not None:
                quantized_err = int(err * 127)
                byte_err = quantized_err.to_bytes(length=1, byteorder='big', signed=True)
                # byte_err=np.int8(frame_counter)
                cgx_serial.write(byte_err)

            # accumulate total error
            accumulated_err+=np.abs(err)
            avg_err=accumulated_err/frame_counter
            running_score=1/avg_err
            driving_started=True


            # maybe terminate
            if elapsed_time>DRIVE_TIME_LIMIT_S or keys[pygame.K_ESCAPE] or keys[pygame.K_x]:
                driving=False
                if driving_song_player: driving_song_player.stop()
                log.info(f'Drive is done after {elapsed_time:.1f}s: Average absolute error: {avg_err:.2f}')
                with open(ACCUMULATED_RESULTS_FILENAME,'a') as results_file:
                    epoch_time=int(time())
                    results_file.write(f'{driver_name},{avg_err},{epoch_time}\n')
                d = pd.read_csv(ACCUMULATED_RESULTS_FILENAME, comment='#')
                drivers = d['driver']
                errors = d['error']
                epoch_times=d['epoch_time']
                i= np.argsort(errors)
                sorted_errors=errors[i]
                sorted_drivers=drivers[i]
                sorted_epoch_times=epoch_times[i]
                rank=np.searchsorted(sorted_errors.to_numpy(),avg_err,side='right')
                from easygui import textbox
                leaderboard_text='Rank\tDriver\tScore\tWhen\n'
                print('************************** Leaderboard *************************\nDriver\t\tAverage Error\tWhen')
                top10_counter=1
                for d,e,t in zip(sorted_drivers,sorted_errors,sorted_epoch_times):
                    datetime_obj = datetime.fromtimestamp(t)
                    when=datetime_obj.strftime('%Y-%m-%d %H:%M')
                    score=int(1/e) # score is 1/error cast to int
                    txt=f'{top10_counter}\t{d}\t{score:,}\t{when}'
                    print(txt)
                    leaderboard_text+=txt+'\n'
                    top10_counter+=1
                    if top10_counter>10:
                        break
                print('***************************************************************')
                txt=f'Your error of {avg_err:.3f} ranks you #{rank} of {len(sorted_errors)}'
                print(txt)
                leaderboard_text+='\n'+txt+'\n'
                print('***************************************************************')
                if game_mode:
                    ret=textbox(msg='Top 10 drives',title="Leaderboard",text=leaderboard_text)
                    if ret is None: # cancelled
                        done=True
                        playing_game=False
                        log.info('cancelled, quitting game')
                    else:
                        playing_game=True
                else:
                    playing_game=False


        # draw brake and throttle discs
        if reversed:
            color = RED
        else:
            color = GREEN
        brake_ball_rad = int(brake01 * 20 + 1)
        throttle_ball_rad = int(throttle01 * 20 + 1)
        pygame.draw.circle(screen, color, brake_pos, brake_ball_rad)
        pygame.draw.circle(screen, color, throttle_pos, throttle_ball_rad)

        # draw text
        time_left=DRIVE_TIME_LIMIT_S-elapsed_time
        img = font.render(f'Time left: {time_left:.1f}s score={running_score:.0f}', True, WHITE)
        screen.blit(img, (20, 20))

        # print(f'axes: {np.array2string(np.array(jsInputs),precision=2)} '
        #       f'\t\t\t steering: {steering01:.2f} throttle: {throttle01:.2f} brake: {brake01:.2f}'
        #       f' time:{time:.2f}s trail:{trail_pos:.2f}/10')

        # update screen
        pygame.display.flip()
        clock.tick(FPS)

# close window on quit
log.info('quitting pygame')
pygame.quit()
