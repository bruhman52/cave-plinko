import pygame as pg
import pymunk as pm
import pymunk.pygame_util as pmu
import random as r

# pygame setup
pg.init()
screen = pg.display.set_mode((1280,720))
clock = pg.time.Clock()
running = True
pg.display.set_caption("My AWESOME SIGMA GAME")
draw_options = pmu.DrawOptions(screen)
pmu.positive_y_is_up = False

# pymunk setup
space = pm.Space()
space.gravity = (0, 981)

# load images
player_surf = pg.image.load("testball.png").convert_alpha()
player_surf = pg.transform.scale(player_surf, (60, 60))
player_surf.set_colorkey((255,0,255))

peg_surf = pg.image.load("peg.png").convert_alpha()
peg_surf = pg.transform.scale(peg_surf, (40, 40))
peg_surf.set_colorkey((255,0,255))

# player setup
at_rest = True
mass = 2
radius = 35
moment = pm.moment_for_circle(mass, 0, radius)
player_body = pm.Body(mass, moment)
player_body.position = (screen.get_width() / 2, 0)
player_shape = pm.Circle(player_body, radius)
player_shape.elasticity = 0.85  # Bounciness (0 to 1)
player_shape.friction = 0.3

space.add(player_body, player_shape)

# peg setup
peg_radius = 20

class Peg(pg.sprite.Sprite):
    def __init__(self, space,x, y):
        super().__init__()

        self.body = pm.Body(body_type=pm.Body.STATIC)
        self.body.position = (x, y)
        self.shape = pm.Circle(self.body, peg_radius)  
        self.shape.elasticity = 1.0
        self.shape.friction = 0.3
        space.add(self.body, self.shape)

        self.image = peg_surf
        self.original_image = self.image
        self.rect = self.image.get_rect(center=(x, y))

# populate pegs & add borders
all_pegs = pg.sprite.Group()
all_borders = []

horizontal_spacing = 250 
vertical_spacing = horizontal_spacing * 0.866 
last_generated_y_bottom = 200
last_generated_y_top = 200
rows_gen_bottom = 0
rows_gen_top = 0
grid_width = 0

def spawn_peg_row(y_pos, row_index, cols=15):
    grid_width = (cols - 1) * horizontal_spacing
    start_x = (screen.get_width() - grid_width) / 2

    for col in range(cols):
        x = start_x + (col * horizontal_spacing)

        if row_index % 2 == 1:
            x += horizontal_spacing / 2
        
        new_peg = Peg(space, x, y_pos)
        all_pegs.add(new_peg)

# reset function
def reset():
    global last_generated_y_bottom, last_generated_y_top, rows_gen_bottom, rows_gen_top
    player_body.position = (screen.get_width() / 2, -200) #also change in game loop
    player_body.velocity = (0, 0)

    for peg in all_pegs:
        space.remove(peg.shape, peg.body)
        peg.kill()

    last_generated_y_bottom = 200
    last_generated_y_top = 200
    rows_gen_bottom = 0
    rows_gen_top = 0
    global at_rest
    at_rest = True


# camera class
class Camera():
    def __init__(self,screen_width,screen_height):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.screen_width = screen_width
        self.screen_height = screen_height
    def apply(self, pos):
        x = (pos[0] - self.x) * self.zoom + self.screen_width / 2
        y = (pos[1] - self.y) * self.zoom + self.screen_height / 2
        return int(x), int(y)
    def get_pm_transform(self):
        return (pm.Transform.translation(self.screen_width / 2, self.screen_height / 2) @
                pm.Transform.scaling(self.zoom) @
                pm.Transform.translation(-self.x, -self.y))
    
cam = Camera(screen.get_width(), screen.get_height())
cam.zoom = 0.3
cam.x = screen.get_width() / 2
cam.y = screen.get_height() / 2
debug_cam_toggle = False

"""

GAME LOOP

"""

reset()

while running:
    # to exit (idk why this isnt already just a thing wtf guys)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_1:
                if debug_cam_toggle == False:
                    debug_cam_toggle = True
                else:
                    debug_cam_toggle = False
        if event.type == pg.MOUSEBUTTONDOWN and at_rest:
            if event.button == 1:  # Left click
                at_rest = False


        if event.type == pg.MOUSEWHEEL:
            cam.zoom += event.y * 0.01
            cam.zoom = max(0.01, min(cam.zoom, 2.0))
            print(f"Zoom: {cam.zoom:.2f}")
    # wipe screen
    screen.fill("black")

    draw_options.transform = cam.get_pm_transform()
    space.debug_draw(draw_options)

    if at_rest:
        player_body.position = (screen.get_width() / 2, -200) #also change reset() func
        player_body.velocity = (0, 0)

    dt = clock.tick(60) / 1000
    space.step(dt)

    #controls
    keys = pg.key.get_pressed()
    speed = 500 * dt 

    if debug_cam_toggle == True:
        if keys[pg.K_w]:
            cam.y -= speed / cam.zoom
        if keys[pg.K_s]:
            cam.y += speed / cam.zoom
        if keys[pg.K_a]:
            cam.x -= speed / cam.zoom
        if keys[pg.K_d]:
            cam.x += speed / cam.zoom
    else:
        cam.x = screen.get_width() / 2
        cam.y = player_body.position.y

    if keys[pg.K_r]:
        reset()

    # gen new pegs and delete old ones

    # gen down
    if player_body.position.y > last_generated_y_bottom - 2000:
        for _ in range(5):
            spawn_peg_row(last_generated_y_bottom, rows_gen_bottom)
            last_generated_y_bottom += vertical_spacing
            rows_gen_bottom += 1

    # gen up
    if player_body.position.y < last_generated_y_top + 2000 and last_generated_y_top > 200:
        for _ in range(5):
            rows_gen_top -= 1
            last_generated_y_top -= vertical_spacing
            spawn_peg_row(last_generated_y_top, rows_gen_top)

    # cleanup
    for peg in all_pegs:
        dist = peg.body.position.y - player_body.position.y
        if abs(dist) > 4000: 
            space.remove(peg.shape, peg.body)
            peg.kill()

    # render stuff
    view_pos = cam.apply(player_body.position)

    scaled_size = int(80 * cam.zoom)
    if scaled_size > 0:
        scaled_player_surf = pg.transform.scale(player_surf, (scaled_size, scaled_size))
        screen.blit(scaled_player_surf, (view_pos[0] - scaled_size // 2, view_pos[1] - scaled_size // 2))

    for peg in all_pegs:
        view_pos = cam.apply(peg.body.position)
        new_size = int(peg_radius * 2 * cam.zoom)
        peg.image = pg.transform.scale(peg.original_image, (new_size, new_size))
        peg.rect = peg.image.get_rect(center=view_pos)
        
    all_pegs.draw(screen)

    # tick player
    if abs(player_body.velocity.x) < 5 or abs(player_body.velocity.y) < 10:
        player_body.apply_impulse_at_local_point((r.randint(-10,10),0))

    # draw to screen
    pg.display.flip()

pg.quit()