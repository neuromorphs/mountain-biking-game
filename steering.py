#  Copyright (c) 2019 Diego Damasceno
#
#  This file is part of pygame-logitechG29_wheel.
#  Documentation, related files, and licensing can be found at
#
#      <https://github.com/damascenodiego/pygame-logitechG29_wheel>.


import pygame
import logitechG27_wheel
import socket

pygame.init()

# define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# window settings
size = [400, 400]
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Steering")

FPS = 10

clock = pygame.time.Clock()

# make a controller
controller = logitechG27_wheel.Controller(0)


# game logic
steer_pos = [200, 100]
brake_pos = [100, 300]
throttle_pos = [300, 300]

# game loop
done = False

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while not done:
    # event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done=True

    # handle joysticks
    jsButtons = controller.get_buttons()
    jsInputs = controller.get_axis()

    steerPos = controller.get_steer()
    reversed=controller.get_reverse()
    # print(f'reversed={reversed}')


    throtPos = 0
    brakePos = 0
    clutchPos  = 0
    try:
        throtPos = controller.get_throttle()
    except IndexError as e:
        print(f'cannot get throttle: {e}')
    try:
        brakePos = controller.get_brake()
    except IndexError as e:
        print(f'cannot get brake: {e}')
    # msgX = bytes([126 + int(steerPos* 126)])
    # msgY = bytes([126 + int(throtPos* 126)])
    # msgZ = bytes([126 + int(breakPos* 126)])
    # sock.sendto(msgX + msgY + msgZ,("127.0.0.1", 5005))

    brake_ball_rad = int((brakePos + 1) * 20)
    throttle_ball_rad = int((throtPos + 1) * 20)

    if(steerPos >= 0):
        ball_color = RED
    else:
        ball_color = GREEN

    
    # drawing
    screen.fill(BLACK)
    pygame.draw.line(screen, BLUE, [steer_pos[0] -100, steer_pos[1]], [steer_pos[0] + 100, steer_pos[1]],3)
    pygame.draw.line(screen, GREEN, [steer_pos[0] + steerPos * 100, steer_pos[1]-50], [steer_pos[0] + steerPos * 100, steer_pos[1] + 50],3)

    if reversed:
        color=RED
    else:
        color=GREEN

    pygame.draw.circle(screen, color, brake_pos, brake_ball_rad)

    pygame.draw.circle(screen, color, throttle_pos, throttle_ball_rad)


    # update screen
    pygame.display.flip()


    clock.tick(FPS)

# close window on quit
pygame.quit ()
