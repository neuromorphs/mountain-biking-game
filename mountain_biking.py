# mountain biking game simplified and written in pure python for Telluride 2023
# Tobi Delbruck

import pygame
import logitechG27_wheel
import socket
import numpy as np

pygame.init()

# define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

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

window_size = [sx, sy] # width and height
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Mountain biking")

FPS = 30

clock = pygame.time.Clock()

# make a controller
controller = logitechG27_wheel.Controller(0)


# game loop
done = False

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while not done:
    throttle01 = 0
    brake01 = 0
    steering01 = 0

    # event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done=True

    # handle joysticks
    jsButtons = controller.get_buttons()
    jsInputs = controller.get_axis()

    steering01 = controller.get_steer()
    reversed=controller.get_reverse()
    # print(f'reversed={reversed}')


    try:
        throttle01 = controller.get_throttle()
    except IndexError as e:
        print(f'cannot get throttle: {e}')
    try:
        brake01 = controller.get_brake()
    except IndexError as e:
        print(f'cannot get brake: {e}')

    print(f'axes: {np.array2string(np.array(jsInputs),precision=2)} \t\t\t steering: {steering01:.2f} throttle: {throttle01:.2f} brake: {brake01:.2f}')
    # msgX = bytes([126 + int(steerPos* 126)])
    # msgY = bytes([126 + int(throtPos* 126)])
    # msgZ = bytes([126 + int(breakPos* 126)])
    # sock.sendto(msgX + msgY + msgZ,("127.0.0.1", 5005))


    
    # drawing
    screen.fill(BLACK)

    # draw line where we are
    pygame.draw.line(screen, BLUE, [0, st_y], [sx, st_y],st_line_width) # the base line where we are and where we show current steering line
    # and steering wheeel position
    st_pos_px=sx2+steering01*sx2
    pygame.draw.line(screen, GREEN, [st_pos_px, st_y-st_h/2], [st_pos_px, st_y+st_h/2], st_line_width)

    # draw brake and throttle discs
    if reversed:
        color=RED
    else:
        color=GREEN
    brake_ball_rad = int(brake01 * 20 + 1)
    throttle_ball_rad = int(throttle01 * 20 + 1)
    pygame.draw.circle(screen, color, brake_pos, brake_ball_rad)
    pygame.draw.circle(screen, color, throttle_pos, throttle_ball_rad)


    # update screen
    pygame.display.flip()


    clock.tick(FPS)

# close window on quit
pygame.quit ()
