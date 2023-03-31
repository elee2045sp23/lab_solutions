import pygame

clock = pygame.time.Clock()
pygame.init()
screen_width,screen_height = (800,600)
display = pygame.display.set_mode((screen_width,screen_height))

V = 5 # voltage
R = 2000 # resistance
C = .001 # capacitance
Q = 0 # charge

font = pygame.font.SysFont('timesnewroman',  30)
running = True
while running:
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False

    dt = clock.tick()/1000 # convert to seconds
    I = -Q/C/R # compute the current (charge per second, assuming discharging

    if pygame.key.get_pressed()[pygame.K_c]: # if c is pressed, charge
        I = (V - Q/C)/R # recompute the current, now that there is a voltage input (note, we could have just added V/R)
    Q += I*dt # this is the simulation part, where charge accumulates over time
    Vc = Q/C # New voltage across the capacitor
    s = font.render(f"Vc = {Vc:.2f}", False, "#FFFFFF","#000000")
    r = pygame.rect.Rect(300,screen_height-Vc*100,200,Vc*100) # compute the height of the voltage rectangle (starts at the bottom, screen_height and goes up)
    display.fill("#000000") # clear the screen
    display.blit(s,(20,20)) # display the voltage computed above
    pygame.draw.rect(display, "#FF0000", r) # draw the rectangle representing the voltage
    pygame.display.flip()

pygame.quit()