from classes import Peg
from config import *

class GameManager:
    def __init__(self, space, peg_group, peg_surf):
        self.state = "AIMING"
        self.space = space
        self.peg_group = peg_group
        self.peg_surf = peg_surf
        
        self.bomb_timer = 10.0
        self.death_timer = 2.0
        self.depth = 0
        self.top_depth = 0
        
        self.last_generated_y = 200
        self.rows_generated = 0
        self.row_count = 0

        self.grid_center_x = WIDTH / 2

    # --- YOUR STATE TRANSITION DEFINITIONS ---
    def start_dive(self, start_y):
        self.state = "DIVING"
        self.bomb_timer = 10.0
        self.start_y = start_y

    def trigger_death(self):
        self.state = "DEAD"
        self.death_timer = 2.0

    def reset_to_aim(self):
        self.state = "AIMING"
        self.depth = 0
        self.bomb_timer = 10.0
        self.last_generated_y = 200
        self.rows_generated = 0
        for peg in self.peg_group:
            self.space.remove(peg.shape, peg.body)
            peg.kill()

    # --- LOGIC FUNCTIONS ---
    def update_depth(self, current_y):
        self.depth = int((current_y - self.start_y)/100)
        if self.depth > self.top_depth:
            self.top_depth = self.depth

    def spawn_rows(self, player_y, purchased_width, vertical_spacing, horizontal_spacing):
        if player_y > self.last_generated_y - 2000:
            for i in range(5):
                grid_width = (purchased_width - 1) * horizontal_spacing
                start_x = (WIDTH - grid_width) / 2

                current_cols = purchased_width - 1 if self.rows_generated % 2 == 1 else purchased_width
                
                for col in range(current_cols):
                    x = start_x + (col * horizontal_spacing)
                    if self.rows_generated % 2 == 1: x += horizontal_spacing / 2
                    
                    new_peg = Peg(self.space, x, self.last_generated_y, self.peg_surf)
                    self.peg_group.add(new_peg)

                self.rows_generated += 1
                self.last_generated_y += vertical_spacing

    def update(self, dt, player_body, config_vars):
        p_width, h_spacing, v_spacing = config_vars

        self.spawn_rows(player_body.position.y, p_width, v_spacing, h_spacing)
        
        if self.state == "DIVING":
            self.bomb_timer -= dt
            self.update_depth(player_body.position.y)
            
            # Check for death conditions
            limit = (p_width - 1) * h_spacing / 2 + 150
            if self.bomb_timer <= 0 or abs(player_body.position.x - self.grid_center_x) > limit:
                self.trigger_death()

        elif self.state == "DEAD":
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.state = "RESTART_READY"

    def hit_peg(self, arbiter, space, data):
        peg_shape = arbiter.shapes[1]
        
        for peg in self.peg_group:
            if peg.shape == peg_shape:
                peg.health -= 1
                if peg.health <= 0:
                    self.space.add_post_step_callback(self.remove_peg_node, peg)
                else:
                    # Update transparency
                    new_alpha = int(255 * (peg.health / peg.max_health))
                    peg.image.set_alpha(new_alpha)
                break
        return True

    def remove_peg_node(self, space, peg):
        if peg in self.peg_group:
            self.space.remove(peg.shape, peg.body)
            peg.kill()