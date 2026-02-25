import pygame as pg
import pymunk as pm
import pymunk.pygame_util as pmu
import random as r
import math as m
from config import *
from classes import *
from gamemanager import *

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

arrow_surf = pg.image.load("shootarrow.png").convert_alpha()
arrow_surf = pg.transform.scale(arrow_surf, (100, 100))
arrow_surf.set_colorkey(PURPLE_KEY)

peg_surf = pg.image.load("peg.png").convert_alpha()
peg_surf = pg.transform.scale(peg_surf, (40, 40))
peg_surf.set_colorkey(PURPLE_KEY)

# --- GROUPS & OBJECTS ---
all_pegs = pg.sprite.Group()
cam = Camera(WIDTH, HEIGHT)
gm = GameManager(space, all_pegs, peg_surf)

# Player setup
moment = pm.moment_for_circle(PLAYER_MASS, 0, PLAYER_RADIUS)
player_body = pm.Body(PLAYER_MASS, moment)
player_shape = pm.Circle(player_body, PLAYER_RADIUS)
player_shape.elasticity = 0.85
player_shape.friction = 0.3
space.add(player_body, player_shape)
player_shape.collision_type = 1

# State Variables
running = True
debug_cam_toggle = False
horizontal_spacing = 180 
vertical_spacing = horizontal_spacing * 0.866 
last_generated_y_bottom = 200
last_generated_y_top = 200
rows_gen_bottom = 0
rows_gen_top = 0
bomb_timer = 10.0
depth = 0
top_depth = 0
p_pos = [0,0]
current_state = GameState.AIMING
death_timer = 0.0
death_delay = 2.0
max_pull = 200 
purchased_width = 10
scaled_peg_cache = {}

# Register the handler
space.on_collision(1, 2, gm.hit_peg) # Player (1) hits Peg (2)

# --- GAME LOOP ---
gm.reset_to_aim()
while running:
    dt = clock.tick(FPS) / 1000
    screen.fill("grey")

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_1: debug_cam_toggle = not debug_cam_toggle
            if event.key == pg.K_r: gm.reset_to_aim()
            if event.key == pg.K_f: pg.display.toggle_fullscreen()
            if event.key == pg.K_ESCAPE: running = False

        if event.type == pg.MOUSEBUTTONDOWN and gm.state == "AIMING":
            if event.button == 1:
                mouse_pos = pg.mouse.get_pos()
                launch_vec = pg.math.Vector2(mouse_pos[0] - p_pos[0], mouse_pos[1] - p_pos[1])
                
                if launch_vec.length() > max_pull:
                    launch_vec.scale_to_length(max_pull)
                launch_multiplier = 5.0
                player_body.velocity = (launch_vec.x * launch_multiplier, launch_vec.y * launch_multiplier)
                gm.start_dive(player_body.position.y)

        if event.type == pg.MOUSEWHEEL:
            cam.zoom = max(0.01, min(cam.zoom + event.y * 0.01, 2.0))

    # Game State Logic
    grid_width = (purchased_width - 1) * horizontal_spacing
    half_width = grid_width / 2
    buffer = 100
    if gm.state == "AIMING":
        player_body.position = (WIDTH / 2, -200)
        player_body.velocity = (0, 0)
        if pg.mouse.get_pressed()[0]:
            gm.start_dive(player_body.position.y)

    elif gm.state == "DIVING":
        space.step(dt)
        gm.update_depth(player_body.position.y)

    elif gm.state == "DEAD":
        gm.death_timer -= dt
        if gm.death_timer <= 0:
            gm.reset_to_aim()
    
    p_pos = cam.apply(player_body.position)

    depth = int(player_body.position.y)+200
    if depth > top_depth: top_depth = depth

    if abs(player_body.velocity.x) < 5 or abs(player_body.velocity.y) < 10:
        player_body.apply_impulse_at_local_point((r.randint(-10, 10), 0))

    if player_body.velocity.y > 3000: player_body.velocity = (player_body.velocity.x, 3000)

    # Debug Camera Controls
    keys = pg.key.get_pressed()
    speed = 500 * dt 

    if debug_cam_toggle:
        if keys[pg.K_w]: cam.y -= speed / cam.zoom
        if keys[pg.K_s]: cam.y += speed / cam.zoom
        if keys[pg.K_a]: cam.x -= speed / cam.zoom
        if keys[pg.K_d]: cam.x += speed / cam.zoom

    else:
        cam.x = WIDTH / 2 + (player_body.position.x - WIDTH / 2) * 0.5
        cam.y = player_body.position.y

    for peg in all_pegs.sprites(): 
        if abs(peg.body.position.y - player_body.position.y) > 4000:
            space.remove(peg.shape, peg.body)
            peg.kill()

    # Rendering
    draw_options.transform = cam.get_pm_transform()
    # space.debug_draw(draw_options) # Uncomment for physics wireframes
    if gm.state == "AIMING":
        p_pos = cam.apply(player_body.position)
        m_pos = pg.mouse.get_pos()
        angle = m.degrees(m.atan2(-(m_pos[1] - p_pos[1]), m_pos[0] - p_pos[0])) 
        rotated_arrow = pg.transform.rotate(arrow_surf, angle)
        arrow_rect = rotated_arrow.get_rect(center=p_pos)
        offset = pg.math.Vector2(60, 0).rotate(-angle) 
        arrow_rect.center += offset
        screen.blit(rotated_arrow, arrow_rect)

    # Render Player
    view_pos = cam.apply(player_body.position)
    scaled_size = int(80 * cam.zoom)
    if scaled_size > 0:
        scaled_player = pg.transform.scale(player_surf, (scaled_size, scaled_size))
        rotated_player = pg.transform.rotate(scaled_player, -m.degrees(player_body.angle))
        rotated_rect = rotated_player.get_rect(center=view_pos)
        if gm.state != "DEAD": 
            screen.blit(rotated_player, rotated_rect)
            
    # Render Pegs
    sz = int(PEG_RADIUS * 2 * cam.zoom)
    if sz not in scaled_peg_cache:
        scaled_peg_cache[sz] = pg.transform.scale(peg_surf, (sz, sz))

    current_peg_img = scaled_peg_cache[sz]

    for peg in all_pegs:
        v_pos = cam.apply(peg.body.position)
        sz = int(PEG_RADIUS * 2 * cam.zoom)
        
        scaled_img = pg.transform.scale(peg.original_image, (sz, sz))
        
        new_alpha = int(255 * (peg.health / peg.max_health))
        scaled_img.set_alpha(new_alpha)
        
        peg.image = scaled_img
        peg.rect = peg.image.get_rect(center=v_pos)

    all_pegs.draw(screen)

    # Render Text
    score_surf = font.render(f"Depth: {gm.depth}", True, (255, 255, 255))
    screen.blit(score_surf, (20, 20))

    top_score_surf = font.render(f"Record Depth: {gm.top_depth}", True, (255, 255, 255))
    screen.blit(top_score_surf, (20, 60))

    if gm.state != "DEAD":
        timer_text = font.render(f"{gm.bomb_timer:.1f}", True, (255, 255, 0))
        if gm.bomb_timer < 3.0:
            timer_text = font.render(f"{gm.bomb_timer:.1f}", True, (255, 0, 0))
    else:
        timer_text = font.render(f"BOOM!! ({gm.death_timer:.1f})", True, (255, 255, 255))
    screen.blit(timer_text, (p_pos[0], p_pos[1] - 50))

    pg.display.flip()
    gm.update(dt, player_body, (purchased_width, horizontal_spacing, vertical_spacing))
    if gm.state == "RESTART_READY":
        gm.reset_to_aim()

pg.quit()