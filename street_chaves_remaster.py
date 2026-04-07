"""
Street Chaves Remaster v7 - Pygame
Remaster do jogo Street Chaves v1.5A da Cybergamba (2003)
Compativel com qualquer controle USB/Bluetooth - configuravel no menu
"""
import pygame
import sys
import os
import random
import math
import json
import numpy as np

# ============================================================
# DEFAULT JOYSTICK / GAMEPAD MAPPINGS
# ============================================================
# Action names that can be mapped
JOY_ACTIONS = ["light_punch", "light_kick", "heavy_punch", "heavy_kick", "special"]

# Sensible default: first 5 buttons map to the 5 attack actions
DEFAULT_JOY_MAP_P1 = {
    "light_punch": 0,
    "light_kick": 1,
    "heavy_punch": 2,
    "heavy_kick": 3,
    "special": 4,
}
DEFAULT_JOY_MAP_P2 = {
    "light_punch": 0,
    "light_kick": 1,
    "heavy_punch": 2,
    "heavy_kick": 3,
    "special": 4,
}
JOY_AXIS_DEADZONE = 0.35

CONFIG_FILE = "street_chaves_config.json"

# ============================================================
# CONFIGURAÇÕES
# ============================================================
ORIGINAL_W, ORIGINAL_H = 400, 300
SCALE = 2
SCREEN_W = ORIGINAL_W * SCALE
SCREEN_H = ORIGINAL_H * SCALE
FPS = 60
BG_SCROLL_W = 600

# 4:3 resolution options for fullscreen
FULLSCREEN_RESOLUTIONS = [
    (800, 600),
    (1024, 768),
]

GRAVITY = 0.6
GROUND_Y = 230  # default, overridden per stage
WALK_SPEED = 2.5

# Per-stage ground Y in game coords (computed from bg floor detection)
STAGE_GROUND_Y = {
    0: 214, 1: 232, 2: 210, 3: 243, 4: 231, 5: 208,
    6: 208, 7: 235, 8: 243, 9: 235, 10: 240, 11: 237,
}
JUMP_FORCE = -11
PUSH_BACK = 4

FIGHTER_NAMES = [
    "CHAVES", "SEU MADRUGA", "CHIQUINHA", "QUICO", "DONA FLORINDA",
    "PROF. GIRAFALES", "SR. BARRIGA", "BRUXA DO 71", "PATY",
    "NHONHO", "GODINES", "SR. FURTADO", "JAIMINHO", "DONA NEVES", "GLORIA"
]

SND_HIT_LIGHT = [6, 8, 11, 33, 46, 48, 50, 56]
SND_HIT_HEAVY = [7, 9, 13, 25, 30, 31, 34, 52]
SND_BLOCK = [49, 53]
SND_KO = [1, 2, 3, 4, 5]
SND_SPECIAL = [12, 14, 15, 16, 17, 18]

DEFAULT_ANIMS = {
    "idle":         (0, 1, 8),
    "walk_fwd":     (2, 5, 6),
    "walk_back":    (2, 5, 6),
    "jump_up":      (6, 6, 1),
    "crouch":       (7, 7, 1),
    "light_punch":  (8, 10, 3),
    "heavy_punch":  (11, 14, 4),
    "light_kick":   (15, 17, 3),
    "heavy_kick":   (18, 21, 4),
    "special":      (22, 28, 3),
    "hit":          (29, 30, 5),
    "knockdown":    (31, 35, 4),
    "getup":        (36, 37, 6),
    "win":          (38, 41, 10),
    "block":        (7, 7, 1),
    "throw":        (42, 45, 4),
}

KEY_BINDINGS = {
    "up":           pygame.K_w,
    "down":         pygame.K_s,
    "left":         pygame.K_a,
    "right":        pygame.K_d,
    "light_punch":  pygame.K_h,
    "light_kick":   pygame.K_j,
    "heavy_punch":  pygame.K_k,
    "heavy_kick":   pygame.K_l,
    "special":      pygame.K_o,
}

KEY_BINDINGS_ALT = {
    "up":           pygame.K_UP,
    "down":         pygame.K_DOWN,
    "left":         pygame.K_LEFT,
    "right":        pygame.K_RIGHT,
}

# Player 2 key bindings
P2_KEY_BINDINGS = {
    "up":           pygame.K_UP,
    "down":         pygame.K_DOWN,
    "left":         pygame.K_LEFT,
    "right":        pygame.K_RIGHT,
    "light_punch":  pygame.K_KP1,
    "light_kick":   pygame.K_KP2,
    "heavy_punch":  pygame.K_KP4,
    "heavy_kick":   pygame.K_KP5,
    "special":      pygame.K_KP6,
}

# Difficulty settings for arcade mode (14 opponents)
TOWER_DIFFICULTY = [
    {"attack_rate": 0.4, "dmg_mult": 0.7, "name": "MUITO FACIL"},
    {"attack_rate": 0.5, "dmg_mult": 0.75, "name": "FACIL"},
    {"attack_rate": 0.6, "dmg_mult": 0.8, "name": "FACIL"},
    {"attack_rate": 0.65, "dmg_mult": 0.82, "name": "FACIL"},
    {"attack_rate": 0.7, "dmg_mult": 0.85, "name": "NORMAL"},
    {"attack_rate": 0.8, "dmg_mult": 0.9, "name": "NORMAL"},
    {"attack_rate": 0.85, "dmg_mult": 0.92, "name": "NORMAL"},
    {"attack_rate": 0.9, "dmg_mult": 0.95, "name": "NORMAL"},
    {"attack_rate": 1.0, "dmg_mult": 1.0, "name": "DIFICIL"},
    {"attack_rate": 1.1, "dmg_mult": 1.05, "name": "DIFICIL"},
    {"attack_rate": 1.3, "dmg_mult": 1.15, "name": "DIFICIL"},
    {"attack_rate": 1.5, "dmg_mult": 1.25, "name": "MUITO DIFICIL"},
    {"attack_rate": 1.7, "dmg_mult": 1.35, "name": "MUITO DIFICIL"},
    {"attack_rate": 2.0, "dmg_mult": 1.5, "name": "PESADELO"},
]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def load_sprite_strip(filepath):
    """Load a horizontal sprite strip, returning (frames, anchors).
    anchors[i] = x-offset from left edge of frame to body center (hip region)."""
    img = pygame.image.load(filepath).convert()
    w, h = img.get_size()
    pixels = pygame.surfarray.array3d(img)
    # Detect separator columns: columns where >= 95% of pixels are dark (brightness <= 50).
    # Some BMPs have near-black separators with 1-3 slightly bright pixels from compression.
    pixel_brightness = pixels.max(axis=2)  # max channel per pixel, shape (w, h)
    dark_pct = (pixel_brightness <= 50).mean(axis=1)  # fraction of dark pixels per column
    col_all_black = dark_pct >= 0.95
    separators = [x for x in range(w) if col_all_black[x]]
    frames = []
    anchors = []
    prev = 0
    boundaries = separators + ([w] if (not separators or separators[-1] != w - 1) else [])
    for sep in boundaries:
        fw = sep - prev
        if fw > 2:
            frame_surf = pygame.Surface((fw, h), pygame.SRCALPHA)
            temp = pygame.Surface((fw, h))
            temp.blit(img, (0, 0), (prev, 0, fw, h))
            temp_pixels = pygame.surfarray.array3d(temp)
            white_mask = (temp_pixels[:, :, 0] >= 248) & \
                         (temp_pixels[:, :, 1] >= 248) & \
                         (temp_pixels[:, :, 2] >= 248)
            frame_arr = pygame.surfarray.pixels3d(frame_surf)
            frame_arr[:] = temp_pixels
            del frame_arr
            alpha_arr = pygame.surfarray.pixels_alpha(frame_surf)
            alpha_arr[:] = 255
            alpha_arr[white_mask] = 0
            del alpha_arr
            frames.append(frame_surf)

            # Compute anchor: weighted center-of-mass of bottom third of body (numpy)
            visible = ~white_mask  # shape (fw, h), True where sprite pixel exists
            col_has_pixel = visible.any(axis=0)  # per-row: is there any visible pixel?
            vis_rows = np.where(col_has_pixel)[0]
            if len(vis_rows) > 0:
                bt = vis_rows[0]
                bb = vis_rows[-1]
                body_h = bb - bt
                hip_start = bb - max(15, body_h // 3)
                hip_region = visible[:, hip_start:bb + 1]  # (fw, hip_h)
                col_weights = hip_region.sum(axis=1).astype(float)  # per-x: count of visible pixels in hip
                total_weight = col_weights.sum()
                if total_weight > 0:
                    xs = np.arange(fw, dtype=float)
                    anchors.append(int((xs * col_weights).sum() / total_weight))
                else:
                    anchors.append(fw // 2)
            else:
                anchors.append(fw // 2)
        prev = sep + 1
    return frames, anchors


def scale_surface(surface, factor):
    w, h = surface.get_size()
    return pygame.transform.scale(surface, (int(w * factor), int(h * factor)))


def flip_frames(frames):
    return [pygame.transform.flip(f, True, False) for f in frames]


def make_transparent(img):
    result = img.convert_alpha()
    arr = pygame.surfarray.pixels3d(result)
    alpha = pygame.surfarray.pixels_alpha(result)
    white_mask = (arr[:, :, 0] >= 248) & (arr[:, :, 1] >= 248) & (arr[:, :, 2] >= 248)
    alpha[white_mask] = 0
    del arr, alpha
    return result


# ============================================================
# VISUAL EFFECTS
# ============================================================
class EffectSprite:
    """Animated effect using Efeitos sprites."""
    def __init__(self, x, y, frames, speed=3, scale_f=SCALE, follow_target=None):
        self.x = x
        self.y = y
        self.frames = frames
        self.speed = speed
        self.scale_f = scale_f
        self.idx = 0
        self.timer = 0
        self.follow_target = follow_target

    def update(self):
        if self.follow_target:
            self.x = self.follow_target.x
            self.y = self.follow_target.y - 40
        self.timer += 1
        if self.timer >= self.speed:
            self.timer = 0
            self.idx += 1
        return self.idx < len(self.frames)

    def draw(self, surface, camera_x):
        if self.idx >= len(self.frames):
            return
        frame = self.frames[self.idx]
        scaled = scale_surface(frame, self.scale_f)
        sw, sh = scaled.get_size()
        sx = (self.x - camera_x) * SCALE - sw // 2
        sy = self.y * SCALE - sh
        surface.blit(scaled, (sx, sy))


class HitSpark:
    def __init__(self, x, y, effects_list):
        self.x = x
        self.y = y
        self.timer = 12
        self.frame = 0
        self.effects = effects_list

    def update(self):
        self.timer -= 1
        self.frame += 1
        return self.timer > 0

    def draw(self, surface, camera_x):
        if self.effects and self.frame < len(self.effects):
            eff = self.effects[min(self.frame, len(self.effects) - 1)]
            scaled = scale_surface(eff, SCALE)
            sx = (self.x - camera_x) * SCALE - scaled.get_width() // 2
            sy = self.y * SCALE - scaled.get_height() // 2
            surface.blit(scaled, (sx, sy))


class DamageNumber:
    def __init__(self, x, y, damage, font):
        self.x = x
        self.y = y
        self.damage = damage
        self.font = font
        self.timer = 40
        self.vy = -1.5

    def update(self):
        self.y += self.vy
        self.vy += 0.03
        self.timer -= 1
        return self.timer > 0

    def draw(self, surface, camera_x):
        alpha = min(255, self.timer * 8)
        txt = self.font.render(str(self.damage), True, (255, 255, 0))
        txt.set_alpha(alpha)
        sx = (self.x - camera_x) * SCALE - txt.get_width() // 2
        sy = self.y * SCALE
        shadow = self.font.render(str(self.damage), True, (0, 0, 0))
        shadow.set_alpha(alpha)
        surface.blit(shadow, (sx + 2, sy + 2))
        surface.blit(txt, (sx, sy))


# ============================================================
# FIGHTER CLASS
# ============================================================
class Fighter:
    def __init__(self, fighter_id, x, y, facing_right=True, is_player=True):
        self.id = fighter_id
        self.name = FIGHTER_NAMES[fighter_id - 1]
        self.x = float(x)
        self.y = float(y)
        self.facing_right = facing_right
        self.is_player = is_player

        self.frames_right = []
        self.frames_left = []
        self.anchors_right = []  # Per-frame anchor X (body center)
        self.anchors_left = []
        self.ground_y = GROUND_Y  # Set by game per stage

        self.anims = dict(DEFAULT_ANIMS)
        self.current_anim = "idle"
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_playing = False

        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.crouching = False

        self.hp = 100
        self.max_hp = 100
        self.hp_display = 100.0
        self.special_meter = 0.0
        self.max_special = 100.0
        self.attacking = False
        self.attack_type = ""
        self.hit_stun = 0
        self.block_stun = 0
        self.blocking = False
        self.invincible = 0
        self.knockdown = False
        self.knockdown_timer = 0
        self.combo_hits = 0
        self.combo_damage = 0
        self.combo_timer = 0
        self.alive = True
        self.flash_timer = 0  # White flash on hit
        self.air_attack_done = False  # One air attack per jump

        self.attack_hitbox = None
        self.attack_damage = 0
        self.has_hit = False
        self.portraits = []

        # Input state
        self.inputs = {
            "left": False, "right": False, "up": False, "down": False,
            "light_punch": False, "heavy_punch": False,
            "light_kick": False, "heavy_kick": False,
            "special": False,
        }
        self.input_pressed = {k: False for k in self.inputs}

        # Input buffer for special detection
        self.input_buffer = {}

        self.score = 0
        self.first_attack = False
        self.attack_voice_pending = False

    def setup_frames(self, frames_right, anchors_right):
        self.frames_right = frames_right
        self.frames_left = flip_frames(frames_right)
        self.anchors_right = anchors_right
        # For flipped frames, anchor is mirrored
        self.anchors_left = [f.get_width() - a for f, a in zip(self.frames_right, anchors_right)] if anchors_right else []
        max_frame = len(self.frames_right) - 1
        adjusted = {}
        for anim_name, (start, end, speed) in self.anims.items():
            adjusted[anim_name] = (min(start, max_frame), min(end, max_frame), speed)
        self.anims = adjusted

    def set_anim(self, name, force=False):
        if name not in self.anims:
            return
        if name != self.current_anim or force:
            self.current_anim = name
            start, end, speed = self.anims[name]
            self.anim_frame = start
            self.anim_timer = 0
            one_shot = ("light_punch", "heavy_punch", "light_kick",
                        "heavy_kick", "hit", "knockdown", "special",
                        "win", "getup", "throw")
            self.anim_playing = name in one_shot

    def update_animation(self):
        if self.current_anim not in self.anims:
            return
        start, end, speed = self.anims[self.current_anim]
        self.anim_timer += 1
        if self.anim_timer >= speed:
            self.anim_timer = 0
            if self.anim_frame < end:
                self.anim_frame += 1
            elif self.anim_playing:
                self.anim_playing = False
                self.attacking = False
                self.attack_hitbox = None
                self.has_hit = False
                if self.current_anim == "getup":
                    self.invincible = 30
                if self.hp > 0 and not self.knockdown:
                    self.set_anim("idle")
            else:
                # Dead characters stay on last knockdown frame (no looping)
                if not self.alive:
                    self.anim_frame = end
                else:
                    self.anim_frame = start

    def update_input(self, opponent):
        if self.invincible > 0:
            self.invincible -= 1

        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_hits = 0
            self.combo_damage = 0

        # Input buffer management
        for k in list(self.input_buffer.keys()):
            self.input_buffer[k] -= 1
            if self.input_buffer[k] <= 0:
                del self.input_buffer[k]
        for k, v in self.input_pressed.items():
            if v:
                self.input_buffer[k] = 8  # 8 frame window

        # Knockdown recovery - frame-based timer
        if self.knockdown:
            if self.on_ground:
                self.knockdown_timer -= 1
            if self.knockdown_timer <= 0:
                self.knockdown = False
                if self.hp > 0:
                    self.set_anim("getup")
                    self.invincible = 20
            return

        if not self.alive:
            return

        if self.hit_stun > 0:
            self.hit_stun -= 1
            if self.hit_stun == 0:
                self.set_anim("idle")
            return

        if self.block_stun > 0:
            self.block_stun -= 1
            if self.block_stun == 0:
                self.blocking = False
                self.set_anim("idle")
            return

        # Auto face opponent
        if opponent and not self.attacking:
            if opponent.x > self.x + 10:
                self.facing_right = True
            elif opponent.x < self.x - 10:
                self.facing_right = False

        if self.attacking:
            return

        moving = False
        if self.on_ground:
            if self.inputs["down"]:
                self.crouching = True
                self.vx = 0
                self.set_anim("crouch")
            else:
                self.crouching = False

            if not self.crouching:
                if self.inputs["left"]:
                    self.vx = -WALK_SPEED
                    moving = True
                elif self.inputs["right"]:
                    self.vx = WALK_SPEED
                    moving = True
                else:
                    self.vx = 0

                if self.inputs["up"] and self.on_ground:
                    self.vy = JUMP_FORCE
                    self.on_ground = False
                    self.set_anim("jump_up")

        # Attacks - check special key (O key / dedicated button)
        has_special = self.input_pressed.get("special", False)

        # Air attacks (one per jump)
        if not self.on_ground and not self.air_attack_done and not self.attacking:
            if self.input_pressed.get("heavy_kick"):
                self.start_attack("heavy_kick", 14, 60)
                self.air_attack_done = True
            elif self.input_pressed.get("heavy_punch"):
                self.start_attack("heavy_punch", 12, 55)
                self.air_attack_done = True
            elif self.input_pressed.get("light_kick"):
                self.start_attack("light_kick", 7, 50)
                self.air_attack_done = True
            elif self.input_pressed.get("light_punch"):
                self.start_attack("light_punch", 6, 45)
                self.air_attack_done = True

        # Ground attacks
        if self.on_ground and has_special and self.special_meter >= 50:
            self.start_attack("special", 25, 70)
            self.special_meter -= 50
            self.input_buffer.clear()
        elif self.input_pressed.get("heavy_kick"):
            self.start_attack("heavy_kick", 12, 60)
        elif self.input_pressed.get("heavy_punch"):
            self.start_attack("heavy_punch", 10, 55)
        elif self.input_pressed.get("light_kick"):
            self.start_attack("light_kick", 6, 50)
        elif self.input_pressed.get("light_punch"):
            self.start_attack("light_punch", 5, 45)
        elif moving and self.on_ground and not self.attacking:
            if self.facing_right and self.inputs["left"]:
                self.set_anim("walk_back")
            elif not self.facing_right and self.inputs["right"]:
                self.set_anim("walk_back")
            else:
                self.set_anim("walk_fwd")
        elif not moving and self.on_ground and not self.attacking and not self.crouching:
            self.set_anim("idle")

        # Block
        if self.on_ground and not self.attacking:
            going_back = (self.facing_right and self.inputs["left"]) or \
                         (not self.facing_right and self.inputs["right"])
            self.blocking = going_back and self.inputs["down"]

    def start_attack(self, attack_type, damage, range_px):
        self.attacking = True
        self.attack_type = attack_type
        self.attack_damage = damage
        self.has_hit = False
        self.set_anim(attack_type)
        # Flag for voice call on attack start
        self.attack_voice_pending = True

    def update_physics(self):
        if not self.on_ground:
            self.vy += GRAVITY

        self.x += self.vx
        self.y += self.vy

        if self.y >= self.ground_y:
            self.y = self.ground_y
            self.vy = 0
            if not self.on_ground:
                self.on_ground = True
                self.air_attack_done = False
                if not self.attacking and not self.knockdown and self.hp > 0:
                    self.set_anim("idle")

        self.x = max(10, min(self.x, BG_SCROLL_W - 10))

        # Hitbox
        if self.attacking and self.attack_type in self.anims:
            start, end, _ = self.anims[self.attack_type]
            total_frames = end - start + 1
            active_start = start + max(1, total_frames // 4)
            if active_start <= self.anim_frame <= end:
                range_px = 65 if "heavy" in self.attack_type or self.attack_type == "special" else 50
                hx = 10 if self.facing_right else -range_px
                self.attack_hitbox = pygame.Rect(
                    self.x + hx, self.y - 85, range_px, 75
                )
            else:
                self.attack_hitbox = None

        if self.on_ground and (self.hit_stun > 0 or self.knockdown):
            self.vx *= 0.85

        diff = self.hp - self.hp_display
        self.hp_display += diff * 0.1

    def take_hit(self, damage, attacker):
        if self.invincible > 0:
            return False
        # Can't be hit while knocked down
        if self.knockdown:
            return False

        if self.blocking:
            chip = max(1, damage // 5)
            self.hp -= chip
            self.block_stun = 10
            push = -PUSH_BACK if self.facing_right else PUSH_BACK
            self.x += push * 2
            self.set_anim("block")
            return False

        self.hp -= damage
        self.flash_timer = 4  # White flash on hit
        self.special_meter = min(self.max_special, self.special_meter + damage * 0.8)
        if attacker:
            attacker.special_meter = min(attacker.max_special, attacker.special_meter + damage * 0.5)
            attacker.combo_hits += 1
            attacker.combo_damage += damage
            attacker.combo_timer = 90
            attacker.score += damage * 10

        self.attacking = False
        self.attack_hitbox = None

        push = -PUSH_BACK if self.facing_right else PUSH_BACK
        self.vx = push * 1.5

        if self.hp <= 0:
            self.hp = 0
            self.knockdown = True
            self.knockdown_timer = 90
            self.set_anim("knockdown")
            self.vy = -9
            self.on_ground = False
            self.alive = False
        elif damage >= 12 or (attacker and attacker.combo_hits >= 3):
            # Knockdown: heavy attacks or 3+ hit combos
            self.knockdown = True
            self.knockdown_timer = 45
            self.hit_stun = 0
            self.set_anim("knockdown")
            self.vy = -7 - damage * 0.12
            self.vx = push * 2.5
            self.on_ground = False
        else:
            self.hit_stun = 8 + damage // 3
            self.set_anim("hit")

        return True

    def get_body_rect(self):
        # Use idle frame width as body width reference
        if self.frames_right:
            idle_w = self.frames_right[0].get_width()
            bw = max(30, idle_w // 2)
        else:
            bw = 40
        bh = 100
        frame = self.get_current_frame()
        if frame:
            bh = frame.get_size()[1] - 10
        return pygame.Rect(self.x - bw // 2, self.y - bh, bw, bh)

    def get_current_frame(self):
        frames = self.frames_right if self.facing_right else self.frames_left
        if not frames:
            return None
        idx = max(0, min(self.anim_frame, len(frames) - 1))
        return frames[idx]

    def get_current_anchor(self):
        """Get the anchor X for the current frame."""
        idx = max(0, min(self.anim_frame, len(self.frames_right) - 1))
        if self.facing_right:
            if idx < len(self.anchors_right):
                return self.anchors_right[idx]
        else:
            if idx < len(self.anchors_left):
                return self.anchors_left[idx]
        # Fallback: frame center
        frame = self.get_current_frame()
        return frame.get_width() // 2 if frame else 20

    def draw(self, surface, camera_x):
        frame = self.get_current_frame()
        if frame is None:
            return

        if self.invincible > 0 and self.invincible % 4 < 2:
            return

        # Decrement flash timer
        if self.flash_timer > 0:
            self.flash_timer -= 1

        unscaled_w, unscaled_h = frame.get_size()
        scaled = scale_surface(frame, SCALE)
        fw, fh = scaled.get_size()

        # Per-frame anchor: the body center X in unscaled pixels
        anchor = self.get_current_anchor()
        draw_x = (self.x - camera_x) * SCALE - anchor * SCALE
        draw_y = self.y * SCALE - fh

        # White flash overlay when hit
        if self.flash_timer > 0:
            flash_surf = scaled.copy()
            white_overlay = pygame.Surface((fw, fh), pygame.SRCALPHA)
            white_overlay.fill((255, 255, 255, 180))
            flash_surf.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            # Blit original then overlay to get white tint effect
            surface.blit(scaled, (draw_x, draw_y))
            flash_layer = pygame.Surface((fw, fh), pygame.SRCALPHA)
            flash_layer.fill((255, 255, 255, 160))
            flash_layer.blit(scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surface.blit(flash_layer, (draw_x, draw_y))
        else:
            surface.blit(scaled, (draw_x, draw_y))

        # Shadow on ground - scales with jump height
        shadow_y = self.ground_y * SCALE
        idle_w = self.frames_right[0].get_width() if self.frames_right else 40
        height_above = max(0, self.ground_y - self.y)
        shadow_scale = max(0.3, 1.0 - height_above / 120.0)
        shadow_alpha = max(20, int(60 * shadow_scale))
        shadow_w = int(idle_w * SCALE * 0.6 * shadow_scale)
        shadow_h = max(4, int(8 * shadow_scale))
        shadow_surf = pygame.Surface((max(4, shadow_w), shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (0, 0, max(4, shadow_w), shadow_h))
        sx = (self.x - camera_x) * SCALE - shadow_w // 2
        surface.blit(shadow_surf, (sx, shadow_y))


# ============================================================
# GAME CLASS
# ============================================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Street Chaves - O Lutador da Vila (Remaster)")
        self.clock = pygame.time.Clock()
        self.fullscreen = False
        self.fs_resolution_idx = 0  # Index into FULLSCREEN_RESOLUTIONS

        self.base_path = os.path.dirname(os.path.abspath(__file__))

        # Joystick / gamepad system — supports any number of controllers
        self.joysticks = []        # list of pygame.joystick.Joystick objects
        self.joy_p1_idx = -1       # index into self.joysticks for P1 (-1 = none)
        self.joy_p2_idx = -1       # index into self.joysticks for P2
        self.joy_map_p1 = dict(DEFAULT_JOY_MAP_P1)
        self.joy_map_p2 = dict(DEFAULT_JOY_MAP_P2)
        self._refresh_joysticks()

        # Joystick config sub-screen state
        self._joy_config_active = False
        self._joy_config_player = 1       # 1 or 2
        self._joy_config_cursor = 0       # which row is selected
        self._joy_config_waiting = False  # waiting for button press
        self._joy_config_action = ""     # action being remapped

        # Volume
        self.vol_sfx = 0.5
        self.vol_music = 0.3
        self.vol_voice = 0.6

        self.state = "intro"
        self.backgrounds = []
        self.music_files = []
        self.sfx = {}
        self.voices = {}
        self.effects = []
        self.animations = []
        self.hit_sparks = []
        self.damage_numbers = []
        self.active_effects = []

        # Effect categories (indices into self.effects list, 0-based)
        self.eff_sparks = []      # Small hit sparks
        self.eff_impact = []      # Medium impact
        self.eff_fire = []        # Large fire/explosion for specials
        self.eff_knockdown = []   # Knockdown body effects

        self.intro_timer = 0
        self.title_option = 0
        self.options_cursor = 0
        self.options_items = ["VOL. MUSICA", "VOL. GOLPES/EFEITOS", "VOL. VOZES", "MODO TELA", "CONTROLE", "COMANDOS", "VOLTAR"]
        self.showing_controls = False

        # Jukebox state
        self._jukebox_cursor = 0
        self._jukebox_playing = -1

        self.p1_selection = 0
        self.p2_selection = 1
        self.p1_confirmed = False
        self.p2_confirmed = False

        self.player1 = None
        self.player2 = None
        self.round_num = 1
        self.p1_wins = 0
        self.p2_wins = 0
        self.timer = 99
        self.timer_tick = 0
        self.camera_x = 0
        self.round_state = "intro"
        self.round_timer = 0
        self.current_bg = 0
        self.current_ground_y = GROUND_Y
        self.fight_started = False
        self.ko_timer = 0
        self.total_score = 0
        self.first_hit_done = False

        # Fight feel systems
        self.hitstop = 0
        self.shake_timer = 0
        self.shake_intensity = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

        # CPU difficulty (for tower mode)
        self.cpu_attack_rate = 1.0
        self.cpu_dmg_mult = 1.0

        # Tower mode
        self.tower_opponents = []
        self.tower_level = 0
        self.tower_state = "display"  # display, prefight, fight, win, lose
        self.tower_timer = 0
        self.is_tower_mode = False
        self.is_2p_mode = False
        self.is_training = False

        # Cheat system (hidden)
        self._cheat_buffer = ""
        self._cheat_max_len = 12
        self.cheat_god_mode = False      # Infinite HP
        self.cheat_one_punch = False     # Max damage
        self.cheat_max_meter = False     # Always full special meter
        self._cheats_active_text = ""    # Temp display on activation
        self._cheats_active_timer = 0

        self.keys_just_pressed = set()

        self.load_assets()

    def load_assets(self):
        print("Carregando assets...")

        for i in range(1, 13):
            path = os.path.join(self.base_path, "Cenarios", f"Cenario-{i:02d}.bmp")
            if os.path.exists(path):
                bg = pygame.image.load(path).convert()
                self.backgrounds.append(bg)
        print(f"  {len(self.backgrounds)} cenarios")

        for i in range(1, 7):
            path = os.path.join(self.base_path, "Musicas", f"Musica-{i:02d}.wav")
            if os.path.exists(path):
                self.music_files.append(path)
        print(f"  {len(self.music_files)} musicas")

        for i in range(1, 68):
            path = os.path.join(self.base_path, "Sons", f"Som-{i:02d}.wav")
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(self.vol_sfx)
                    self.sfx[i] = snd
                except:
                    pass
        print(f"  {len(self.sfx)} sons")

        for i in range(1, 16):
            for suffix in ['a', 'b']:
                path = os.path.join(self.base_path, "Falas", f"Fala-{i:02d}-{suffix}.wav")
                if os.path.exists(path):
                    try:
                        snd = pygame.mixer.Sound(path)
                        snd.set_volume(self.vol_voice)
                        self.voices[(i, suffix)] = snd
                    except:
                        pass
        print(f"  {len(self.voices)} falas")

        # Load effects and categorize
        raw_effects = {}
        for i in range(1, 102):
            path = os.path.join(self.base_path, "Efeitos", f"Efeito-{i:03d}.bmp")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert()
                    raw_effects[i] = make_transparent(img)
                except:
                    pass
        # Store in list, keep mapping
        self.effects = []
        self.effect_map = {}  # original_id -> list_index
        for eid, surf in sorted(raw_effects.items()):
            self.effect_map[eid] = len(self.effects)
            self.effects.append(surf)

        # Categorize
        for eid in [5, 6, 7, 8, 9, 11, 12, 13, 19, 21]:
            if eid in self.effect_map:
                self.eff_sparks.append(self.effect_map[eid])
        for eid in [2, 3, 4, 14, 15, 16, 20, 28, 29, 30, 31, 32, 33, 34, 35, 36]:
            if eid in self.effect_map:
                self.eff_impact.append(self.effect_map[eid])
        for eid in [10, 17, 18, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101]:
            if eid in self.effect_map:
                self.eff_fire.append(self.effect_map[eid])
        for eid in [58, 59, 60, 61]:
            if eid in self.effect_map:
                self.eff_knockdown.append(self.effect_map[eid])

        print(f"  {len(self.effects)} efeitos (sparks:{len(self.eff_sparks)}, impact:{len(self.eff_impact)}, fire:{len(self.eff_fire)}, kd:{len(self.eff_knockdown)})")

        for i in range(1, 79):
            path = os.path.join(self.base_path, "Animacoes", f"Anim-{i:02d}.bmp")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert()
                    self.animations.append(make_transparent(img))
                except:
                    pass
        print(f"  {len(self.animations)} animacoes")

        self.portraits = {}
        for i in range(1, 16):
            portraits = []
            for suffix in ['a', 'b', 'c']:
                path = os.path.join(self.base_path, "Rostos", f"R{i:02d}-{suffix}.bmp")
                if os.path.exists(path):
                    img = pygame.image.load(path).convert()
                    portraits.append(make_transparent(img))
            if portraits:
                self.portraits[i] = portraits
        print(f"  {len(self.portraits)} retratos")

        self.fighter_frames = {}
        self.fighter_anchors = {}
        for i in range(1, 16):
            path = os.path.join(self.base_path, "Lutadores", f"C{i:02d}.bmp")
            if os.path.exists(path):
                frames, anchors = load_sprite_strip(path)
                self.fighter_frames[i] = frames
                self.fighter_anchors[i] = anchors
                print(f"  Lutador {i} ({FIGHTER_NAMES[i-1]}): {len(frames)} frames")

        self.font_big = pygame.font.Font(None, int(48 * SCALE / 2))
        self.font_medium = pygame.font.Font(None, int(32 * SCALE / 2))
        self.font_small = pygame.font.Font(None, int(20 * SCALE / 2))
        self.font_damage = pygame.font.Font(None, int(28 * SCALE / 2))
        self.font_combo = pygame.font.Font(None, int(36 * SCALE / 2))

        print("Assets carregados!")

    # ==========================================
    # VOLUME / SOUND
    # ==========================================
    def apply_volumes(self):
        pygame.mixer.music.set_volume(self.vol_music)
        for snd in self.sfx.values():
            snd.set_volume(self.vol_sfx)
        for snd in self.voices.values():
            snd.set_volume(self.vol_voice)

    def play_music(self, index):
        if 0 <= index < len(self.music_files):
            try:
                pygame.mixer.music.load(self.music_files[index])
                pygame.mixer.music.set_volume(self.vol_music)
                pygame.mixer.music.play(-1)
            except:
                pass

    def play_sfx(self, index):
        if index in self.sfx:
            self.sfx[index].play()

    def play_hit_sound(self, heavy=False):
        pool = SND_HIT_HEAVY if heavy else SND_HIT_LIGHT
        valid = [s for s in pool if s in self.sfx]
        if valid:
            self.sfx[random.choice(valid)].play()

    def play_block_sound(self):
        valid = [s for s in SND_BLOCK if s in self.sfx]
        if valid:
            self.sfx[random.choice(valid)].play()

    def play_ko_sound(self):
        valid = [s for s in SND_KO if s in self.sfx]
        if valid:
            self.sfx[random.choice(valid)].play()

    def play_special_sound(self):
        valid = [s for s in SND_SPECIAL if s in self.sfx]
        if valid:
            self.sfx[random.choice(valid)].play()

    def play_voice(self, fighter_id, variant='a'):
        key = (fighter_id, variant)
        if key in self.voices:
            self.voices[key].play()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._apply_display_mode()

    def cycle_display_mode(self, direction=1):
        """Cycle through: JANELA -> TELA CHEIA 800x600 -> TELA CHEIA 1024x768 -> ..."""
        # Mode 0 = windowed, mode 1..N = fullscreen at each FULLSCREEN_RESOLUTIONS index
        total = 1 + len(FULLSCREEN_RESOLUTIONS)
        if self.fullscreen:
            current = 1 + self.fs_resolution_idx
        else:
            current = 0
        current = (current + direction) % total
        if current == 0:
            self.fullscreen = False
        else:
            self.fullscreen = True
            self.fs_resolution_idx = current - 1
        self._apply_display_mode()

    def _apply_display_mode(self):
        """Apply the current display mode (windowed or fullscreen)."""
        try:
            if self.fullscreen:
                res = FULLSCREEN_RESOLUTIONS[self.fs_resolution_idx]
                self.screen = pygame.display.set_mode(res,
                                                       pygame.FULLSCREEN | pygame.SCALED)
            else:
                self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        except Exception:
            # Fallback to windowed if fullscreen fails
            self.fullscreen = False
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    def fade_out(self, duration=20):
        """Fade current screen to black."""
        snapshot = self.screen.copy()
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.fill((0, 0, 0))
        for i in range(duration):
            self.screen.blit(snapshot, (0, 0))
            alpha = int(255 * (i + 1) / duration)
            overlay.set_alpha(alpha)
            self.screen.blit(overlay, (0, 0))
            pygame.event.pump()
            pygame.display.flip()
            self.clock.tick(FPS)

    # ==========================================
    # JOYSTICK / GAMEPAD SYSTEM
    # ==========================================
    def _refresh_joysticks(self):
        """Re-detect all connected joysticks."""
        for j in self.joysticks:
            try:
                j.quit()
            except Exception:
                pass
        self.joysticks = []
        pygame.joystick.quit()
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            try:
                j = pygame.joystick.Joystick(i)
                j.init()
                self.joysticks.append(j)
            except Exception:
                pass
        # Auto-assign first joy to P1 if not assigned
        if self.joy_p1_idx < 0 and len(self.joysticks) > 0:
            self.joy_p1_idx = 0
        if self.joy_p2_idx < 0 and len(self.joysticks) > 1:
            self.joy_p2_idx = 1
        # Clamp indices
        if self.joy_p1_idx >= len(self.joysticks):
            self.joy_p1_idx = -1
        if self.joy_p2_idx >= len(self.joysticks):
            self.joy_p2_idx = -1
        self._load_joy_config()
        print(f"  {len(self.joysticks)} controle(s) detectado(s)")

    def _get_joy(self, player):
        """Return the Joystick object for a player, or None."""
        idx = self.joy_p1_idx if player == 1 else self.joy_p2_idx
        if 0 <= idx < len(self.joysticks):
            return self.joysticks[idx]
        return None

    def _joy_name(self, idx):
        if 0 <= idx < len(self.joysticks):
            return self.joysticks[idx].get_name()[:28]
        return "Nenhum"

    def _read_joy_input(self, joy, joy_map, inputs_dict, pressed_dict, just_pressed_set):
        """Read a joystick into the given dicts, merging with existing keyboard state."""
        if joy is None:
            return
        try:
            # Axes → directions
            ax0 = joy.get_axis(0)
            ax1 = joy.get_axis(1)
            if ax0 < -JOY_AXIS_DEADZONE:
                inputs_dict["left"] = True
            elif ax0 > JOY_AXIS_DEADZONE:
                inputs_dict["right"] = True
            if ax1 < -JOY_AXIS_DEADZONE:
                inputs_dict["up"] = True
            elif ax1 > JOY_AXIS_DEADZONE:
                inputs_dict["down"] = True
            # Hat → directions
            if joy.get_numhats() > 0:
                hat = joy.get_hat(0)
                if hat[0] < 0:
                    inputs_dict["left"] = True
                elif hat[0] > 0:
                    inputs_dict["right"] = True
                if hat[1] > 0:
                    inputs_dict["up"] = True
                elif hat[1] < 0:
                    inputs_dict["down"] = True
            # Buttons → actions
            nb = joy.get_numbuttons()
            for action, btn in joy_map.items():
                if 0 <= btn < nb and joy.get_button(btn):
                    inputs_dict[action] = True
                    # pressed detection: use joybuttondown events tracked per frame
                    if ("joy", btn) in just_pressed_set:
                        pressed_dict[action] = True
        except Exception:
            pass

    def _save_joy_config(self):
        """Persist joystick config to JSON alongside game."""
        cfg_path = os.path.join(self.base_path, CONFIG_FILE)
        data = {
            "joy_p1_idx": self.joy_p1_idx,
            "joy_p2_idx": self.joy_p2_idx,
            "joy_map_p1": self.joy_map_p1,
            "joy_map_p2": self.joy_map_p2,
            "vol_music": self.vol_music,
            "vol_sfx": self.vol_sfx,
            "vol_voice": self.vol_voice,
            "fs_resolution_idx": self.fs_resolution_idx,
        }
        try:
            with open(cfg_path, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_joy_config(self):
        """Load joystick config from JSON if exists."""
        cfg_path = os.path.join(self.base_path, CONFIG_FILE)
        if not os.path.exists(cfg_path):
            return
        try:
            with open(cfg_path, "r") as f:
                data = json.load(f)
            if "joy_p1_idx" in data:
                self.joy_p1_idx = int(data["joy_p1_idx"])
            if "joy_p2_idx" in data:
                self.joy_p2_idx = int(data["joy_p2_idx"])
            if "joy_map_p1" in data:
                self.joy_map_p1 = {k: int(v) for k, v in data["joy_map_p1"].items()}
            if "joy_map_p2" in data:
                self.joy_map_p2 = {k: int(v) for k, v in data["joy_map_p2"].items()}
            if "vol_music" in data:
                self.vol_music = float(data["vol_music"])
            if "vol_sfx" in data:
                self.vol_sfx = float(data["vol_sfx"])
            if "vol_voice" in data:
                self.vol_voice = float(data["vol_voice"])
            if "fs_resolution_idx" in data:
                self.fs_resolution_idx = int(data["fs_resolution_idx"])
            self.apply_volumes()
        except Exception:
            pass

    def create_fighter(self, fighter_id, x, y, facing_right=True, is_player=True):
        f = Fighter(fighter_id, x, y, facing_right, is_player)
        if fighter_id in self.fighter_frames:
            anchors = self.fighter_anchors.get(fighter_id, [])
            f.setup_frames(self.fighter_frames[fighter_id], anchors)
        if fighter_id in self.portraits:
            f.portraits = self.portraits[fighter_id]
        f.ground_y = self.current_ground_y
        return f

    # ==========================================
    # EFFECTS SPAWNING
    # ==========================================
    def spawn_hit_spark(self, x, y, heavy=False):
        pool = self.eff_impact if heavy else self.eff_sparks
        if pool:
            # Pick 3-4 random frames for the spark animation
            count = min(4, len(pool))
            indices = random.sample(pool, count) if len(pool) >= count else pool[:]
            frames = [self.effects[i] for i in indices]
            self.hit_sparks.append(HitSpark(x, y, frames))

    def spawn_knockdown_effect(self, x, y, target=None):
        if self.eff_knockdown:
            frames = [self.effects[i] for i in self.eff_knockdown]
            eff = EffectSprite(x, y, frames, speed=4, scale_f=SCALE)
            self.active_effects.append(eff)

    def spawn_special_effect(self, x, y, target=None):
        if self.eff_fire:
            # Use fire effects 85-101 range as animation sequence
            fire_indices = [i for i in self.eff_fire if i >= self.effect_map.get(85, 0)]
            if not fire_indices:
                fire_indices = self.eff_fire
            frames = [self.effects[i] for i in fire_indices[:12]]
            eff = EffectSprite(x, y - 20, frames, speed=2, scale_f=SCALE * 1.5,
                              follow_target=target)
            self.active_effects.append(eff)

    def spawn_damage_number(self, x, y, damage):
        self.damage_numbers.append(DamageNumber(x, y - 50, damage, self.font_damage))

    def draw_centered_text(self, text, y, font, color, shadow=None):
        txt = font.render(text, True, color)
        x = SCREEN_W // 2 - txt.get_width() // 2
        if shadow:
            sh = font.render(text, True, shadow)
            self.screen.blit(sh, (x + 2, y + 2))
        self.screen.blit(txt, (x, y))

    # ==========================================
    # INTRO
    # ==========================================
    def handle_intro(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    self.state = "title"
                    return True

        self.intro_timer += 1
        t = self.intro_timer

        self.screen.fill((0, 0, 0))

        if self.backgrounds:
            bg = self.backgrounds[min(1, len(self.backgrounds) - 1)]
            scaled_bg = pygame.transform.scale(bg, (SCREEN_W, SCREEN_H))
            self.screen.blit(scaled_bg, (0, 0))

        if self.animations:
            num_shown = min(len(self.animations), t // 8)
            for i in range(min(num_shown, 12)):
                angle = i * 0.8 + t * 0.02
                ax = SCREEN_W // 2 + int(math.sin(angle) * (SCREEN_W // 3))
                ay = int(SCREEN_H * 0.55 + math.sin(i * 1.5) * 30)
                if i < len(self.animations):
                    anim = self.animations[i]
                    scaled_a = scale_surface(anim, SCALE * 1.2)
                    self.screen.blit(scaled_a,
                                     (ax - scaled_a.get_width() // 2,
                                      ay - scaled_a.get_height() // 2))

        if t > 30:
            alpha = min(255, (t - 30) * 5)
            title_surf = self.font_big.render("STREET CHAVES", True, (255, 255, 0))
            title_surf.set_alpha(alpha)
            shadow = self.font_big.render("STREET CHAVES", True, (80, 0, 0))
            shadow.set_alpha(alpha)
            tx = SCREEN_W // 2 - title_surf.get_width() // 2
            ty = SCREEN_H // 6
            self.screen.blit(shadow, (tx + 3, ty + 3))
            self.screen.blit(title_surf, (tx, ty))

        if t > 60:
            alpha = min(255, (t - 60) * 4)
            sub = self.font_medium.render("O LUTADOR DA VILA", True, (255, 200, 100))
            sub.set_alpha(alpha)
            self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 6 + 55))

        if t > 120 and (t // 30) % 2:
            prompt = self.font_small.render("PRESSIONE ENTER", True, (255, 255, 255))
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, SCREEN_H - 70))

        if t == 1 and self.music_files:
            self.play_music(0)

        if t > 600:
            self.state = "title"

        return True

    # ==========================================
    # TITLE
    # ==========================================
    def handle_title(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                # Hidden cheat input - capture letter keys silently
                if event.unicode and event.unicode.isalpha():
                    self._cheat_buffer += event.unicode.lower()
                    if len(self._cheat_buffer) > self._cheat_max_len:
                        self._cheat_buffer = self._cheat_buffer[-self._cheat_max_len:]
                    self._check_cheats()

                if event.key in (pygame.K_UP, pygame.K_w):
                    self.title_option = (self.title_option - 1) % 5
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.title_option = (self.title_option + 1) % 5
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    if self.title_option == 0:
                        # MODO ARCADE - fight all opponents sequentially
                        self.is_tower_mode = True
                        self.is_2p_mode = False
                        self.is_training = False
                        self.state = "select"
                        self.p1_confirmed = False
                        self.p2_confirmed = False
                        if self.music_files:
                            self.play_music(0)
                    elif self.title_option == 1:
                        # VERSUS - 2 players, best of 3
                        self.is_tower_mode = False
                        self.is_2p_mode = True
                        self.is_training = False
                        self.cpu_attack_rate = 1.0
                        self.cpu_dmg_mult = 1.0
                        self.state = "select"
                        self.p1_confirmed = False
                        self.p2_confirmed = False
                        if self.music_files:
                            self.play_music(0)
                    elif self.title_option == 2:
                        # TREINO - training mode
                        self.is_tower_mode = False
                        self.is_2p_mode = False
                        self.is_training = True
                        self.cpu_attack_rate = 0.0
                        self.cpu_dmg_mult = 0.0
                        self.state = "select"
                        self.p1_confirmed = False
                        self.p2_confirmed = False
                        if self.music_files:
                            self.play_music(0)
                    elif self.title_option == 3:
                        self.state = "options"
                        self.options_cursor = 0
                        self.showing_controls = False
                    elif self.title_option == 4:
                        self.state = "jukebox"
                        self._jukebox_cursor = 0
                        self._jukebox_playing = -1
                elif event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_F11:
                    self.toggle_fullscreen()

        self.screen.fill((0, 0, 0))

        if self.backgrounds:
            bg = self.backgrounds[0]
            scaled_bg = pygame.transform.scale(bg, (SCREEN_W, SCREEN_H))
            self.screen.blit(scaled_bg, (0, 0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

        title = self.font_big.render("STREET CHAVES", True, (255, 255, 0))
        subtitle = self.font_medium.render("O LUTADOR DA VILA - REMASTER", True, (255, 200, 0))
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 6))
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, SCREEN_H // 6 + 55))

        menu_y = SCREEN_H // 2 - 30
        menu_items = ["MODO ARCADE", "VERSUS", "TREINO", "OPCOES", "MUSICAS"]
        for i, item in enumerate(menu_items):
            if i == self.title_option:
                color = (255, 255, 0)
                prefix = "> "
            else:
                color = (180, 180, 180)
                prefix = "  "
            txt = self.font_medium.render(prefix + item, True, color)
            self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, menu_y + i * 45))

        credit = self.font_small.render("Original por Cybergamba (2003) | Remaster em Pygame", True, (140, 140, 140))
        self.screen.blit(credit, (SCREEN_W // 2 - credit.get_width() // 2, SCREEN_H - 25))

        # Cheat activation flash (subtle, disappears quickly)
        if self._cheats_active_timer > 0:
            self._cheats_active_timer -= 1
            alpha = min(255, self._cheats_active_timer * 4)
            ct = self.font_small.render(self._cheats_active_text, True, (100, 255, 100))
            ct.set_alpha(alpha)
            self.screen.blit(ct, (SCREEN_W // 2 - ct.get_width() // 2, SCREEN_H - 50))

        return True

    # ==========================================
    # OPTIONS
    # ==========================================
    def handle_options(self):
        if self.showing_controls:
            return self.handle_controls_screen()
        if self._joy_config_active:
            return self._handle_joy_config()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._save_joy_config()
                    self.state = "title"
                    return True
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.options_cursor = (self.options_cursor - 1) % len(self.options_items)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.options_cursor = (self.options_cursor + 1) % len(self.options_items)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._adjust_option(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._adjust_option(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    if self.options_cursor == 3:
                        self.cycle_display_mode(1)
                    elif self.options_cursor == 4:
                        # Open joystick config sub-screen
                        self._joy_config_active = True
                        self._joy_config_player = 1
                        self._joy_config_cursor = 0
                        self._joy_config_waiting = False
                    elif self.options_cursor == 5:
                        self.showing_controls = True
                    elif self.options_cursor == 6:
                        self._save_joy_config()
                        self.state = "title"
                        return True

        self.screen.fill((15, 15, 50))
        self.draw_centered_text("OPCOES", 30, self.font_big, (255, 255, 0), shadow=(80, 50, 0))

        start_y = 120
        volumes = [self.vol_music, self.vol_sfx, self.vol_voice]

        for i, item_name in enumerate(self.options_items):
            y = start_y + i * 65
            is_selected = (i == self.options_cursor)
            color = (255, 255, 0) if is_selected else (180, 180, 180)
            prefix = "> " if is_selected else "  "

            txt = self.font_medium.render(prefix + item_name, True, color)
            self.screen.blit(txt, (60, y))

            if i < 3:
                bar_x = 60
                bar_y = y + 30
                bar_w = SCREEN_W - 120
                bar_h = 14
                vol = volumes[i]
                pygame.draw.rect(self.screen, (40, 40, 80), (bar_x, bar_y, bar_w, bar_h))
                fill_w = int(bar_w * vol)
                bar_color = (0, 200, 100) if is_selected else (0, 130, 70)
                pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill_w, bar_h))
                pygame.draw.rect(self.screen, (100, 100, 150), (bar_x, bar_y, bar_w, bar_h), 1)
                pct = self.font_small.render(f"{int(vol * 100)}%", True, (255, 255, 255))
                self.screen.blit(pct, (bar_x + bar_w + 8, bar_y - 1))
            elif i == 3:
                # Display mode option
                if self.fullscreen:
                    res = FULLSCREEN_RESOLUTIONS[self.fs_resolution_idx]
                    fs_label = f"< TELA CHEIA {res[0]}x{res[1]} >"
                    fs_color = (100, 255, 100)
                else:
                    fs_label = "< JANELA 800x600 >"
                    fs_color = (200, 200, 200)
                fs_txt = self.font_small.render(fs_label, True, fs_color)
                self.screen.blit(fs_txt, (80, y + 28))
                if is_selected:
                    hint_fs = self.font_small.render("ENTER ou A/D = Trocar modo", True, (150, 150, 200))
                    self.screen.blit(hint_fs, (80, y + 44))
            elif i == 4:
                # Joystick info
                n_joy = len(self.joysticks)
                joy_info = f"{n_joy} controle(s)"
                if n_joy > 0 and self.joy_p1_idx >= 0:
                    p1n = self._joy_name(self.joy_p1_idx)
                    joy_info += f"  |  P1: {p1n}"
                ji = self.font_small.render(joy_info, True, (200, 200, 200))
                self.screen.blit(ji, (80, y + 28))

        hint = self.font_small.render("A/D ou SETAS = Ajustar | W/S = Navegar | ESC = Voltar", True, (120, 120, 160))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 30))

        return True

    def _adjust_option(self, delta):
        if self.options_cursor == 0:
            self.vol_music = max(0.0, min(1.0, self.vol_music + delta * 0.1))
        elif self.options_cursor == 1:
            self.vol_sfx = max(0.0, min(1.0, self.vol_sfx + delta * 0.1))
        elif self.options_cursor == 2:
            self.vol_voice = max(0.0, min(1.0, self.vol_voice + delta * 0.1))
        elif self.options_cursor == 3:
            self.cycle_display_mode(delta)
        self.apply_volumes()

    def _check_cheats(self):
        """Check if any cheat code was typed in the buffer."""
        buf = self._cheat_buffer
        # "barril" = god mode (infinite HP) - reference to Chaves' barrel
        if buf.endswith("barril"):
            self.cheat_god_mode = not self.cheat_god_mode
            self._cheats_active_text = "..." if self.cheat_god_mode else ""
            self._cheats_active_timer = 60
            self._cheat_buffer = ""
        # "panela" = one punch KO (max force) - reference to Dona Florinda's pan
        elif buf.endswith("panela"):
            self.cheat_one_punch = not self.cheat_one_punch
            self._cheats_active_text = "..." if self.cheat_one_punch else ""
            self._cheats_active_timer = 60
            self._cheat_buffer = ""
        # "vila" = max special meter always full
        elif buf.endswith("vila"):
            self.cheat_max_meter = not self.cheat_max_meter
            self._cheats_active_text = "..." if self.cheat_max_meter else ""
            self._cheats_active_timer = 60
            self._cheat_buffer = ""

    # ==========================================
    # JOYSTICK CONFIGURATION SCREEN
    # ==========================================
    def _handle_joy_config(self):
        """Full-screen joystick/gamepad configuration."""
        ACTION_LABELS = {
            "light_punch": "Soco Fraco",
            "light_kick": "Chute Fraco",
            "heavy_punch": "Soco Forte",
            "heavy_kick": "Chute Forte",
            "special": "Especial",
        }
        player = self._joy_config_player
        joy_map = self.joy_map_p1 if player == 1 else self.joy_map_p2
        joy_idx_attr = "joy_p1_idx" if player == 1 else "joy_p2_idx"
        joy_idx = getattr(self, joy_idx_attr)

        # Build rows: [select joy, select player, then each action, then back]
        rows = ["CONTROLE", "JOGADOR"] + list(JOY_ACTIONS) + ["REDETECTAR", "VOLTAR"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self._joy_config_waiting:
                # Waiting for a joystick button press to assign
                if event.type == pygame.JOYBUTTONDOWN:
                    joy_map[self._joy_config_action] = event.button
                    if player == 1:
                        self.joy_map_p1 = joy_map
                    else:
                        self.joy_map_p2 = joy_map
                    self._joy_config_waiting = False
                    self._save_joy_config()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._joy_config_waiting = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._joy_config_active = False
                    self._save_joy_config()
                    return True
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._joy_config_cursor = (self._joy_config_cursor - 1) % len(rows)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._joy_config_cursor = (self._joy_config_cursor + 1) % len(rows)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    cur = rows[self._joy_config_cursor]
                    if cur == "CONTROLE":
                        new_idx = joy_idx - 1
                        if new_idx < -1:
                            new_idx = len(self.joysticks) - 1
                        setattr(self, joy_idx_attr, new_idx)
                    elif cur == "JOGADOR":
                        self._joy_config_player = 2 if player == 1 else 1
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    cur = rows[self._joy_config_cursor]
                    if cur == "CONTROLE":
                        new_idx = joy_idx + 1
                        if new_idx >= len(self.joysticks):
                            new_idx = -1
                        setattr(self, joy_idx_attr, new_idx)
                    elif cur == "JOGADOR":
                        self._joy_config_player = 2 if player == 1 else 1
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    cur = rows[self._joy_config_cursor]
                    if cur in JOY_ACTIONS:
                        self._joy_config_waiting = True
                        self._joy_config_action = cur
                    elif cur == "REDETECTAR":
                        self._refresh_joysticks()
                    elif cur == "VOLTAR":
                        self._joy_config_active = False
                        self._save_joy_config()
                        return True

        # Refresh references after potential changes
        player = self._joy_config_player
        joy_map = self.joy_map_p1 if player == 1 else self.joy_map_p2
        joy_idx = getattr(self, "joy_p1_idx" if player == 1 else "joy_p2_idx")

        # Draw
        self.screen.fill((15, 15, 50))
        self.draw_centered_text("CONFIGURAR CONTROLE", 20, self.font_big, (255, 255, 0), shadow=(80, 50, 0))

        sy = 80
        for ri, row_name in enumerate(rows):
            yy = sy + ri * 42
            is_sel = ri == self._joy_config_cursor
            color = (255, 255, 0) if is_sel else (180, 180, 180)
            prefix = "> " if is_sel else "  "

            if row_name == "CONTROLE":
                label = f"Controle: {self._joy_name(joy_idx)}"
                txt = self.font_medium.render(prefix + label, True, color)
                self.screen.blit(txt, (40, yy))
                if is_sel:
                    h = self.font_small.render("A/D = Trocar controle", True, (150, 150, 200))
                    self.screen.blit(h, (60, yy + 24))
            elif row_name == "JOGADOR":
                label = f"Jogador: P{player}"
                txt = self.font_medium.render(prefix + label, True, color)
                self.screen.blit(txt, (40, yy))
                if is_sel:
                    h = self.font_small.render("A/D = Trocar jogador", True, (150, 150, 200))
                    self.screen.blit(h, (60, yy + 24))
            elif row_name in JOY_ACTIONS:
                act_label = ACTION_LABELS.get(row_name, row_name)
                btn = joy_map.get(row_name, -1)
                btn_label = f"Botao {btn}" if btn >= 0 else "--"
                txt = self.font_medium.render(f"{prefix}{act_label}", True, color)
                val = self.font_medium.render(btn_label, True, (100, 255, 100) if not is_sel else (255, 255, 0))
                self.screen.blit(txt, (40, yy))
                self.screen.blit(val, (SCREEN_W - val.get_width() - 40, yy))
            elif row_name == "REDETECTAR":
                txt = self.font_medium.render(prefix + "Redetectar Controles", True, color)
                self.screen.blit(txt, (40, yy))
            elif row_name == "VOLTAR":
                txt = self.font_medium.render(prefix + "Voltar", True, color)
                self.screen.blit(txt, (40, yy))

        # Waiting overlay
        if self._joy_config_waiting:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            act_label = ACTION_LABELS.get(self._joy_config_action, self._joy_config_action)
            self.draw_centered_text(f"Aperte um botao no controle para:", SCREEN_H // 2 - 30,
                                     self.font_medium, (255, 255, 255))
            self.draw_centered_text(act_label, SCREEN_H // 2 + 10,
                                     self.font_big, (255, 255, 0), shadow=(80, 50, 0))
            self.draw_centered_text("ESC = Cancelar", SCREEN_H // 2 + 60,
                                     self.font_small, (200, 200, 200))

        return True

    # ==========================================
    # CONTROLS SCREEN
    # ==========================================
    def handle_controls_screen(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                self.showing_controls = False
                return True

        self.screen.fill((15, 15, 50))
        self.draw_centered_text("COMANDOS", 20, self.font_big, (255, 255, 0), shadow=(80, 50, 0))

        controls = [
            ("JOGADOR 1", ""),
            ("Andar", "W A S D"),
            ("Soco Fraco", "H"),
            ("Chute Fraco", "J"),
            ("Soco Forte", "K"),
            ("Chute Forte", "L"),
            ("Especial", "O  (barra 50%+)"),
            ("Defesa", "TRAS + S"),
            ("", ""),
            ("JOGADOR 2", ""),
            ("Andar", "SETAS"),
            ("Soco Fraco", "NUM 1"),
            ("Chute Fraco", "NUM 2"),
            ("Soco Forte", "NUM 4"),
            ("Chute Forte", "NUM 5"),
            ("Especial", "NUM 6  (barra 50%+)"),
            ("", ""),
            ("SISTEMA", ""),
            ("Pausa", "P"),
            ("Tela Cheia", "F11"),
        ]

        y = 80
        for label, key in controls:
            if label == "" and key == "":
                y += 8
                continue
            if key == "":
                txt = self.font_medium.render(label, True, (255, 200, 0))
                self.screen.blit(txt, (60, y))
                y += 30
            else:
                lbl = self.font_small.render(label, True, (200, 200, 200))
                val = self.font_small.render(key, True, (100, 255, 100))
                self.screen.blit(lbl, (80, y))
                self.screen.blit(val, (SCREEN_W - val.get_width() - 60, y))
                y += 22

        hint = self.font_small.render("Pressione qualquer tecla para voltar", True, (120, 120, 160))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 25))

        return True

    # ==========================================
    # JUKEBOX - MUSIC PLAYER
    # ==========================================
    def handle_jukebox(self):
        n_tracks = len(self.music_files)
        if n_tracks == 0:
            self.state = "title"
            return True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    self._jukebox_playing = -1
                    self.state = "title"
                    return True
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._jukebox_cursor = (self._jukebox_cursor - 1) % n_tracks
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._jukebox_cursor = (self._jukebox_cursor + 1) % n_tracks
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    self.play_music(self._jukebox_cursor)
                    self._jukebox_playing = self._jukebox_cursor
                elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    pygame.mixer.music.stop()
                    self._jukebox_playing = -1

        # Check if music ended naturally
        if self._jukebox_playing >= 0 and not pygame.mixer.music.get_busy():
            # Auto-advance to next track
            self._jukebox_playing = (self._jukebox_playing + 1) % n_tracks
            self.play_music(self._jukebox_playing)
            self._jukebox_cursor = self._jukebox_playing

        # Draw
        self.screen.fill((15, 15, 50))
        self.draw_centered_text("MUSICAS", 20, self.font_big, (255, 255, 0), shadow=(80, 50, 0))

        # Scrollable list
        visible = 8
        start_idx = max(0, self._jukebox_cursor - visible // 2)
        if start_idx + visible > n_tracks:
            start_idx = max(0, n_tracks - visible)

        sy = 90
        for vi in range(visible):
            idx = start_idx + vi
            if idx >= n_tracks:
                break
            yy = sy + vi * 52
            is_sel = (idx == self._jukebox_cursor)
            is_playing = (idx == self._jukebox_playing)
            if is_playing and is_sel:
                color = (100, 255, 100)
            elif is_sel:
                color = (255, 255, 0)
            elif is_playing:
                color = (100, 200, 100)
            else:
                color = (180, 180, 180)

            prefix = ""
            if is_sel:
                prefix = "> "
            if is_playing:
                prefix = ">> " if is_sel else "  * "
            elif not is_sel:
                prefix = "  "

            track_name = os.path.basename(self.music_files[idx])
            track_name = os.path.splitext(track_name)[0]
            label = f"{prefix}{idx + 1:02d}. {track_name}"
            txt = self.font_medium.render(label, True, color)
            self.screen.blit(txt, (60, yy))

            # Playing indicator bar
            if is_playing:
                bar_y = yy + 28
                bar_w = SCREEN_W - 120
                pygame.draw.rect(self.screen, (40, 80, 40), (60, bar_y, bar_w, 6))
                # Animated position indicator
                t = pygame.time.get_ticks() % 3000
                pos = int(bar_w * t / 3000)
                pygame.draw.rect(self.screen, (100, 255, 100), (60, bar_y, pos, 6))

        # Status bar at bottom
        if self._jukebox_playing >= 0:
            playing_name = os.path.splitext(os.path.basename(self.music_files[self._jukebox_playing]))[0]
            status = f"Tocando: {playing_name}"
            st = self.font_small.render(status, True, (100, 255, 100))
            self.screen.blit(st, (SCREEN_W // 2 - st.get_width() // 2, SCREEN_H - 55))

        hint = self.font_small.render("ENTER = Tocar | BACKSPACE = Parar | ESC = Voltar", True, (120, 120, 160))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 25))

        return True

    # ==========================================
    # SELECT
    # ==========================================
    def handle_select(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "title"
                    pygame.mixer.music.stop()
                    return True

                if not self.p1_confirmed:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.p1_selection = (self.p1_selection - 1) % 15
                        self.play_sfx(random.choice([s for s in [46, 48] if s in self.sfx] or [46]))
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.p1_selection = (self.p1_selection + 1) % 15
                        self.play_sfx(random.choice([s for s in [46, 48] if s in self.sfx] or [46]))
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.p1_selection = (self.p1_selection - 5) % 15
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.p1_selection = (self.p1_selection + 5) % 15
                    elif event.key in (pygame.K_h, pygame.K_RETURN, pygame.K_SPACE):
                        self.p1_confirmed = True
                        self.play_voice(self.p1_selection + 1, 'a')
                        if self.is_tower_mode:
                            self.start_tower()
                            return True
                        elif self.is_training:
                            others = [i for i in range(15) if i != self.p1_selection]
                            self.p2_selection = random.SystemRandom().choice(others)
                            self.p2_confirmed = True
                        elif not self.is_2p_mode:
                            others = [i for i in range(15) if i != self.p1_selection]
                            self.p2_selection = random.SystemRandom().choice(others)
                            self.p2_confirmed = True

                # P2 selection in 2-player mode
                if self.is_2p_mode and self.p1_confirmed and not self.p2_confirmed:
                    if event.key == pygame.K_LEFT:
                        self.p2_selection = (self.p2_selection - 1) % 15
                        self.play_sfx(random.choice([s for s in [46, 48] if s in self.sfx] or [46]))
                    elif event.key == pygame.K_RIGHT:
                        self.p2_selection = (self.p2_selection + 1) % 15
                        self.play_sfx(random.choice([s for s in [46, 48] if s in self.sfx] or [46]))
                    elif event.key == pygame.K_UP:
                        self.p2_selection = (self.p2_selection - 5) % 15
                    elif event.key == pygame.K_DOWN:
                        self.p2_selection = (self.p2_selection + 5) % 15
                    elif event.key in (pygame.K_KP1, pygame.K_RETURN):
                        self.p2_confirmed = True
                        self.play_voice(self.p2_selection + 1, 'a')

                elif self.p1_confirmed and self.p2_confirmed:
                    if event.key in (pygame.K_h, pygame.K_RETURN, pygame.K_SPACE):
                        self.fade_out(15)
                        self.start_fight()
                        return True

        self.screen.fill((20, 20, 60))

        if self.is_tower_mode:
            mode_label = "MODO ARCADE - ESCOLHA SEU LUTADOR"
        elif self.is_training:
            mode_label = "TREINO - ESCOLHA SEU LUTADOR"
        elif self.is_2p_mode:
            if not self.p1_confirmed:
                mode_label = "P1: ESCOLHA SEU LUTADOR (WASD + H)"
            elif not self.p2_confirmed:
                mode_label = "P2: ESCOLHA SEU LUTADOR (SETAS + NUM1)"
            else:
                mode_label = "2 JOGADORES"
        else:
            mode_label = "SELECIONE SEU LUTADOR"
        title = self.font_medium.render(mode_label, True, (255, 255, 0))
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 10))

        cell_w = 60 * SCALE // 2
        cell_h = 72 * SCALE // 2
        gap = 6
        grid_w = 5 * cell_w + 4 * gap
        grid_x = SCREEN_W // 2 - grid_w // 2
        grid_y = 60

        for i in range(15):
            row, col = i // 5, i % 5
            px = grid_x + col * (cell_w + gap)
            py = grid_y + row * (cell_h + gap)

            pygame.draw.rect(self.screen, (40, 40, 80), (px, py, cell_w, cell_h))

            if (i + 1) in self.portraits and self.portraits[i + 1]:
                portrait = self.portraits[i + 1][0]
                scaled_p = pygame.transform.scale(portrait, (cell_w, cell_h))
                self.screen.blit(scaled_p, (px, py))
            else:
                name_s = self.font_small.render(FIGHTER_NAMES[i][:6], True, (180, 180, 180))
                self.screen.blit(name_s, (px + 2, py + cell_h // 2 - 8))

            if i == self.p1_selection:
                color = (0, 200, 255) if not self.p1_confirmed else (0, 255, 0)
                pygame.draw.rect(self.screen, color,
                               (px - 3, py - 3, cell_w + 6, cell_h + 6), 3)
                p1_label = self.font_small.render("1P", True, (0, 200, 255))
                self.screen.blit(p1_label, (px, py - 16))

            if self.p2_confirmed and i == self.p2_selection:
                pygame.draw.rect(self.screen, (255, 50, 50),
                               (px - 3, py - 3, cell_w + 6, cell_h + 6), 3)
                p2_label_text = "2P" if self.is_2p_mode else "CPU"
                p2_label = self.font_small.render(p2_label_text, True, (255, 50, 50))
                self.screen.blit(p2_label, (px + cell_w - 30, py - 16))
            elif self.is_2p_mode and self.p1_confirmed and not self.p2_confirmed and i == self.p2_selection:
                # P2 is selecting
                pygame.draw.rect(self.screen, (255, 100, 100),
                               (px - 3, py - 3, cell_w + 6, cell_h + 6), 2)
                p2_label = self.font_small.render("2P?", True, (255, 100, 100))
                self.screen.blit(p2_label, (px + cell_w - 30, py - 16))

        name_y = grid_y + 3 * (cell_h + gap) + 15
        sel_name = FIGHTER_NAMES[self.p1_selection]
        name_text = self.font_medium.render(sel_name, True, (255, 255, 255))
        self.screen.blit(name_text, (SCREEN_W // 2 - name_text.get_width() // 2, name_y))

        fid = self.p1_selection + 1
        if fid in self.fighter_frames and self.fighter_frames[fid]:
            preview_frame = self.fighter_frames[fid][0]
            pscale = min(SCALE * 1.5, 200 / max(1, preview_frame.get_height()))
            preview = scale_surface(preview_frame, pscale)
            self.screen.blit(preview, (30, SCREEN_H - preview.get_height() - 20))

        if self.p2_confirmed:
            fid2 = self.p2_selection + 1
            if fid2 in self.fighter_frames and self.fighter_frames[fid2]:
                pf2 = self.fighter_frames[fid2][0]
                pscale2 = min(SCALE * 1.5, 200 / max(1, pf2.get_height()))
                preview2 = scale_surface(pygame.transform.flip(pf2, True, False), pscale2)
                self.screen.blit(preview2, (SCREEN_W - preview2.get_width() - 30,
                                            SCREEN_H - preview2.get_height() - 20))

        if self.p1_confirmed and self.p2_confirmed:
            vs_text = self.font_medium.render(
                f"{FIGHTER_NAMES[self.p1_selection]}  VS  {FIGHTER_NAMES[self.p2_selection]}",
                True, (255, 255, 0))
            self.screen.blit(vs_text, (SCREEN_W // 2 - vs_text.get_width() // 2, name_y + 35))

            if (pygame.time.get_ticks() // 400) % 2:
                prompt = self.font_small.render("Pressione H ou ENTER para lutar!", True, (255, 255, 255))
                self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, name_y + 70))

        return True

    # ==========================================
    # TOWER MODE
    # ==========================================
    def start_tower(self):
        others = [i for i in range(15) if i != self.p1_selection]
        random.shuffle(others)
        self.tower_opponents = others  # Fight ALL 14 opponents in arcade mode
        self.tower_level = 0
        self.total_score = 0
        self.state = "tower"
        self.tower_state = "display"
        self.tower_timer = 0

    def handle_tower(self):
        if self.tower_state == "display":
            return self.handle_tower_display()
        elif self.tower_state == "prefight":
            return self.handle_tower_prefight()
        elif self.tower_state == "fight":
            return self.handle_fight()
        elif self.tower_state == "win":
            return self.handle_tower_win()
        elif self.tower_state == "lose":
            return self.handle_tower_lose()
        elif self.tower_state == "victory":
            return self.handle_tower_victory()
        return True

    def handle_tower_display(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "title"
                    pygame.mixer.music.stop()
                    return True
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    self.fade_out(15)
                    self.tower_start_next_fight()
                    return True

        self.screen.fill((10, 5, 30))

        self.draw_centered_text("MODO ARCADE", 15, self.font_big, (255, 255, 0), (80, 50, 0))

        # Draw pyramid
        total = len(self.tower_opponents)
        cell_w = 56
        gap = 4
        max_height = SCREEN_H - 120
        cell_h = min(48, max(24, (max_height - (total - 1) * gap) // total))
        base_y = SCREEN_H - 55

        for i in range(total):
            level = total - 1 - i  # Bottom = last opponent, top = first
            row = level
            # Pyramid widening: top has 1, bottom has more
            offset_x = SCREEN_W // 2 - cell_w // 2

            y = base_y - row * (cell_h + gap)
            x = offset_x

            opp_idx = self.tower_opponents[i]
            fid = opp_idx + 1

            # Color by status
            if i < self.tower_level:
                # Defeated
                bg_color = (0, 80, 0)
                border_color = (0, 200, 0)
            elif i == self.tower_level:
                # Current
                bg_color = (100, 50, 0)
                border_color = (255, 200, 0)
            else:
                # Upcoming
                bg_color = (40, 20, 60)
                border_color = (80, 80, 120)

            pygame.draw.rect(self.screen, bg_color, (x, y, cell_w, cell_h))
            pygame.draw.rect(self.screen, border_color, (x, y, cell_w, cell_h), 2)

            # Portrait
            if fid in self.portraits and self.portraits[fid]:
                p = self.portraits[fid][0]
                sp = pygame.transform.scale(p, (cell_w - 4, cell_h - 4))
                self.screen.blit(sp, (x + 2, y + 2))
                if i < self.tower_level:
                    # X mark over defeated
                    cross = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                    cross.fill((0, 0, 0, 120))
                    self.screen.blit(cross, (x, y))
                    mark = self.font_small.render("X", True, (255, 0, 0))
                    self.screen.blit(mark, (x + cell_w // 2 - mark.get_width() // 2, y + 10))

            # Name to the right
            name = self.font_small.render(FIGHTER_NAMES[opp_idx], True, border_color)
            self.screen.blit(name, (x + cell_w + 8, y + cell_h // 2 - 8))

            # Level number to the left
            lvl_txt = self.font_small.render(f"{i + 1}", True, border_color)
            self.screen.blit(lvl_txt, (x - lvl_txt.get_width() - 8, y + cell_h // 2 - 8))

            # Difficulty label
            if i == self.tower_level and i < len(TOWER_DIFFICULTY):
                diff_name = TOWER_DIFFICULTY[i]["name"]
                diff_txt = self.font_small.render(diff_name, True, (255, 150, 50))
                self.screen.blit(diff_txt, (x + cell_w + 8, y + cell_h // 2 + 8))

        # Player info
        pfid = self.p1_selection + 1
        if pfid in self.portraits and self.portraits[pfid]:
            pp = self.portraits[pfid][0]
            spp = pygame.transform.scale(pp, (50, 60))
            self.screen.blit(spp, (10, 10))
        pname = self.font_medium.render(FIGHTER_NAMES[self.p1_selection], True, (0, 200, 255))
        self.screen.blit(pname, (70, 20))
        score_txt = self.font_small.render(f"Score: {self.total_score}", True, (255, 255, 255))
        self.screen.blit(score_txt, (70, 50))

        if (pygame.time.get_ticks() // 500) % 2:
            prompt = self.font_small.render("ENTER para lutar!", True, (255, 255, 255))
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, SCREEN_H - 30))

        return True

    def tower_start_next_fight(self):
        if self.tower_level >= len(self.tower_opponents):
            self.tower_state = "victory"
            return

        # Set difficulty
        diff = TOWER_DIFFICULTY[min(self.tower_level, len(TOWER_DIFFICULTY) - 1)]
        self.cpu_attack_rate = diff["attack_rate"]
        self.cpu_dmg_mult = diff["dmg_mult"]

        self.p2_selection = self.tower_opponents[self.tower_level]
        self.round_num = 1
        self.p1_wins = 0
        self.p2_wins = 0

        self.tower_state = "prefight"
        self.tower_timer = 120

    def handle_tower_prefight(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "title"
                    pygame.mixer.music.stop()
                    return True
                self.tower_timer = 0

        self.tower_timer -= 1

        self.screen.fill((0, 0, 0))

        if self.backgrounds:
            bg_idx = (self.tower_level * 3) % len(self.backgrounds)
            bg = self.backgrounds[bg_idx]
            scaled_bg = pygame.transform.scale(bg, (SCREEN_W, SCREEN_H))
            self.screen.blit(scaled_bg, (0, 0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

        level_text = f"LUTA {self.tower_level + 1}"
        self.draw_centered_text(level_text, SCREEN_H // 4, self.font_big, (255, 255, 0), (80, 50, 0))

        diff = TOWER_DIFFICULTY[min(self.tower_level, len(TOWER_DIFFICULTY) - 1)]
        self.draw_centered_text(diff["name"], SCREEN_H // 4 + 50, self.font_medium, (255, 150, 50))

        opp_name = FIGHTER_NAMES[self.p2_selection]
        self.draw_centered_text(f"VS  {opp_name}", SCREEN_H // 2, self.font_big, (255, 100, 100), (80, 0, 0))

        # Show portraits
        pfid = self.p1_selection + 1
        ofid = self.p2_selection + 1
        if pfid in self.portraits and self.portraits[pfid]:
            pp = self.portraits[pfid][0]
            spp = pygame.transform.scale(pp, (80, 96))
            self.screen.blit(spp, (SCREEN_W // 4 - 40, SCREEN_H // 2 + 40))
        if ofid in self.portraits and self.portraits[ofid]:
            op = self.portraits[ofid][0]
            sop = pygame.transform.scale(op, (80, 96))
            self.screen.blit(sop, (3 * SCREEN_W // 4 - 40, SCREEN_H // 2 + 40))

        if self.tower_timer <= 0:
            self.tower_state = "fight"
            self.start_fight()

        return True

    def handle_tower_win(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    self.tower_level += 1
                    if self.tower_level >= len(self.tower_opponents):
                        self.tower_state = "victory"
                    else:
                        self.tower_state = "display"
                    return True
                if event.key == pygame.K_ESCAPE:
                    self.state = "title"
                    pygame.mixer.music.stop()
                    return True

        self.screen.fill((0, 30, 0))
        self.draw_centered_text("VITORIA!", SCREEN_H // 3, self.font_big, (0, 255, 0), (0, 80, 0))
        bonus = (self.tower_level + 1) * 500
        self.draw_centered_text(f"Bonus: {bonus} pts", SCREEN_H // 2, self.font_medium, (255, 255, 0))
        self.draw_centered_text(f"Score Total: {self.total_score}", SCREEN_H // 2 + 40, self.font_medium, (255, 255, 255))

        remaining = len(self.tower_opponents) - self.tower_level - 1
        if remaining > 0:
            self.draw_centered_text(f"{remaining} oponentes restantes", SCREEN_H * 2 // 3, self.font_small, (200, 200, 200))

        if (pygame.time.get_ticks() // 500) % 2:
            self.draw_centered_text("ENTER para continuar", SCREEN_H - 40, self.font_small, (200, 200, 200))

        return True

    def handle_tower_lose(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                    # Retry same opponent
                    self.tower_start_next_fight()
                    return True
                if event.key == pygame.K_ESCAPE:
                    self.state = "title"
                    pygame.mixer.music.stop()
                    return True

        self.screen.fill((40, 0, 0))
        self.draw_centered_text("DERROTA", SCREEN_H // 3, self.font_big, (255, 0, 0), (80, 0, 0))
        opp_name = FIGHTER_NAMES[self.tower_opponents[self.tower_level]]
        self.draw_centered_text(f"{opp_name} venceu!", SCREEN_H // 2, self.font_medium, (255, 150, 150))
        self.draw_centered_text(f"Score: {self.total_score}", SCREEN_H // 2 + 40, self.font_medium, (255, 255, 255))
        self.draw_centered_text("ENTER = Tentar de novo | ESC = Sair", SCREEN_H - 40, self.font_small, (200, 200, 200))

        return True

    def handle_tower_victory(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                self.state = "title"
                pygame.mixer.music.stop()
                return True

        t = pygame.time.get_ticks()
        self.screen.fill((10, 10, 40))

        # Confetti-like effect
        for i in range(50):
            cx = (i * 97 + t // 3) % SCREEN_W
            cy = (i * 53 + t // 5) % SCREEN_H
            col = [(255, 255, 0), (0, 255, 0), (255, 100, 100), (100, 200, 255)][i % 4]
            pygame.draw.circle(self.screen, col, (cx, cy), 3)

        self.draw_centered_text("PARABENS!", SCREEN_H // 4, self.font_big, (255, 255, 0), (80, 50, 0))
        pname = FIGHTER_NAMES[self.p1_selection]
        self.draw_centered_text(f"{pname} E O CAMPEAO DA VILA!", SCREEN_H // 3 + 20, self.font_medium, (0, 255, 0))
        self.draw_centered_text(f"Score Final: {self.total_score}", SCREEN_H // 2 + 20, self.font_big, (255, 255, 255))

        pfid = self.p1_selection + 1
        if pfid in self.portraits and self.portraits[pfid]:
            pp = self.portraits[pfid][0]
            spp = pygame.transform.scale(pp, (100, 120))
            self.screen.blit(spp, (SCREEN_W // 2 - 50, SCREEN_H // 2 + 60))

        self.draw_centered_text("Pressione qualquer tecla", SCREEN_H - 30, self.font_small, (200, 200, 200))

        return True

    # ==========================================
    # FIGHT
    # ==========================================
    def start_fight(self):
        if not self.is_tower_mode:
            self.state = "fight"
        self.round_state = "intro"
        self.round_timer = 120
        self.timer = 99 if not self.is_training else 0
        self.timer_tick = 0
        self.fight_started = False
        self.hit_sparks = []
        self.damage_numbers = []
        self.active_effects = []
        self.first_hit_done = False

        self.current_bg = random.randint(0, max(0, len(self.backgrounds) - 1))
        self.current_ground_y = STAGE_GROUND_Y.get(self.current_bg, GROUND_Y)

        self.player1 = self.create_fighter(
            self.p1_selection + 1, 50, self.current_ground_y, True, True)
        self.player2 = self.create_fighter(
            self.p2_selection + 1, 550, self.current_ground_y, False,
            is_player=self.is_2p_mode)

        # Reset fight feel systems
        self.hitstop = 0
        self.shake_timer = 0
        self.shake_intensity = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

        if self.music_files:
            self.play_music(random.randint(1, min(5, len(self.music_files) - 1)))

        self.play_voice(self.p1_selection + 1, 'a')

    def handle_fight(self):
        self.keys_just_pressed = set()
        self._joy_buttons_just_pressed = set()  # track ("joy", btn) for joystick presses
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                self.keys_just_pressed.add(event.key)
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.handle_pause()
                    return True
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
            if event.type == pygame.JOYBUTTONDOWN:
                self._joy_buttons_just_pressed.add(("joy", event.button))

        keys = pygame.key.get_pressed()
        if self.player1:
            self.player1.inputs["left"] = keys[KEY_BINDINGS["left"]]
            self.player1.inputs["right"] = keys[KEY_BINDINGS["right"]]
            self.player1.inputs["up"] = keys[KEY_BINDINGS["up"]]
            self.player1.inputs["down"] = keys[KEY_BINDINGS["down"]]
            # In 1P mode, arrow keys also work for P1
            if not self.is_2p_mode:
                self.player1.inputs["left"] = self.player1.inputs["left"] or keys[KEY_BINDINGS_ALT["left"]]
                self.player1.inputs["right"] = self.player1.inputs["right"] or keys[KEY_BINDINGS_ALT["right"]]
                self.player1.inputs["up"] = self.player1.inputs["up"] or keys[KEY_BINDINGS_ALT["up"]]
                self.player1.inputs["down"] = self.player1.inputs["down"] or keys[KEY_BINDINGS_ALT["down"]]
            self.player1.inputs["light_punch"] = keys[KEY_BINDINGS["light_punch"]]
            self.player1.inputs["heavy_punch"] = keys[KEY_BINDINGS["heavy_punch"]]
            self.player1.inputs["light_kick"] = keys[KEY_BINDINGS["light_kick"]]
            self.player1.inputs["heavy_kick"] = keys[KEY_BINDINGS["heavy_kick"]]
            self.player1.inputs["special"] = keys[KEY_BINDINGS["special"]]

            self.player1.input_pressed["light_punch"] = KEY_BINDINGS["light_punch"] in self.keys_just_pressed
            self.player1.input_pressed["heavy_punch"] = KEY_BINDINGS["heavy_punch"] in self.keys_just_pressed
            self.player1.input_pressed["light_kick"] = KEY_BINDINGS["light_kick"] in self.keys_just_pressed
            self.player1.input_pressed["heavy_kick"] = KEY_BINDINGS["heavy_kick"] in self.keys_just_pressed
            self.player1.input_pressed["special"] = KEY_BINDINGS["special"] in self.keys_just_pressed

            # P1 joystick / gamepad (merges with keyboard)
            self._read_joy_input(self._get_joy(1), self.joy_map_p1,
                                 self.player1.inputs, self.player1.input_pressed,
                                 self._joy_buttons_just_pressed)

        # Player 2 input (2P mode uses arrow keys + numpad)
        if self.is_2p_mode and self.player2:
            self.player2.inputs["left"] = keys[P2_KEY_BINDINGS["left"]]
            self.player2.inputs["right"] = keys[P2_KEY_BINDINGS["right"]]
            self.player2.inputs["up"] = keys[P2_KEY_BINDINGS["up"]]
            self.player2.inputs["down"] = keys[P2_KEY_BINDINGS["down"]]
            self.player2.inputs["light_punch"] = keys[P2_KEY_BINDINGS["light_punch"]]
            self.player2.inputs["heavy_punch"] = keys[P2_KEY_BINDINGS["heavy_punch"]]
            self.player2.inputs["light_kick"] = keys[P2_KEY_BINDINGS["light_kick"]]
            self.player2.inputs["heavy_kick"] = keys[P2_KEY_BINDINGS["heavy_kick"]]
            self.player2.inputs["special"] = keys[P2_KEY_BINDINGS["special"]]

            self.player2.input_pressed["light_punch"] = P2_KEY_BINDINGS["light_punch"] in self.keys_just_pressed
            self.player2.input_pressed["heavy_punch"] = P2_KEY_BINDINGS["heavy_punch"] in self.keys_just_pressed
            self.player2.input_pressed["light_kick"] = P2_KEY_BINDINGS["light_kick"] in self.keys_just_pressed
            self.player2.input_pressed["heavy_kick"] = P2_KEY_BINDINGS["heavy_kick"] in self.keys_just_pressed
            self.player2.input_pressed["special"] = P2_KEY_BINDINGS["special"] in self.keys_just_pressed

            # P2 joystick / gamepad (merges with keyboard)
            self._read_joy_input(self._get_joy(2), self.joy_map_p2,
                                 self.player2.inputs, self.player2.input_pressed,
                                 self._joy_buttons_just_pressed)

        # Round state machine
        if self.round_state == "intro":
            self.round_timer -= 1
            # Walk-in: fighters approach center during intro
            if self.player1 and self.player2:
                target_p1 = 180
                target_p2 = 420
                if self.round_timer > 60:
                    # Walk phase
                    if self.player1.x < target_p1:
                        self.player1.x += 2
                        self.player1.set_anim("walk_fwd")
                    elif self.player1.x > target_p1:
                        self.player1.set_anim("idle")
                    if self.player2.x > target_p2:
                        self.player2.x -= 2
                        self.player2.set_anim("walk_fwd")
                    elif self.player2.x < target_p2:
                        self.player2.set_anim("idle")
                else:
                    self.player1.set_anim("idle")
                    self.player2.set_anim("idle")
                self.player1.update_animation()
                self.player2.update_animation()
            if self.round_timer <= 0:
                self.round_state = "fight"
                self.fight_started = True
                # Play fight start sound
                start_sfx = [s for s in [25, 30, 34] if s in self.sfx]
                if start_sfx:
                    self.sfx[random.choice(start_sfx)].play()

        elif self.round_state == "fight" and self.fight_started:
            # Hitstop: freeze gameplay for impact feel
            if self.hitstop > 0:
                self.hitstop -= 1
            else:
                if self.player1 and self.player1.alive:
                    self.player1.update_input(self.player2)
                if self.player2 and self.player2.alive:
                    if self.is_2p_mode:
                        self.player2.update_input(self.player1)
                    else:
                        self.update_cpu(self.player2, self.player1)

                if self.player1: self.player1.update_physics()
                if self.player2: self.player2.update_physics()

                self.check_attacks()
                self.push_fighters()

                # Training mode: regenerate HP for both fighters
                if self.is_training:
                    for f in (self.player1, self.player2):
                        if f:
                            if f.hp < f.max_hp:
                                f.hp = min(f.max_hp, f.hp + 0.3)
                            if f.hp <= 0:
                                f.hp = f.max_hp
                                f.hp_display = f.max_hp
                                f.alive = True
                                f.knockdown = False
                                f.knockdown_timer = 0
                                f.set_anim("idle")

                # Cheat effects (P1 only)
                if self.player1:
                    if self.cheat_god_mode:
                        self.player1.hp = self.player1.max_hp
                        self.player1.hp_display = self.player1.max_hp
                        if not self.player1.alive:
                            self.player1.alive = True
                            self.player1.knockdown = False
                            self.player1.knockdown_timer = 0
                            self.player1.set_anim("idle")
                    if self.cheat_max_meter:
                        self.player1.special_meter = self.player1.max_special

                if not self.is_training:
                    self.timer_tick += 1
                    if self.timer_tick >= FPS:
                        self.timer_tick = 0
                        self.timer -= 1
                        if self.timer <= 0:
                            self.timer = 0
                            self.end_round_by_time()

                if self.player1: self.player1.update_animation()
                if self.player2: self.player2.update_animation()

            # Screen shake update
            if self.shake_timer > 0:
                self.shake_timer -= 1
                intensity = self.shake_intensity * (self.shake_timer / max(1, self.shake_timer + 2))
                self.shake_offset_x = random.uniform(-intensity, intensity)
                self.shake_offset_y = random.uniform(-intensity, intensity)
            else:
                self.shake_offset_x = 0
                self.shake_offset_y = 0

            if not self.is_training:
                if self.player1 and not self.player1.alive:
                    self.round_state = "ko"
                    self.ko_timer = 120
                    self.p2_wins += 1
                    self.play_ko_sound()
                    if self.player2:
                        self.player2.set_anim("win")
                        self.play_voice(self.p2_selection + 1, 'b')
                elif self.player2 and not self.player2.alive:
                    self.round_state = "ko"
                    self.ko_timer = 120
                    self.p1_wins += 1
                    self.play_ko_sound()
                    if self.player1:
                        self.player1.set_anim("win")
                        self.play_voice(self.p1_selection + 1, 'b')

        elif self.round_state == "ko":
            self.ko_timer -= 1
            if self.player1:
                self.player1.update_animation()
                self.player1.update_physics()
            if self.player2:
                self.player2.update_animation()
                self.player2.update_physics()
            if self.ko_timer <= 0:
                if self.p1_wins >= 2 or self.p2_wins >= 2:
                    if self.is_tower_mode:
                        self.handle_tower_fight_end()
                    else:
                        self.state = "result"
                        self.round_timer = 240
                else:
                    self.round_num += 1
                    self.restart_round()

        self.hit_sparks = [s for s in self.hit_sparks if s.update()]
        self.damage_numbers = [d for d in self.damage_numbers if d.update()]
        self.active_effects = [e for e in self.active_effects if e.update()]

        self.update_camera()
        self.draw_fight()
        return True

    def handle_tower_fight_end(self):
        if self.p1_wins >= 2:
            if self.player1:
                self.total_score += self.player1.score + (self.tower_level + 1) * 500
            self.tower_state = "win"
            self.state = "tower"
        else:
            self.tower_state = "lose"
            self.state = "tower"

    def end_round_by_time(self):
        self.round_state = "ko"
        self.ko_timer = 120
        if self.player1 and self.player2:
            if self.player1.hp > self.player2.hp:
                self.p1_wins += 1
                self.player1.set_anim("win")
            elif self.player2.hp > self.player1.hp:
                self.p2_wins += 1
                self.player2.set_anim("win")

    def restart_round(self):
        self.round_state = "intro"
        self.round_timer = 90
        self.timer = 99
        self.timer_tick = 0
        self.fight_started = False
        self.hit_sparks = []
        self.damage_numbers = []
        self.active_effects = []
        self.first_hit_done = False

        for f, start_x, face_right in [(self.player1, 150, True), (self.player2, 450, False)]:
            if f:
                f.x = start_x
                f.y = self.current_ground_y
                f.facing_right = face_right
                f.hp = f.max_hp
                f.hp_display = f.max_hp
                f.alive = True
                f.knockdown = False
                f.knockdown_timer = 0
                f.attacking = False
                f.attack_hitbox = None
                f.vx = 0
                f.vy = 0
                f.hit_stun = 0
                f.block_stun = 0
                f.invincible = 0
                f.combo_hits = 0
                f.combo_damage = 0
                f.combo_timer = 0
                f.on_ground = True
                f.set_anim("idle")

    def update_cpu(self, cpu, target):
        if not cpu.alive or cpu.knockdown or cpu.hit_stun > 0:
            cpu.update_input(target)
            return

        if not target or not target.alive:
            for k in cpu.inputs: cpu.inputs[k] = False
            for k in cpu.input_pressed: cpu.input_pressed[k] = False
            cpu.update_input(target)
            return

        dist = abs(cpu.x - target.x)

        for k in cpu.inputs: cpu.inputs[k] = False
        for k in cpu.input_pressed: cpu.input_pressed[k] = False

        if cpu.attacking:
            cpu.update_input(target)
            return

        r = random.random()
        ar = self.cpu_attack_rate

        # CPU blocking: react to opponent attacks
        if target.attacking and dist < 100:
            block_chance = 0.25 * ar
            if r < block_chance:
                # Block: hold back + down
                if target.x > cpu.x:
                    cpu.inputs["left"] = True
                else:
                    cpu.inputs["right"] = True
                cpu.inputs["down"] = True
                cpu.update_input(target)
                return

        # CPU jumps to dodge or approach
        if not cpu.on_ground:
            # Air attack when close and descending
            if dist < 80 and cpu.vy > 0 and r < 0.15 * ar:
                atk = random.choice(["light_kick", "heavy_kick", "light_punch"])
                cpu.input_pressed[atk] = True
            cpu.update_input(target)
            return

        if dist > 150:
            # Approach - walk or jump toward
            if target.x > cpu.x:
                cpu.inputs["right"] = True
            else:
                cpu.inputs["left"] = True
            if r < 0.03 * ar:
                cpu.inputs["up"] = True
        elif dist > 70:
            # Mid range - mix attacks and movement
            if r < 0.06 * ar:
                cpu.input_pressed["heavy_punch"] = True
            elif r < 0.11 * ar:
                cpu.input_pressed["heavy_kick"] = True
            elif r < 0.16 * ar:
                cpu.input_pressed["light_punch"] = True
            elif r < 0.19 * ar:
                cpu.inputs["up"] = True  # Jump in
                if target.x > cpu.x:
                    cpu.inputs["right"] = True
                else:
                    cpu.inputs["left"] = True
            elif r < 0.24:
                # Step back
                if target.x > cpu.x:
                    cpu.inputs["left"] = True
                else:
                    cpu.inputs["right"] = True
            elif r < 0.27 * ar and cpu.special_meter >= 50:
                cpu.input_pressed["special"] = True
            else:
                if target.x > cpu.x:
                    cpu.inputs["right"] = True
                else:
                    cpu.inputs["left"] = True
        else:
            # Close range - fast attacks, throws, specials
            if r < 0.10 * ar:
                cpu.input_pressed["light_punch"] = True
            elif r < 0.18 * ar:
                cpu.input_pressed["light_kick"] = True
            elif r < 0.24 * ar:
                cpu.input_pressed["heavy_punch"] = True
            elif r < 0.29 * ar:
                cpu.input_pressed["heavy_kick"] = True
            elif r < 0.33 * ar and cpu.special_meter >= 50:
                cpu.input_pressed["special"] = True
            elif r < 0.38:
                # Crouch block
                cpu.inputs["down"] = True
                if target.x > cpu.x:
                    cpu.inputs["left"] = True
                else:
                    cpu.inputs["right"] = True
            elif r < 0.42:
                # Jump away to create space
                cpu.inputs["up"] = True
                if target.x > cpu.x:
                    cpu.inputs["left"] = True
                else:
                    cpu.inputs["right"] = True

        cpu.update_input(target)

    def check_attacks(self):
        if not self.player1 or not self.player2:
            return

        for attacker, defender in [(self.player1, self.player2), (self.player2, self.player1)]:
            # Play whoosh sound when attack starts
            if attacker.attack_voice_pending and attacker.attacking:
                attacker.attack_voice_pending = False
                whoosh_pool = [s for s in [6, 8, 46, 48] if s in self.sfx]
                if whoosh_pool:
                    self.sfx[random.choice(whoosh_pool)].play()

            if attacker.attack_hitbox and not attacker.has_hit:
                body = defender.get_body_rect()
                if attacker.attack_hitbox.colliderect(body):
                    is_heavy = "heavy" in attacker.attack_type or attacker.attack_type == "special"
                    is_special = attacker.attack_type == "special"

                    # Apply CPU damage multiplier
                    actual_damage = attacker.attack_damage
                    if not attacker.is_player:
                        actual_damage = int(actual_damage * self.cpu_dmg_mult)

                    # Cheat: one punch mode
                    if self.cheat_one_punch and attacker.is_player:
                        actual_damage = 999

                    hit = defender.take_hit(actual_damage, attacker)
                    attacker.has_hit = True

                    ix = (attacker.x + defender.x) / 2
                    iy = min(attacker.y, defender.y) - 40

                    if hit:
                        self.play_hit_sound(heavy=is_heavy)
                        self.spawn_hit_spark(ix, iy, heavy=is_heavy)
                        self.spawn_damage_number(ix, iy, actual_damage)

                        # Hitstop - freeze frames for impact feel
                        if is_special:
                            self.hitstop = 8
                        elif is_heavy:
                            self.hitstop = 5
                        else:
                            self.hitstop = 3

                        # Screen shake on heavy attacks
                        if is_special:
                            self.shake_timer = 12
                            self.shake_intensity = 6
                        elif is_heavy:
                            self.shake_timer = 8
                            self.shake_intensity = 4

                        if is_special:
                            self.play_special_sound()
                            self.spawn_special_effect(defender.x, defender.y, target=defender)

                        if defender.knockdown:
                            self.spawn_knockdown_effect(defender.x, defender.y)
                            # KO voice
                            if not defender.alive:
                                self.play_voice(attacker.id, 'b')

                        if not self.first_hit_done:
                            self.first_hit_done = True
                            attacker.score += 300
                    else:
                        self.play_block_sound()

    def push_fighters(self):
        if not self.player1 or not self.player2:
            return
        min_dist = 35
        dist = self.player1.x - self.player2.x
        if abs(dist) < min_dist:
            push = (min_dist - abs(dist)) / 2 + 0.5

            if dist > 0:
                new_p1 = self.player1.x + push
                new_p2 = self.player2.x - push
            else:
                new_p1 = self.player1.x - push
                new_p2 = self.player2.x + push

            wall_min, wall_max = 10, BG_SCROLL_W - 10
            if new_p1 < wall_min:
                overflow = wall_min - new_p1
                new_p1 = wall_min
                new_p2 -= overflow
            elif new_p1 > wall_max:
                overflow = new_p1 - wall_max
                new_p1 = wall_max
                new_p2 += overflow
            if new_p2 < wall_min:
                overflow = wall_min - new_p2
                new_p2 = wall_min
                new_p1 += overflow
            elif new_p2 > wall_max:
                overflow = new_p2 - wall_max
                new_p2 = wall_max
                new_p1 -= overflow

            self.player1.x = max(wall_min, min(wall_max, new_p1))
            self.player2.x = max(wall_min, min(wall_max, new_p2))

    def update_camera(self):
        if self.player1 and self.player2:
            center = (self.player1.x + self.player2.x) / 2
            target = center - ORIGINAL_W / 2
            self.camera_x += (target - self.camera_x) * 0.1
            self.camera_x = max(0, min(self.camera_x, BG_SCROLL_W - ORIGINAL_W))

    def draw_fight(self):
        self.screen.fill((0, 0, 0))

        # Screen shake offset
        shake_x = int(self.shake_offset_x)
        shake_y = int(self.shake_offset_y)

        # Create a fight surface to apply shake
        fight_surface = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fight_surface.fill((0, 0, 0, 0))

        if self.backgrounds and self.current_bg < len(self.backgrounds):
            bg = self.backgrounds[self.current_bg]
            bg_w, bg_h = bg.get_size()
            src_x = int(self.camera_x)
            src_w = min(ORIGINAL_W, bg_w - src_x)
            if src_w > 0:
                visible_bg = bg.subsurface(pygame.Rect(src_x, 0, src_w, bg_h))
                scaled_bg = pygame.transform.scale(visible_bg, (SCREEN_W, SCREEN_H))
                fight_surface.blit(scaled_bg, (0, 0))

        if self.player2: self.player2.draw(fight_surface, self.camera_x)
        if self.player1: self.player1.draw(fight_surface, self.camera_x)

        for fx in self.active_effects:
            fx.draw(fight_surface, self.camera_x)
        for spark in self.hit_sparks:
            spark.draw(fight_surface, self.camera_x)
        for dn in self.damage_numbers:
            dn.draw(fight_surface, self.camera_x)

        # Blit with shake offset
        self.screen.blit(fight_surface, (shake_x, shake_y))

        self.draw_hud()

        if self.round_state == "intro":
            if self.is_tower_mode:
                round_label = f"LUTA {self.tower_level + 1}"
            elif self.is_training:
                round_label = "TREINO"
            else:
                round_label = f"ROUND {self.round_num}"
            if self.round_timer >= 60:
                self.draw_centered_text(round_label, SCREEN_H // 2 - 50, self.font_big,
                                         (255, 255, 0), shadow=(0, 0, 0))
                p1n = FIGHTER_NAMES[self.p1_selection]
                p2n = FIGHTER_NAMES[self.p2_selection]
                self.draw_centered_text(f"{p1n}  VS  {p2n}", SCREEN_H // 2 + 10,
                                         self.font_medium, (255, 150, 150), shadow=(80, 0, 0))
            else:
                flash = abs(math.sin(pygame.time.get_ticks() * 0.01))
                lute_color = (255, int(255 * flash), 0)
                self.draw_centered_text("LUTE!", SCREEN_H // 2 - 20, self.font_big,
                                         lute_color, shadow=(0, 0, 0))
        elif self.round_state == "ko":
            ko_pulse = abs(math.sin(pygame.time.get_ticks() * 0.008))
            ko_color = (255, int(60 * ko_pulse), 0)
            self.draw_centered_text("K.O.!", SCREEN_H // 2 - 20, self.font_big,
                                     ko_color, shadow=(80, 0, 0))

        # Combo display
        for fighter in (self.player1, self.player2):
            if fighter and fighter.combo_hits >= 2 and fighter.combo_timer > 0:
                combo_text = f"{fighter.combo_hits}"
                ct = self.font_combo.render(combo_text, True, (255, 200, 0))
                cx = 30 if fighter.is_player else SCREEN_W - ct.get_width() - 30
                cy = 80
                # Shadow
                shadow = self.font_combo.render(combo_text, True, (80, 50, 0))
                self.screen.blit(shadow, (cx + 2, cy + 2))
                self.screen.blit(ct, (cx, cy))
                acertos = self.font_small.render("Acertos.", True, (255, 100, 0))
                self.screen.blit(acertos, (cx, cy + 32))

        # Training mode: show move list
        if self.is_training:
            training_label = self.font_medium.render("TREINO", True, (0, 255, 100))
            self.screen.blit(training_label, (SCREEN_W // 2 - training_label.get_width() // 2, 50))

            moves = [
                "H = Soco Fraco", "J = Chute Fraco",
                "K = Soco Forte", "L = Chute Forte",
                "O = Especial (50%+)", "W = Pular",
                "S = Agachar", "TRAS+S = Defesa",
            ]
            my = SCREEN_H - len(moves) * 18 - 10
            for i, move in enumerate(moves):
                mt = self.font_small.render(move, True, (180, 255, 180))
                self.screen.blit(mt, (10, my + i * 18))

    def draw_hud(self):
        bar_w = 280
        bar_h = 20
        margin = 20
        sp_h = 10

        for fighter, is_left in [(self.player1, True), (self.player2, False)]:
            if not fighter:
                continue

            bx = margin if is_left else SCREEN_W - margin - bar_w

            # HP bar background
            pygame.draw.rect(self.screen, (60, 0, 0), (bx, 10, bar_w, bar_h))

            hp_ratio = max(0, fighter.hp_display / fighter.max_hp)
            hp_w = int(bar_w * hp_ratio)
            if hp_ratio > 0.5:
                color = (0, 200, 0)
            elif hp_ratio > 0.25:
                color = (200, 200, 0)
            else:
                color = (200, 0, 0)

            if is_left:
                pygame.draw.rect(self.screen, color, (bx, 10, hp_w, bar_h))
            else:
                pygame.draw.rect(self.screen, color, (bx + bar_w - hp_w, 10, hp_w, bar_h))

            # Damage decay visual
            hp_real_ratio = max(0, fighter.hp / fighter.max_hp)
            hp_real_w = int(bar_w * hp_real_ratio)
            if hp_real_w < hp_w:
                dark_color = (color[0] // 2, color[1] // 2, color[2] // 2)
                if is_left:
                    pygame.draw.rect(self.screen, dark_color,
                                   (bx + hp_real_w, 10, hp_w - hp_real_w, bar_h))
                else:
                    diff = hp_w - hp_real_w
                    pygame.draw.rect(self.screen, dark_color,
                                   (bx + bar_w - hp_w, 10, diff, bar_h))

            pygame.draw.rect(self.screen, (200, 200, 200), (bx, 10, bar_w, bar_h), 2)

            # Power / Special meter
            sp_y = 10 + bar_h + 3
            sp_ratio = fighter.special_meter / fighter.max_special
            sp_w = int(bar_w * sp_ratio)
            pygame.draw.rect(self.screen, (20, 20, 60), (bx, sp_y, bar_w, sp_h))

            # Power bar color - flash when >= 50
            if fighter.special_meter >= 50:
                flash = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.5 + 0.5
                sp_color = (int(255 * flash), int(200 * flash), 0)
            else:
                sp_color = (0, 80, 200)

            if is_left:
                pygame.draw.rect(self.screen, sp_color, (bx, sp_y, sp_w, sp_h))
            else:
                pygame.draw.rect(self.screen, sp_color, (bx + bar_w - sp_w, sp_y, sp_w, sp_h))

            pygame.draw.rect(self.screen, (100, 100, 200), (bx, sp_y, bar_w, sp_h), 1)

            # "SUPER!" label when meter >= 50
            if fighter.special_meter >= 50:
                flash_alpha = int(abs(math.sin(pygame.time.get_ticks() * 0.008)) * 255)
                super_txt = self.font_small.render("SUPER!", True, (255, 255, 0))
                super_txt.set_alpha(flash_alpha)
                if is_left:
                    self.screen.blit(super_txt, (bx + bar_w - super_txt.get_width() - 2, sp_y - 1))
                else:
                    self.screen.blit(super_txt, (bx + 2, sp_y - 1))

            # Name
            name = self.font_small.render(fighter.name, True, (255, 255, 255))
            name_shadow = self.font_small.render(fighter.name, True, (0, 0, 0))
            nx = margin if is_left else SCREEN_W - margin - name.get_width()
            self.screen.blit(name_shadow, (nx + 1, sp_y + sp_h + 3))
            self.screen.blit(name, (nx, sp_y + sp_h + 2))

            # Portrait
            if fighter.portraits:
                p = fighter.portraits[0]
                scaled_p = pygame.transform.scale(p, (36, 44))
                if is_left:
                    self.screen.blit(scaled_p, (bx + bar_w + 4, 6))
                else:
                    self.screen.blit(scaled_p, (bx - 40, 6))

        # Timer
        if self.is_training:
            inf_text = self.font_big.render("--", True, (100, 255, 100))
            tx = SCREEN_W // 2 - inf_text.get_width() // 2
            self.screen.blit(inf_text, (tx, 5))
        else:
            if self.timer <= 10:
                t_flash = abs(math.sin(pygame.time.get_ticks() * 0.008))
                timer_color = (255, int(60 * t_flash), int(60 * t_flash))
            else:
                timer_color = (255, 255, 255)
            timer_text = self.font_big.render(f"{self.timer:02d}", True, timer_color)
            shadow = self.font_big.render(f"{self.timer:02d}", True, (0, 0, 0))
            tx = SCREEN_W // 2 - timer_text.get_width() // 2
            self.screen.blit(shadow, (tx + 2, 6))
            self.screen.blit(timer_text, (tx, 5))

        # Round label above timer
        if self.is_tower_mode:
            blabel = f"LUTA {self.tower_level + 1}"
        elif self.is_training:
            blabel = "TREINO"
        else:
            blabel = f"ROUND {self.round_num}"

        # Score display
        if self.player1:
            score_text = self.font_small.render(f"{self.player1.score}", True, (255, 255, 255))
            self.screen.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, 36))

        # Round win indicators
        for i in range(self.p1_wins):
            pygame.draw.rect(self.screen, (255, 200, 0), (margin + i * 18, 55, 12, 12))
            pygame.draw.rect(self.screen, (180, 140, 0), (margin + i * 18, 55, 12, 12), 1)
        for i in range(2 - self.p1_wins):
            pygame.draw.rect(self.screen, (40, 30, 0), (margin + (self.p1_wins + i) * 18, 55, 12, 12))
            pygame.draw.rect(self.screen, (80, 60, 0), (margin + (self.p1_wins + i) * 18, 55, 12, 12), 1)

        for i in range(self.p2_wins):
            pygame.draw.rect(self.screen, (255, 200, 0),
                           (SCREEN_W - margin - 12 - i * 18, 55, 12, 12))
            pygame.draw.rect(self.screen, (180, 140, 0),
                           (SCREEN_W - margin - 12 - i * 18, 55, 12, 12), 1)
        for i in range(2 - self.p2_wins):
            pygame.draw.rect(self.screen, (40, 30, 0),
                           (SCREEN_W - margin - 12 - (self.p2_wins + i) * 18, 55, 12, 12))
            pygame.draw.rect(self.screen, (80, 60, 0),
                           (SCREEN_W - margin - 12 - (self.p2_wins + i) * 18, 55, 12, 12), 1)

    # ==========================================
    # RESULT (normal mode)
    # ==========================================
    def handle_result(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                self.state = "select"
                self.p1_confirmed = False
                self.p2_confirmed = False
                self.p1_wins = 0
                self.p2_wins = 0
                self.round_num = 1
                return True

        self.round_timer -= 1

        if self.backgrounds and self.current_bg < len(self.backgrounds):
            bg = self.backgrounds[self.current_bg]
            scaled_bg = pygame.transform.scale(bg, (SCREEN_W, SCREEN_H))
            self.screen.blit(scaled_bg, (0, 0))

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        if self.p1_wins >= 2:
            winner_name = FIGHTER_NAMES[self.p1_selection]
            winner_id = self.p1_selection + 1
        elif self.p2_wins >= 2:
            winner_name = FIGHTER_NAMES[self.p2_selection]
            winner_id = self.p2_selection + 1
        else:
            winner_name = "EMPATE"
            winner_id = 0

        self.draw_centered_text(f"{winner_name} VENCE!", SCREEN_H // 4, self.font_big,
                                 (255, 255, 0), shadow=(80, 50, 0))

        if winner_id > 0 and winner_id in self.portraits:
            p = self.portraits[winner_id][0]
            scaled = pygame.transform.scale(p, (100, 120))
            self.screen.blit(scaled, (SCREEN_W // 2 - 50, SCREEN_H // 3 + 20))

        score_text = f"{self.p1_wins} - {self.p2_wins}"
        self.draw_centered_text(score_text, SCREEN_H * 2 // 3, self.font_big,
                                 (255, 255, 255))

        if (pygame.time.get_ticks() // 500) % 2:
            self.draw_centered_text("Pressione qualquer tecla", SCREEN_H - 60,
                                     self.font_small, (200, 200, 200))

        if self.round_timer <= 0:
            self.state = "select"
            self.p1_confirmed = False
            self.p2_confirmed = False
            self.p1_wins = 0
            self.p2_wins = 0
            self.round_num = 1

        return True

    # ==========================================
    # PAUSE
    # ==========================================
    def handle_pause(self):
        paused = True
        pause_option = 0
        pause_items = ["CONTINUAR", "SELECAO DE LUTADOR", "MENU PRINCIPAL"]
        while paused:
            # Draw fight scene underneath
            self.draw_fight()

            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            self.draw_centered_text("PAUSA", SCREEN_H // 2 - 80, self.font_big,
                                     (255, 255, 0), shadow=(80, 50, 0))

            for i, item in enumerate(pause_items):
                y = SCREEN_H // 2 - 20 + i * 40
                if i == pause_option:
                    color = (255, 255, 0)
                    prefix = "> "
                else:
                    color = (180, 180, 180)
                    prefix = "  "
                self.draw_centered_text(prefix + item, y, self.font_medium, color)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        paused = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        pause_option = (pause_option - 1) % len(pause_items)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        pause_option = (pause_option + 1) % len(pause_items)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h):
                        if pause_option == 0:
                            paused = False
                        elif pause_option == 1:
                            self.state = "select"
                            self.p1_confirmed = False
                            self.p2_confirmed = False
                            self.p1_wins = 0
                            self.p2_wins = 0
                            self.round_num = 1
                            pygame.mixer.music.stop()
                            paused = False
                        elif pause_option == 2:
                            if self.is_tower_mode:
                                self.state = "tower"
                                self.tower_state = "display"
                            else:
                                self.state = "title"
                            pygame.mixer.music.stop()
                            paused = False
            self.clock.tick(30)

    # ==========================================
    # MAIN LOOP
    # ==========================================
    def run(self):
        running = True
        while running:
            if self.state == "intro":
                running = self.handle_intro()
            elif self.state == "title":
                running = self.handle_title()
            elif self.state == "options":
                running = self.handle_options()
            elif self.state == "jukebox":
                running = self.handle_jukebox()
            elif self.state == "select":
                running = self.handle_select()
            elif self.state == "fight":
                running = self.handle_fight()
            elif self.state == "result":
                running = self.handle_result()
            elif self.state == "tower":
                running = self.handle_tower()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
