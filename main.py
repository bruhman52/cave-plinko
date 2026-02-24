import pygame as pg
import pymunk as pm
import pymunk.pygame_util as pmu
import random as r
from config import *
from classes import Peg, Camera

# --- INITIALIZATION ---
pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT), FLAGS)
clock = pg.time.Clock()
draw_options = pmu.DrawOptions(screen)
pmu.positive_y_is_up = False
pg.display.set_caption("Cave Dive")
font = pg.font.SysFont("Arial", 36)

space = pm.Space()
space.gravity = GRAVITY

# --- ASSETS ---
player_surf = pg.image.load("testball.png").convert_alpha()
player_surf = pg.transform.scale(player_surf, (60, 60))
player_surf.set_colorkey(PURPLE_KEY)

peg_surf = pg.image.load("peg.png").convert_alpha()
peg_surf = pg.transform.scale(peg_surf, (40, 40))
peg_surf.set_colorkey(PURPLE_KEY)

# --- GROUPS & OBJECTS ---
all_pegs = pg.sprite.Group()
cam = Camera(WIDTH, HEIGHT)

# Player setup
moment = pm.moment_for_circle(PLAYER_MASS, 0, PLAYER_RADIUS)
player_body = pm.Body(PLAYER_MASS, moment)
player_shape = pm.Circle(player_body, PLAYER_RADIUS)
player_shape.elasticity = 0.85
player_shape.friction = 0.3
space.add(player_body, player_shape)

# State Variables
running = True
at_rest = True
debug_cam_toggle = False
horizontal_spacing = 250 
vertical_spacing = horizontal_spacing * 0.866 
last_generated_y_bottom = 200
last_generated_y_top = 200
rows_gen_bottom = 0
rows_gen_top = 0
bomb_timer = 10.0
depth = 0
top_depth = 0

def spawn_peg_row(y_pos, row_index, cols=15):
    grid_width = (cols - 1) * horizontal_spacing
    start_x = (WIDTH - grid_width) / 2
    for col in range(cols):
        x = start_x + (col * horizontal_spacing)
        if row_index % 2 == 1: x += horizontal_spacing / 2
        new_peg = Peg(space, x, y_pos, peg_surf)
        all_pegs.add(new_peg)

def reset():
    global last_generated_y_bottom, last_generated_y_top, rows_gen_bottom, rows_gen_top, at_rest
    player_body.position = (WIDTH / 2, -200)
    player_body.velocity = (0, 0)
    for peg in all_pegs:
        space.remove(peg.shape, peg.body)
        peg.kill()
    last_generated_y_bottom = last_generated_y_top = 200
    rows_gen_bottom = rows_gen_top = 0
    at_rest = True

# --- GAME LOOP ---
reset()
while running:
    dt = clock.tick(FPS) / 1000
    screen.fill("black")

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_1: debug_cam_toggle = not debug_cam_toggle
            if event.key == pg.K_r: reset()
            if event.key == pg.K_f: pg.display.toggle_fullscreen()
            if event.key == pg.K_ESCAPE: running = False

            if at_rest:
                if event.key == pg.K_a: player_body.velocity -= (50, 0)
                elif event.key == pg.K_d: player_body.velocity += (50, 0)

        if event.type == pg.MOUSEBUTTONDOWN and at_rest:
            if event.button == 1:  # Left click
                at_rest = False
                # Get mouse pos and convert to world space using camera
                mouse_pos = pg.mouse.get_pos()
                
                # Calculate direction from player to mouse
                # Note: We use cam.apply in reverse logic or just simple vector math
                p_pos = cam.apply(player_body.position)
                dx = mouse_pos[0] - p_pos[0]
                dy = mouse_pos[1] - p_pos[1]
                    
                # Set velocity based on the direction (scaled by a power factor)
                launch_power = 5.0
                player_body.velocity = (dx * launch_power, dy * launch_power)

        if event.type == pg.MOUSEWHEEL:
            cam.zoom = max(0.01, min(cam.zoom + event.y * 0.01, 2.0))

    # Physics & Camera Logic
    if at_rest:
            player_body.position = (WIDTH / 2, -200)
            player_body.velocity = (0, 0)
            player_body.angular_velocity = 0

    space.step(dt)

    depth = int(player_body.position.y)+200
    if depth > top_depth: top_depth = depth

    if abs(player_body.velocity.x) < 5 or abs(player_body.velocity.y) < 10:
        player_body.apply_impulse_at_local_point((r.randint(-10, 10), 0))

    if player_body.velocity.y > 3000: player_body.velocity = (player_body.velocity.x, 3000)

    keys = pg.key.get_pressed()
    speed = 500 * dt 

    if debug_cam_toggle:
        if keys[pg.K_w]: cam.y -= speed / cam.zoom
        if keys[pg.K_s]: cam.y += speed / cam.zoom
        if keys[pg.K_a]: cam.x -= speed / cam.zoom
        if keys[pg.K_d]: cam.x += speed / cam.zoom
    else:
        cam.x = WIDTH / 2
        cam.y = player_body.position.y

    # Bomb Timer Logic
    if not at_rest:
        bomb_timer -= dt
        if bomb_timer <= 0:
            bomb_timer = 10.0
            reset()

    # Generation and unrendering Logic
    if player_body.position.y > last_generated_y_bottom - 2000:
        for _ in range(5):
            spawn_peg_row(last_generated_y_bottom, rows_gen_bottom)
            last_generated_y_bottom += vertical_spacing
            rows_gen_bottom += 1

    for peg in all_pegs.sprites(): # .sprites() creates a temporary list to iterate over
        if abs(peg.body.position.y - player_body.position.y) > 4000:
            space.remove(peg.shape, peg.body)
            peg.kill()

    # Rendering
    draw_options.transform = cam.get_pm_transform()
    # space.debug_draw(draw_options) # Uncomment for physics wireframes
    if at_rest:
        p_pos = cam.apply(player_body.position)
        m_pos = pg.mouse.get_pos()
        pg.draw.line(screen, (0, 255, 0), p_pos, m_pos, 2) # Green line, 2px wide

    # Render Player
    view_pos = cam.apply(player_body.position)
    scaled_size = int(80 * cam.zoom)
    if scaled_size > 0:
        scaled_player = pg.transform.scale(player_surf, (scaled_size, scaled_size))
        screen.blit(scaled_player, (view_pos[0] - scaled_size // 2, view_pos[1] - scaled_size // 2))

    # Render Pegs
    for peg in all_pegs:
        v_pos = cam.apply(peg.body.position)
        sz = int(PEG_RADIUS * 2 * cam.zoom)
        peg.image = pg.transform.scale(peg.original_image, (sz, sz))
        peg.rect = peg.image.get_rect(center=v_pos)
    all_pegs.draw(screen)

    # Render Text
    score_surf = font.render(f"Depth: {depth}", True, (255, 255, 255))
    screen.blit(score_surf, (20, 20))
    top_score_surf = font.render(f"Record Depth: {top_depth}", True, (255, 255, 255))
    screen.blit(top_score_surf, (20, 60))
    timer_text = font.render(f"Time: {int(bomb_timer)}s", True, (255, 255, 0))
    screen.blit(timer_text, (WIDTH - 180, 20))

    pg.display.flip()

pg.quit()