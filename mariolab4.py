import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import time

ground_level = 100
pit_start_x = 200
pit_end_x = 280

window_width = 800
window_height = 640

# A simple 2D point class for handling positions
class Vector2D:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def set(self, x, y):
        self.x = x
        self.y = y

    def getX(self):
        return self.x

    def getY(self):
        return self.y

# Initialize Pygame and OpenGL settings
def initialize():
    pygame.init()
    pygame.display.set_mode((window_width, window_height), DOUBLEBUF | OPENGL)
    glClearColor(0.5, 0.7, 0.5, 1.0)  # Background color (green valley)
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)  # Set drawing color to white
    
    
    #drawing 2D using window width and height of coordinate system
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

# Mario class handles movement and state
class Character:
    def __init__(self, initial_position):
        self.position = Vector2D(initial_position[0], initial_position[1])
        self.current_state = 'IDLE'
        self.action = 'WAITING'
        self.sprite_sheet = {
            'IDLE': pygame.image.load("MarioStanding.bmp"),
            'RUN_STEP1': pygame.image.load("MarioRun1.bmp"),
            'RUN_STEP2': pygame.image.load("MarioRun2.bmp"),
            'RUN_STEP3': pygame.image.load("MarioRun3.bmp"),
            'LEAP': pygame.image.load("MarioJump.bmp"),
            'GAME_OVER': pygame.image.load('MarioDie.png')
        }
        self.sprite = self.sprite_sheet['IDLE']
        self.speed = 1
        self.jump_clock = 0
        self.in_jump = False
        self.falling = False
        self.death_notified = 0
        self.last_print_time = time.time()

    def draw(self):
        image_data = pygame.image.tostring(self.sprite, "RGBA", True)
        glRasterPos2f(self.position.getX(), self.position.getY())
        glDrawPixels(self.sprite.get_width(), self.sprite.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, image_data)

    def set_action(self, action):
        self.action = action
        if action == 'RUN':
            self.current_state = 'RUN_STEP1'
            self.sprite = self.sprite_sheet['RUN_STEP1']
        elif action == 'JUMP':
            self.current_state = 'LEAP'
            self.sprite = self.sprite_sheet['LEAP']
        elif action == 'WAITING':
            self.current_state = 'IDLE'
            self.sprite = self.sprite_sheet['IDLE']
        elif action == 'GAME_OVER':
            self.current_state = 'GAME_OVER'
            self.sprite = self.sprite_sheet['GAME_OVER']
            self.falling = True

    def switch_sprite(self):
        if self.current_state == 'GAME_OVER':
            return
        elif self.current_state == 'RUN_STEP1':
            self.sprite = self.sprite_sheet['RUN_STEP2']
            self.current_state = 'RUN_STEP2'
        elif self.current_state == 'RUN_STEP2':
            self.sprite = self.sprite_sheet['RUN_STEP3']
            self.current_state = 'RUN_STEP3'
        elif self.current_state == 'RUN_STEP3':
            self.sprite = self.sprite_sheet['RUN_STEP1']
            self.current_state = 'RUN_STEP1'

    def shift(self, dx, dy):
        self.position.set(self.position.getX() + dx, self.position.getY() + dy)

    def leap(self):
        if not self.in_jump:
            self.in_jump = True
            self.jump_clock = time.time()

    def handle_jump(self):
        if self.in_jump:
            time_in_air = time.time() - self.jump_clock
            if time_in_air < 0.25:
                self.position.set(self.position.getX(), self.position.getY() + 2)  # Rising
            elif time_in_air < 0.5:
                self.position.set(self.position.getX(), self.position.getY() - 2)  # Descending
            else:
                self.in_jump = False
                self.position.set(self.position.getX(), ground_level)  # Back to the valley ground

    def handle_fall(self):
        if self.falling:
            self.position.set(self.position.getX(), self.position.getY() - 1)  # Falling down
            if self.position.getY() <= -self.sprite.get_height():
                self.position.set(self.position.getX(), -self.sprite.get_height())  # Lock Mario off-screen
                for i in range(3):
                    print("Mario fell off the screen!")
                    time.sleep(10 / 3)
                self.falling = False

# Handle basic keyboard inputs
def keyboard_input(key, mario):
    if key == pygame.K_r and mario.current_state == 'GAME_OVER':
        mario.position.set(320, ground_level)
        mario.set_action('WAITING')
        mario.in_jump = False
        mario.jump_clock = 0
        print("Mario's position reset after falling.")

# Handle special keys like arrow keys
def handle_special_keypress(key, mario, movement_state):
    if key == pygame.K_LEFT:
        movement_state["left"] = True
        mario.set_action('RUN')
    elif key == pygame.K_RIGHT:
        movement_state["right"] = True
        mario.set_action('RUN')
    elif key == pygame.K_UP:
        mario.leap()
        mario.set_action('JUMP')

def handle_special_keyrelease(key, mario, movement_state):
    if key == pygame.K_LEFT:
        movement_state["left"] = False
    elif key == pygame.K_RIGHT:
        movement_state["right"] = False
    if not (movement_state["left"] or movement_state["right"]):
        mario.set_action('WAITING')

# Draw valley and pit
def draw_terrain():
    glColor3f(0.2, 0.7, 0.2)  # Valley
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(window_width, 0)
    glVertex2f(window_width, 100)
    glVertex2f(0, 100)
    glEnd()

    glColor3f(0.5, 0.3, 0.0)  # Pit
    glBegin(GL_QUADS)
    glVertex2f(pit_start_x, 0)
    glVertex2f(pit_end_x, 0)
    glVertex2f(pit_end_x, ground_level)
    glVertex2f(pit_start_x, ground_level)
    glEnd()

# Update the screen with Mario and the environment
def update_screen(mario):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw_terrain()

    if mario.current_state == 'GAME_OVER':
        mario.handle_fall()
    else:
        mario.handle_jump()

    mario.draw()
    glFlush()

# Check if Mario has fallen into the pit
def check_for_pit(mario):
    if pit_start_x < mario.position.getX() < pit_end_x and mario.position.getY() <= ground_level:
        mario.set_action("GAME_OVER")

# Main game loop
def game_loop():
    initialize()

    mario = Character((320, ground_level))  # Start at the middle

    running = True
    last_animation_time = time.time()
    movement_flags = {"left": False, "right": False}

    while running:
        current_time = time.time()
        if current_time - last_animation_time > 0.1:
            if mario.action == 'RUN':
                mario.switch_sprite()
            last_animation_time = current_time

        if mario.current_state != 'GAME_OVER':
            if movement_flags["left"]:
                mario.shift(-mario.speed, 0)
            if movement_flags["right"]:
                mario.shift(mario.speed, 0)

        update_screen(mario)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                keyboard_input(event.key, mario)
                handle_special_keypress(event.key, mario, movement_flags)
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.KEYUP:
                handle_special_keyrelease(event.key, mario, movement_flags)

        check_for_pit(mario)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    game_loop()
