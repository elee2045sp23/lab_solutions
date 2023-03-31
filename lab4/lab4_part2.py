import asyncio
import struct
import threading
import random
from dataclasses import dataclass

from bleak import BleakClient
import pygame
from pygame.math import Vector2,Vector3

# below are all of the types we'll use in the game
@dataclass # simple way to initialize data-only types (better than a dictionary)
class M5Input: # this will hold an M5 sticks sensor values
    acc: Vector3
    button: int
    battery: int
    connected: bool=False

@dataclass # this will hold relevant game input
class InputState:
    player_throttle: Vector2 = Vector2(0,0)
    held:bool = False # whether or not the fire button is held down
    held_time: float = 0.0 # how long the button has been held for
    fire:bool = False # a flag, set to to true on a frame the button is initially pressed

@dataclass
class GameObject: # every game object in this game will have position, velocity, and health
    pos:Vector2
    vel:Vector2
    health:float
    speed:float # speed, used to determine velocities

@dataclass
class Game: # this class holds everything relevant about our game
    player: GameObject
    enemies: list[GameObject]
    bullets: list[GameObject]
    input: InputState
    enemy_spawn_timer: float = 5
    life: int = 100
    score: int = 0
    time: float = 0


# this is mostly necessary pygame code
pygame.init()
screen_size = Vector2(1280,720)
screen = pygame.display.set_mode(screen_size,flags=pygame.SCALED,vsync=True) # screen is a "surface"
font = pygame.font.Font(None,30)
clock = pygame.time.Clock() # clock helps us with timing (not strictly necessary)
running = True

# these are our two relevant states (input and game)
m5 = M5Input(Vector3(0,0,0),0,0) # note, could have 2 of these! 

def new_game(): #we'll use this later to reset the game
    return Game(GameObject(Vector2(screen_size/2),Vector2(0,0),1,1200),[],[],InputState())

game = new_game()

# these are assets we'll use
laser_sound = pygame.mixer.Sound("laser.ogg")
ship = pygame.image.load("ship.png").convert() # note that convert is recommended, to ensure that the pixel format is good for the display

# this is a thread for async bluetooth, it will update m5
def run_controller(m5, address):
    # attempt a connection to the bluetooth device
    def callback(sender,data:bytearray):
        ax,ay,az,button,battery=struct.unpack("<fffbh",data)
        m5.acc = Vector3(ax,ay,az)
        m5.button = button
        m5.battery = battery
        m5.connected = True
    async def run():
        async with BleakClient(address) as client:
            await client.start_notify("5e8be540-13b8-49bf-af35-63b725c5c066",callback)
            while running:
                await asyncio.sleep(1)
    asyncio.run(run())
    m5.connected = False
t = threading.Thread(target=run_controller, args = (m5, "e8:9f:6d:00:a7:52")) # in theory, multiple m5 sticks would work
t.start() 

# This deals with setting flags based on the M5 state.  It also clears those flags.  
def update_input(dt):

    # some parts of our game want to know how long a button is held
    if game.input.held:
        game.input.held_time+=dt
    else:
        game.input.held_time=0

    fire_button = False

    if m5.connected:
        game.input.player_throttle = Vector2(-m5.acc.x,m5.acc.y) # maybe should go in input state, but okay
        fire_button = m5.button > 0
    else: # allow for keyboard
        pressed = pygame.key.get_pressed()
        horizontal = -pressed[pygame.K_a]/2 + pressed[pygame.K_d]/2
        vertical = -pressed[pygame.K_w]/2 + pressed[pygame.K_s]/2
        game.input.player_throttle = game.input.player_throttle*.9 + Vector2(horizontal,vertical)*.1 # apply some smoothing
        fire_button = pressed[pygame.K_SPACE]

    game.input.fire = False # fire is a flag, which is reset every frame

    # determine if the button was pressed or released
    if fire_button and not game.input.held:
        game.input.held = True # button was pressed
    elif not fire_button and game.input.held:
        game.input.held = False # button was released
        game.input.fire = True # fire on release

# this updates the player, making sure it stays in bounds
def update_player(dt):
    game.player.vel = game.input.player_throttle*game.player.speed
    game.player.pos += game.player.vel*dt

    # keeps the player in the bounds of the screen
    if game.player.pos.x < 0:
        game.player.pos.x = 0
    elif game.player.pos.y < 0:
        game.player.pos.y = 0
    elif game.player.pos.x > screen_size.x:
        game.player.pos.x = screen_size.x
    elif game.player.pos.y > screen_size.y:
        game.player.pos.y = screen_size.y

# this updates all of the bullets
def update_bullets(dt):
    if game.input.fire: # create a bullet
        fire_power = 200+game.input.held_time*600 # some magic numbers that works well, could put in a bullet subclass
        game.bullets.append(GameObject(Vector2(game.player.pos),Vector2(0,-1),fire_power,fire_power))
        volume = fire_power/800 # will be 1 if fire_power is 800 (held for 1s)
        laser_sound.set_volume(volume) # caps out at 1 (loudest)
        laser_sound.play() # even though sound is technically a visualization, you want it to play immediately
    
    # move bullets forward
    for b in game.bullets:
        dp = b.vel*b.speed*dt
        b.pos += dp

        # check for collisions 
        for e in game.enemies:
            if (b.pos-e.pos).magnitude() < 20:
                game.score+=1
                b.health = 0
                e.health = 0   
        # reduce the "health" by how far the bullet has travelled, which will eventually kill the bullet
        b.health-=dp.magnitude()

    # delete any bullets that are dead by keeping only those bullets that still have positive health
    game.bullets = [b for b in game.bullets if b.health>0] 

def update_enemies(dt):
    game.enemy_spawn_timer -= dt
    if game.enemy_spawn_timer < 0:
        game.enemy_spawn_timer = random.randint(1,2)
        game.enemies.append(GameObject(Vector2(random.randint(20,screen_size.x-20),0),Vector2(0,1),1,300))
    
    # move the enemies, and do collision checking with the base 
    for e in game.enemies:
        e.pos += e.vel*e.speed*dt
        if e.pos.y > screen_size.y: # the game life gets lost if they reach the bottom the screen
            game.life -= 5
            e.health = 0

    # same strategy as bullets above
    game.enemies = [e for e in game.enemies if e.health > 0] # keep enemies that have yet to reach the base and have life left

# main game loop.  We can be in one of three possible states
PAUSED,ACTIVE,OVER = range(3)
state = ACTIVE
while running:
    # handle pygame inputs 

    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False
        if evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_p:
                if state == PAUSED:
                    state = ACTIVE
                elif state == ACTIVE:
                    state = PAUSED
            if evt.key == pygame.K_r:
                game = new_game()
                state = ACTIVE
    
    # do all of the simulation 
    dt = clock.tick()/1000 # convert to s
    if state == ACTIVE:
        game.time += dt
        update_input(dt) 
        update_player(dt)
        update_bullets(dt)
        update_enemies(dt)
        if game.life <= 0:
            state = OVER

    # do all of the drawing
    screen.fill("#000000")

    screen.blit(ship,game.player.pos-Vector2(ship.get_rect().center))
    for b in game.bullets:
        pygame.draw.circle(screen,"#00FF00",b.pos,3)
    for e in game.enemies:
        pygame.draw.circle(screen,"#0000FF",e.pos,20)
            
    if state == ACTIVE:
        f = font.render(f"Life: {game.life} Score: {game.score} Time: {game.time:.2f} Batt: {m5.battery*1.1/1000:.2f}",False,"#FFFFFF","#000000")
    elif state == OVER:
        f = font.render(f"Life: {game.life} Score: {game.score} Time: {game.time:.2f} Batt: {m5.battery*1.1/1000:.2f} ... Hit R to reset.",False,"#FFFFFF","#000000")
    screen.blit(f,(0,0))
        
    pygame.display.flip()

pygame.quit()
t.join()