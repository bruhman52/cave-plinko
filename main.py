import pygame as pg
import pymunk as pm
import pymunk.pygame_util as pmu
import random as r
import math as m
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

arrow_surf = pg.image.load("shootarrow.png").convert_alpha()
arrow_surf = pg.transform.scale(arrow_surf, (100, 100))
arrow_surf.set_colorkey(PURPLE_KEY)

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
p_pos = [0,0]
is_dead = False
death_timer = 0.0
death_delay = 2.0
max_pull = 300 
purchased_width = 5

def spawn_peg_row(y_pos, row_index, cols=15):
    grid_width = (cols - 1) * horizontal_spacing
    start_x = (WIDTH - grid_width) / 2
    current_cols = cols - 1 if row_index % 2 == 1 else cols
    for col in range(current_cols):
        x = start_x + (col * horizontal_spacing)
        if row_index % 2 == 1: x += horizontal_spacing / 2
        new_peg = Peg(space, x, y_pos, peg_surf)
        all_pegs.add(new_peg)

def reset():
    global last_generated_y_bottom, last_generated_y_top, rows_gen_bottom, rows_gen_top, at_rest, bomb_timer, death_timer, is_dead, top_depth
    player_body.position = (WIDTH / 2, -200)
    player_body.velocity = (0, 0)
    bomb_timer = 10.0
    death_timer = death_delay
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
    screen.fill("grey")

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
            if event.button == 1:  
                at_rest = False
                mouse_pos = pg.mouse.get_pos()
                
                # Create a vector from player to mouse
                launch_vec = pg.math.Vector2(
                    mouse_pos[0] - p_pos[0], 
                    mouse_pos[1] - p_pos[1]
                )
                
                if launch_vec.length() > max_pull:
                    launch_vec.scale_to_length(max_pull)
                
                # Apply power
                launch_multiplier = 5.0
                player_body.velocity = (launch_vec.x * launch_multiplier, launch_vec.y * launch_multiplier)

        if event.type == pg.MOUSEWHEEL:
            cam.zoom = max(0.01, min(cam.zoom + event.y * 0.01, 2.0))

    # Physics & Camera Logic
    if at_rest:
            player_body.position = (WIDTH / 2, -200)
            player_body.velocity = (0, 0)
            player_body.angular_velocity = 0

    p_pos = cam.apply(player_body.position)

    if is_dead:
        print(death_timer)
        death_timer -= dt
        if death_timer <= 0:
            is_dead = False
            reset() 
    else:
        space.step(dt)

    depth = int(player_body.position.y)+200
    if depth > top_depth: top_depth = depth

    board_center = (WIDTH / 2, player_body.position.y)
    distance_from_center = player_body.position.get_distance(board_center)
    if distance_from_center > ((purchased_width-1)*horizontal_spacing)-100: is_dead = True

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
        cam.x = WIDTH / 2 + (player_body.position.x - WIDTH / 2) * 0.1
        cam.y = player_body.position.y

    # Bomb Timer Logic
    if not at_rest:
        bomb_timer -= dt
        if bomb_timer <= 0:
            is_dead = True

    # Generation and unrendering Logic
    if player_body.position.y > last_generated_y_bottom - 2000:
        for _ in range(5):
            spawn_peg_row(last_generated_y_bottom, rows_gen_bottom, purchased_width)
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
        # Negative dy because Pygame's Y axis is flipped
        angle = m.degrees(m.atan2(-(m_pos[1] - p_pos[1]), m_pos[0] - p_pos[0])) 
        # (Pygame rotates counter-clockwise, which matches atan2)
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
        if not is_dead: 
            screen.blit(rotated_player, rotated_rect)
            #screen.blit(scaled_player, (view_pos[0] - scaled_size // 2, view_pos[1] - scaled_size // 2))

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

    if not is_dead:
        timer_text = font.render(f"{bomb_timer:.1f}", True, (255, 255, 0))
        if bomb_timer < 3.0:
            timer_text = font.render(f"{bomb_timer:.1f}", True, (255, 0, 0))
    else:
        timer_text = font.render(f"BOOM!! ({death_timer:.1f})", True, (255, 255, 255))
    screen.blit(timer_text, (p_pos[0], p_pos[1] - 50))

    pg.display.flip()

pg.quit()