# mountain biking game simplified and written in pure python for Telluride 2023
# Tobi Delbruck
from get_logger import get_logger
log=get_logger()

import pygame
import logitechG27_wheel
import socket
import numpy as np
import csv
try:
    import pyxid2
except FileNotFoundError as e:
    log.error(f'cannot load driver DLL for USB serial port? {e}\n You may need to install drivers from https://ftdichip.com/drivers/d2xx-drivers/')

pygame.init()

# define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARKBLUE = (0, 0, 128)

# window settings
sx=800 # window width, 'size x'
sx2=int(sx/2) # half window width
sy=int(3*sx/4) # window height (size y)
st_y=int(3*sy/4) # y position of steering line from top
st_h= int(sy/10)# height of steering line
st_line_width=3 # width of steering stuff

br_th_y=int(sy * .9)  # from top, y starts with 0 at top of pygame display
br_th_x=int(sx * .2)
brake_pos = [br_th_x,br_th_y]
throttle_pos = [sx - br_th_x,br_th_y]

rows_per_frame=2 # how many rows to shift image per pygame tick

window_size = [sx, sy] # width and height
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Mountain biking")

font = pygame.font.SysFont(None, 36)

stars=np.empty(sy)*np.nan # locations by row of image (from top) of background 'stars' (to show movement through space), range -1 to 1
star_creation_prob=.1 # chance of having a star in each row of image
trail=np.empty(sy)*np.nan # locations of trail by row (from top) range -1 to 1


FPS = 100

clock = pygame.time.Clock()

# make a controller
controller=None
try:
    controller = logitechG27_wheel.Controller(0)
except Exception as e:
    log.error(f'cannot open steering wheel: {e}')

trigger_device=None
try:
    # get a list of all attached XID devices
    devices = pyxid2.get_xid_devices()

    if devices:
        print(devices)
    else:
        log.error("No Cedrus XID trigger devices detected")

    trigger_device = devices[0] # get the first device to use
    log.info("Using ", trigger_device)
except Exception as e:
    log.error(f'cannot open EEG trigger device: {e}')


# trail CSV file
csv.register_dialect('skip-comments', skipinitialspace=True)
csv_file_name='trail.csv'
csvfile = open(csv_file_name, 'r')
reader = csv.DictReader(filter(lambda row: row[0] != '#', csvfile),
                             dialect='skip-comments')  # https://stackoverflow.com/questions/14158868/python-skip-comment-lines-marked-with-in-csv-dictreader
# row_iterator = reader.__iter__()

# game loop
done = False

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while not done:
    throttle01 = 0 # throttle 0-1 range
    brake01 = 0 # brake 0-1 range
    steering11 = 0 # steering angle -1 to 1
    reversed=0
    jsInputs=None

    # event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done=True

    if not controller is None:
        # handle joysticks
        # jsButtons = controller.get_buttons()
        jsInputs = controller.get_axis()
        #
        steering11 = controller.get_steer()
        reversed=controller.get_reverse()
        # print(f'reversed={reversed}')
        throttle01 = controller.get_throttle()
        brake01 = controller.get_brake()


    # msgX = bytes([126 + int(steerPos* 126)])
    # msgY = bytes([126 + int(throtPos* 126)])
    # msgZ = bytes([126 + int(breakPos* 126)])
    # sock.sendto(msgX + msgY + msgZ,("127.0.0.1", 5005))

    # read trail info
    current_row =  next(reader)
    if current_row is None:
        reader = csv.DictReader(filter(lambda row: row[0] != '#', csvfile),
                                dialect='skip-comments')  # https://stackoverflow.com/questions/14158868/python-skip-comment-lines-marked-with-in-csv-dictreader
        current_row=next(reader)
    time=float(current_row['time'])
    newest_trail_pos= float(current_row['trail_pos']) / 10  # range in file is -10 to +10, map to -1 to +1

    # drawing
    screen.fill(BLACK)

    # draw stars
    stars[rows_per_frame:]=stars[0:-rows_per_frame] # shift all the star rows down one
    if np.random.uniform(0,1)<star_creation_prob:
        stars[0]=np.random.uniform(-1,1) # make a new star with low probability
    else:
        stars[0]=np.nan
    # draw the stars
    for i in range(sy):
        if not np.isnan(stars[i]):
            l=stars[i]*sx-2
            w=5
            t=i
            h=5
            r=pygame.Rect(l,t,w,h)
            pygame.draw.rect(screen, GRAY, r)


    # draw line where we are
    pygame.draw.line(screen, BLUE, [0, st_y], [sx, st_y],st_line_width) # the base line where we are and where we show current steering line

    # draw trail pixels
    trail[rows_per_frame:] = trail[0:-rows_per_frame]  # shift all the star rows down one
    trail[0]=newest_trail_pos # show trail from top of image
    # draw the trail
    for i in range(sy):
        if not np.isnan(trail[i]):
            l = (1+trail[i]) * sx2 - 2
            w = 5
            t = i
            h = 5
            r = pygame.Rect(l, t, w, h)
            pygame.draw.rect(screen, WHITE, r)

    current_trail_pos=trail[st_y] # the trail at the current timeline, target for user -1 to 1

    # draw steering wheeel position
    st_pos_px= sx2 + steering11 * sx2
    pygame.draw.line(screen, GREEN, [st_pos_px, st_y-st_h/2], [st_pos_px, st_y+st_h/2], st_line_width)

    err = (current_trail_pos - steering11)/2 # steering error, range -1 to 1, ideally zero
    # print(f'error={err:.3f}')
    if not np.isnan(current_trail_pos):
        pygame.draw.line(screen,RED,[sx2+current_trail_pos*sx2,st_y],[sx2+steering11*sx2,st_y],width=st_line_width)

    # draw brake and throttle discs
    if reversed:
        color=RED
    else:
        color=GREEN
    brake_ball_rad = int(brake01 * 20 + 1)
    throttle_ball_rad = int(throttle01 * 20 + 1)
    pygame.draw.circle(screen, color, brake_pos, brake_ball_rad)
    pygame.draw.circle(screen, color, throttle_pos, throttle_ball_rad)

    # draw text
    img = font.render(f't={time:.1f}s', True, WHITE)
    screen.blit(img, (20, 20))

    # print(f'axes: {np.array2string(np.array(jsInputs),precision=2)} '
    #       f'\t\t\t steering: {steering01:.2f} throttle: {throttle01:.2f} brake: {brake01:.2f}'
    #       f' time:{time:.2f}s trail:{trail_pos:.2f}/10')

    # update screen
    pygame.display.flip()
    clock.tick(FPS)

# close window on quit
pygame.quit ()

