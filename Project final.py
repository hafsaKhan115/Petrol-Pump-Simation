from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, sys, random, time

# ─── Window ──────────────────────────────────────────────────────────────────
WIN_W, WIN_H = 1000, 800

# ─── Scene constants ──────────────────────────────────────────────────────────
CANOPY_W = 520
CANOPY_D = 400
CANOPY_H = 400
ROOF_T   = 28

# ─── Seller fixed position ────────────────────────────────────────────────────
SEL_X_HOME  =  115.0
SEL_Y_HOME  =  -50.0
SEL_YAW     = math.pi * 0.12   # world-space yaw the seller body faces

# ─── Camera – 3rd person ─────────────────────────────────────────────────────
cam_angle  = 0.35
cam_height = 700.0
cam_radius = 1000.0

# ─── Camera – 1st person ─────────────────────────────────────────────────────
is_first_person = False
fp_yaw   = 0.0
fp_pitch = 0.0

# ─── Day/Night state ─────────────────────────────────────────────────────────
day_light = 1.0  # 1.0 is full day, 0.0 is night

# ─── Road / Queue constants ───────────────────────────────────────────────────
ROAD_Y_ENTRY  = -1800
ROAD_Y_PUMP   =    0
ROAD_X        = -200
PUMP_STOP_Y   = -130
VEHICLE_GAP   =  200

# ─── Seller walk state ────────────────────────────────────────────────────────
sel_x          = SEL_X_HOME
sel_y          = SEL_Y_HOME
seller_walk_t  = 0.0
SELLER_SPEED   = 200.0

seller_walking_backward = False
seller_at_vehicle       = False

# ─── Nozzle / fueling state ───────────────────────────────────────────────────
nozzle_connected  = False
seller_fueling    = False
fuel_timer        = 0.0

# ─── Fuel system constants ────────────────────────────────────────────────────
FUEL_RATE = 1.0          # litres per second
FUEL_LIMITS = {
    "bike":  5.0,
    "car":   10.0,
    "truck": 20.0,
}
fuel_dispensed     = 0.0   # litres dispensed this session
fuel_limit_reached = False
fuel_limit_msg_timer = 0.0  # how long to show the "tank full" message

# ─── Simulation state ─────────────────────────────────────────────────────────
last_time        = 0.0
spawn_timer      = 0.0
SPAWN_INTERVAL   = 3.5
vehicles         = []
gate_angle       = 90.0
station_open     = True

VTYPES = ["bike", "car", "truck"]

def make_vehicle():
    vtype = random.choice(VTYPES)
    color_body = (random.uniform(0.4,1.0), random.uniform(0.1,0.8), random.uniform(0.1,0.8))
    return {
        "type"  : vtype,
        "x"     : ROAD_X,
        "y"     : ROAD_Y_ENTRY,
        "speed" : random.uniform(180, 260),
        "color" : color_body,
        "state" : "moving",
        "fuel_t": 0.0,
        "fuel_pct": 0.0,
        "is_exited": False,
        "exit_anim": 0.0
    }


#MOHSINA
# Daily statistics (reset each day)
daily_vehicles_served = 0
daily_fuel_dispensed = 0.0   
daily_revenue = 0.0             

# Lifetime (never reset)
lifetime_vehicles_served = 0
lifetime_fuel_dispensed = 0.0    
lifetime_revenue = 0.0           

# Tank sizes for pricing calculation
BIKE_TANK_SIZE = 5.0    
CAR_TANK_SIZE = 10.0   
TRUCK_TANK_SIZE = 20.0 
PRICE_PER_FULL_TANK = 120.0 

# Time-based daily reset system
time_since_last_reset = 0.0
AUTO_RESET_INTERVAL = 120.0  # Reset every 120 seconds 

# Animated money effects
class MoneyEffect:
    def __init__(self, start_x, start_y, start_z, amount):
        self.x = start_x
        self.y = start_y
        self.z = start_z
        self.amount = amount
        self.life_time = 2.0
        self.elapsed = 0.0
        self.vx = (random.random() - 0.5) * 300
        self.vy = (random.random() - 0.5) * 300
        self.vz = 200

money_effects = []  # List of active money effects

# Receipt/Invoice system
class Receipt:
    def __init__(self, vehicle_type, fuel_amount, price, time_str):
        self.vehicle_type = vehicle_type.upper()
        self.fuel_amount = fuel_amount
        self.price = price
        self.time = time_str
        self.display_time = 3.0
        self.elapsed = 0.0

active_receipt = None

# Cheat mode system
cheat_mode_active = False
cheat_auto_serve_timer = 0.0
cheat_cars_served_this_cycle = 0
CHEAT_AUTO_SERVE_INTERVAL = 4.0
CHEAT_RESET_AT_CARS = 7

# Clock system (simulated time)
simulation_time_hours = 8.0
simulation_time_minutes = 0.0
time_scale = 60.0  # 1 real second = 60 sim seconds
sim_speed = 1.0    # Speed multiplier for cheat mode controls





# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_box(x1,y1,z1, x2,y2,z2):
    glBegin(GL_QUADS)
    glVertex3f(x1,y1,z1); glVertex3f(x2,y1,z1); glVertex3f(x2,y2,z1); glVertex3f(x1,y2,z1)
    glVertex3f(x1,y1,z2); glVertex3f(x2,y1,z2); glVertex3f(x2,y2,z2); glVertex3f(x1,y2,z2)
    glVertex3f(x1,y1,z1); glVertex3f(x2,y1,z1); glVertex3f(x2,y1,z2); glVertex3f(x1,y1,z2)
    glVertex3f(x1,y2,z1); glVertex3f(x2,y2,z1); glVertex3f(x2,y2,z2); glVertex3f(x1,y2,z2)
    glVertex3f(x1,y1,z1); glVertex3f(x1,y2,z1); glVertex3f(x1,y2,z2); glVertex3f(x1,y1,z2)
    glVertex3f(x2,y1,z1); glVertex3f(x2,y2,z1); glVertex3f(x2,y2,z2); glVertex3f(x2,y1,z2)
    glEnd()


def draw_manual_solid_cylinder(br, tr, h, sl, lw=2.0):
    glLineWidth(lw)
    glBegin(GL_LINES)
    layers = max(int(h / max(1,lw)), 1) + 8
    for i in range(sl):
        a0 = 2*math.pi*i/sl;     a1 = 2*math.pi*(i+1)/sl
        c0,s0 = math.cos(a0), math.sin(a0)
        c1,s1 = math.cos(a1), math.sin(a1)
        glVertex3f(br*c0,br*s0,0);  glVertex3f(tr*c0,tr*s0,h)
        for j in range(layers+1):
            hj = h*j/layers
            r  = br+(tr-br)*j/layers
            glVertex3f(r*c0,r*s0,hj);  glVertex3f(r*c1,r*s1,hj)
    glEnd()
    glLineWidth(1.0)


def _enter_ortho():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

def _exit_ortho():
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_text(x, y, text, color=(1,1,1)):
    glColor3f(*color)
    _enter_ortho()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    _exit_ortho()

def draw_text_large(x, y, text, color=(1,1,1)):
    glColor3f(*color)
    _enter_ortho()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    _exit_ortho()

def set_color_lit(r, g, b):
    """Sets color with a minimum floor so the station is visible at night."""
    ambient_min = 0.4
    brightness = max(ambient_min, day_light)
    glColor3f(r * brightness, g * brightness, b * brightness)

def draw_human(color=(0.84, 0.63, 0.43), is_standing=True):
    """Draws a human with professional attire."""
    quad = gluNewQuadric()
    glPushMatrix()
    
    # Trousers
    glColor3f(0.15, 0.15, 0.15)
    if is_standing:
        draw_box(-12, -8, 0, -2, 8, 45)
        draw_box(2, -8, 0, 12, 8, 45)
        draw_box(-12, -8, 45, 12, 8, 55)
    else:
        draw_box(-12, -30, 35, -2, 8, 50)
        draw_box(2, -30, 35, 12, 8, 50)
        draw_box(-12, -10, 35, 12, 8, 55)

    # Shirt
    glColor3f(0.7, 0.8, 0.9)
    draw_box(-15, -10, 55, 15, 10, 95)
    
    glColor3f(0.5, 0.6, 0.8)
    draw_box(-6, -11, 92, 6, -6, 98)

    # Head
    glColor3f(color[0], color[1], color[2])
    glPushMatrix()
    glTranslatef(0, 0, 95)
    draw_manual_solid_cylinder(5, 5, 10, 8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 112)
    gluSphere(quad, 14, 16, 16)
    
    glColor3f(0.1, 0.05, 0.02)
    glPushMatrix()
    glTranslatef(0, 0, 4)
    glScalef(1.1, 1.1, 0.8)
    gluSphere(quad, 13, 12, 12)
    glPopMatrix()
    glPopMatrix()

    # Arms
    glColor3f(0.7, 0.8, 0.9)
    draw_box(-22, -8, 70, -15, 8, 92)
    draw_box(15, -8, 70, 22, 8, 92)
    
    glColor3f(color[0], color[1], color[2])
    draw_box(-21, -7, 60, -16, 7, 70)
    draw_box(16, -7, 60, 21, 7, 70)

    glPopMatrix()


def draw_station_name_on_fascia():
    bz1 = CANOPY_H - 12
    bz2 = CANOPY_H + ROOF_T + 4
    by_face = -CANOPY_D - 15 - 16 - 4  # in front of fascia front face at -431

    text   = "openGL Filling Station"
    n      = len(text)
    char_w = 18.0
    char_h = 24.0
    gap    = 4.0
    total_w = n * (char_w + gap) - gap
    start_x = -total_w / 2.0
    text_z  = (bz1 + bz2) / 2.0 - char_h / 2.0

    glColor3f(1.0, 0.92, 0.15)
    glEnable(GL_DEPTH_TEST)

    for ci, ch in enumerate(text):
        ox = start_x + ci * (char_w + gap)
        _draw_char_geometry(ch, ox, by_face, text_z, char_w, char_h)



_SEG_T  = 0b1000000
_SEG_M  = 0b0100000
_SEG_B  = 0b0010000
_SEG_TL = 0b0001000
_SEG_TR = 0b0000100
_SEG_BL = 0b0000010
_SEG_BR = 0b0000001

_CHAR_MAP = {
    'o': _SEG_T|_SEG_B|_SEG_TL|_SEG_TR|_SEG_BL|_SEG_BR,
    'p': _SEG_T|_SEG_M|_SEG_TL|_SEG_TR|_SEG_BL,
    'e': _SEG_T|_SEG_M|_SEG_B|_SEG_TL|_SEG_BL,
    'n': _SEG_M|_SEG_TL|_SEG_TR|_SEG_BL|_SEG_BR,
    'G': _SEG_T|_SEG_M|_SEG_B|_SEG_TL|_SEG_BL|_SEG_BR,
    'L': _SEG_B|_SEG_TL|_SEG_BL,
    'F': _SEG_T|_SEG_M|_SEG_TL|_SEG_BL,
    'i': _SEG_T|_SEG_B|_SEG_BL,
    'l': _SEG_TL|_SEG_BL,
    'g': _SEG_T|_SEG_M|_SEG_B|_SEG_TR|_SEG_TL|_SEG_BR,
    'S': _SEG_T|_SEG_M|_SEG_B|_SEG_TL|_SEG_BR,
    't': _SEG_T|_SEG_M|_SEG_B|_SEG_TL|_SEG_BL,
    'a': _SEG_T|_SEG_M|_SEG_B|_SEG_TR|_SEG_BL|_SEG_BR,
    ' ': 0,
    'I': _SEG_T|_SEG_B|_SEG_TL|_SEG_BL,
}
_GENERIC_SEGS = _SEG_T|_SEG_M|_SEG_B|_SEG_TL|_SEG_TR|_SEG_BL|_SEG_BR

def _get_segs(ch):
    return _CHAR_MAP.get(ch, _GENERIC_SEGS if ch != ' ' else 0)

def _draw_char_geometry(ch, ox, fy, fz, cw, ch_h):
    t  = 2.8
    hw = cw
    hh = ch_h
    mid_z = fz + hh * 0.5
    top_z = fz + hh
    y1 = fy - t
    y2 = fy + t

    segs = _get_segs(ch)

    def hbar(x1, x2, z):
        glBegin(GL_QUADS)
        glVertex3f(x1, y1, z-t); glVertex3f(x2, y1, z-t)
        glVertex3f(x2, y2, z+t); glVertex3f(x1, y2, z+t)
        glEnd()

    def vbar(x, z1, z2):
        glBegin(GL_QUADS)
        glVertex3f(x-t, y1, z1); glVertex3f(x+t, y1, z1)
        glVertex3f(x+t, y2, z2); glVertex3f(x-t, y2, z2)
        glEnd()

    if segs & _SEG_T:  hbar(ox,       ox+hw, top_z)
    if segs & _SEG_M:  hbar(ox,       ox+hw, mid_z)
    if segs & _SEG_B:  hbar(ox,       ox+hw, fz)
    if segs & _SEG_TL: vbar(ox,       mid_z, top_z)
    if segs & _SEG_TR: vbar(ox+hw,    mid_z, top_z)
    if segs & _SEG_BL: vbar(ox,       fz,    mid_z)
    if segs & _SEG_BR: vbar(ox+hw,    fz,    mid_z)


# ═══════════════════════════════════════════════════════════════════════════════
#  FUELING ANIMATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _local_to_world_xy(lx, ly, sx, sy):
    c = math.cos(SEL_YAW)
    s = math.sin(SEL_YAW)
    return sx + lx*c + ly*s,  sy - lx*s + ly*c


def get_fueling_hand_world():
    wx, wy = _local_to_world_xy(-110.0, 0.0, sel_x, sel_y)
    return wx, wy, 88.0


def get_vehicle_fuel_cap(v):
    vx, vy = v["x"], v["y"]
    if v["type"] == "car":
        return vx + 72, vy - 80, 68
    elif v["type"] == "bike":
        return vx + 0, vy + 20, 75
    else:  # truck
        return vx + 82, vy - 80, 90


def get_seller_target_pos(front_vehicle):
    vx, vy = front_vehicle["x"], front_vehicle["y"]
    vtype  = front_vehicle["type"]

    if vtype == "car":
        return vx + 185.0, vy - 80.0
    elif vtype == "bike":
        return vx + 110.0, vy + 20.0
    else:  # truck
        return vx + 195.0, vy - 80.0


def draw_nozzle_hose(front_vehicle):
    """Draw flexible fuel hose from pump → seller hand → vehicle cap."""
    pnx, pny, pnz = -60.0, 25.0, 92.0
    hx,  hy,  hz  = get_fueling_hand_world()
    fcx, fcy, fcz = get_vehicle_fuel_cap(front_vehicle)

    quad = gluNewQuadric()

    glColor3f(0.12, 0.12, 0.12)
    glLineWidth(5.0)
    glBegin(GL_LINE_STRIP)
    glVertex3f(pnx, pny, pnz)
    glVertex3f((pnx+hx)*0.5, (pny+hy)*0.5, (pnz+hz)*0.5 - 14)
    glVertex3f(hx, hy, hz)
    mid_x = (hx + fcx) * 0.5
    mid_y = (hy + fcy) * 0.5
    mid_z = min(hz, fcz) - 20
    glVertex3f(mid_x, mid_y, mid_z)
    glVertex3f(fcx, fcy, fcz)
    glEnd()
    glLineWidth(1.0)

    glColor3f(0.25, 0.25, 0.28)
    glPushMatrix()
    glTranslatef(fcx, fcy, fcz)
    gluSphere(quad, 7, 8, 8)
    glPopMatrix()
    glColor3f(0.18, 0.18, 0.20)
    draw_box(fcx-5, fcy-4, fcz-9, fcx+5, fcy+4, fcz+2)


def draw_idle_nozzle_at_pump():
    """Draw the nozzle hanging on the pump when not connected."""
    quad = gluNewQuadric()
    glColor3f(0.22, 0.22, 0.26)
    draw_box(-62, 20, 88, -48, 30, 102)
    glColor3f(0.18, 0.18, 0.22)
    draw_box(-60, 21, 78, -50, 29, 90)
    glColor3f(0.12, 0.12, 0.12)
    glLineWidth(4.0)
    glBegin(GL_LINE_STRIP)
    glVertex3f(-55, 25, 92)
    glVertex3f(-55, 25, 110)
    glVertex3f(-30, 25, 118)
    glEnd()
    glLineWidth(1.0)


def draw_3d_fuel_bar(percentage, vtype):
    """Draws a smooth, flicker-free color-changing bar above the vehicle."""
    h = 180 if vtype == "truck" else 120
    if vtype == "bike": h = 150

    width = 100
    thickness = 8
    
    r = 1.0 - percentage
    g = percentage
    b = 0.0
    
    glPushMatrix()
    glTranslatef(-width/2, 0, h)
    
    glColor3f(0.1, 0.1, 0.1)
    draw_box(0, -5, 0, width, 5, thickness)
    
    glColor3f(r, g, b)
    if percentage > 0:
        draw_box(0, -5.5, 0.5, width * percentage, 5.5, thickness - 0.5)
    
    glPopMatrix()


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUND
# ═══════════════════════════════════════════════════════════════════════════════

def get_sky_color():
    """Returns unified sky color for both clear color and sky box."""
    p = max(0.0, min(1.0, (day_light - 0.1) / 0.9))
    r = 0.04 + (0.45 - 0.04) * p
    g = 0.05 + (0.65 - 0.05) * p
    b = 0.15 + (0.85 - 0.15) * p
    return (r, g, b)

def draw_ground():
    # Get unified sky color
    sky_r, sky_g, sky_b = get_sky_color()
    p = max(0.0, min(1.0, (day_light - 0.1) / 0.9))
    
    # Sky box (large cube)
    glColor3f(sky_r, sky_g, sky_b)
    S = 5800
    draw_box(-S, -S, -S, S, S, S)

    # Ground plane with proper day/night lighting
    set_color_lit(0.22, 0.22, 0.25)
    glBegin(GL_QUADS)
    glVertex3f(-2000,-2000,-2); glVertex3f(2000,-2000,-2)
    glVertex3f(2000,2000,-2);   glVertex3f(-2000,2000,-2)
    glEnd()

    # Concrete apron with good visibility
    apron_brightness = 0.45 + (0.75 - 0.45) * p
    glColor3f(apron_brightness, apron_brightness, apron_brightness)
    glBegin(GL_QUADS)
    glVertex3f(-CANOPY_W-35,-CANOPY_D-35,0); glVertex3f(CANOPY_W+35,-CANOPY_D-35,0)
    glVertex3f(CANOPY_W+35,CANOPY_D+35,0);   glVertex3f(-CANOPY_W-35,CANOPY_D+35,0)
    glEnd()

    # Inner concrete
    inner_brightness = 0.52 + (0.82 - 0.52) * p
    glColor3f(inner_brightness, inner_brightness, inner_brightness)
    glBegin(GL_QUADS)
    glVertex3f(-CANOPY_W+15,-CANOPY_D+15,0.5); glVertex3f(CANOPY_W-15,-CANOPY_D+15,0.5)
    glVertex3f(CANOPY_W-15,CANOPY_D-15,0.5);   glVertex3f(-CANOPY_W+15,CANOPY_D-15,0.5)
    glEnd()

    for ox,oy,ow,od in [(-40,-60,80,50),(60,80,70,45),(-80,20,60,40)]:
        glColor3f(0.60,0.60,0.62)
        glBegin(GL_QUADS)
        glVertex3f(ox,oy,1); glVertex3f(ox+ow,oy,1)
        glVertex3f(ox+ow,oy+od,1); glVertex3f(ox,oy+od,1)
        glEnd()

    # Yellow lines
    line_r = 0.70 + (0.94 - 0.70) * p
    line_g = 0.60 + (0.84 - 0.60) * p
    line_b = 0.05 + (0.10 - 0.05) * p
    glColor3f(line_r, line_g, line_b)
    for lx in [-210,210]:
        glBegin(GL_QUADS)
        glVertex3f(lx-5,-CANOPY_D-35,2); glVertex3f(lx+5,-CANOPY_D-35,2)
        glVertex3f(lx+5,CANOPY_D+35,2);  glVertex3f(lx-5,CANOPY_D+35,2)
        glEnd()

    # Road markings
    road_mark_r = 0.55 + (0.85 - 0.55) * p
    road_mark_g = 0.55 + (0.85 - 0.55) * p
    road_mark_b = 0.05 + (0.15 - 0.05) * p
    glColor3f(road_mark_r, road_mark_g, road_mark_b)
    for seg in range(6):
        ys = -2000+seg*260
        glBegin(GL_QUADS)
        glVertex3f(-6,ys,1); glVertex3f(6,ys,1)
        glVertex3f(6,ys+160,1); glVertex3f(-6,ys+160,1)
        glEnd()

    # Curb edges
    curb_bright = 0.55 + (0.95 - 0.55) * p
    glColor3f(curb_bright, curb_bright, curb_bright)
    cw=10; cy1=CANOPY_D+35; cx1=CANOPY_W+35
    draw_box(-cx1-cw,-cy1-cw,0, cx1+cw,-cy1,8)
    draw_box(-cx1-cw,cy1,0,     cx1+cw,cy1+cw,8)
    draw_box(-cx1-cw,-cy1-cw,0,-cx1,cy1+cw,8)
    draw_box(cx1,-cy1-cw,0,     cx1+cw,cy1+cw,8)

    # Road asphalt
    asphalt_r = 0.15 + (0.28 - 0.15) * p
    asphalt_g = 0.15 + (0.28 - 0.15) * p
    asphalt_b = 0.16 + (0.30 - 0.16) * p
    glColor3f(asphalt_r, asphalt_g, asphalt_b)
    glBegin(GL_QUADS)
    glVertex3f(ROAD_X-120,-2000,0); glVertex3f(ROAD_X+120,-2000,0)
    glVertex3f(ROAD_X+120,-CANOPY_D-35,0); glVertex3f(ROAD_X-120,-CANOPY_D-35,0)
    glEnd()

    # Road side lines
    side_line_r = 0.55 + (0.90 - 0.55) * p
    side_line_g = 0.55 + (0.90 - 0.55) * p
    side_line_b = 0.05 + (0.20 - 0.05) * p
    glColor3f(side_line_r, side_line_g, side_line_b)
    glBegin(GL_QUADS)
    glVertex3f(ROAD_X-118,-2000,1); glVertex3f(ROAD_X-112,-2000,1)
    glVertex3f(ROAD_X-112,-CANOPY_D-35,1); glVertex3f(ROAD_X-118,-CANOPY_D-35,1)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(ROAD_X+112,-2000,1); glVertex3f(ROAD_X+118,-2000,1)
    glVertex3f(ROAD_X+118,-CANOPY_D-35,1); glVertex3f(ROAD_X+112,-CANOPY_D-35,1)
    glEnd()

    # Dashed center line
    dash_color_r = 0.60 + (0.92 - 0.60) * p
    dash_color_g = 0.60 + (0.92 - 0.60) * p
    dash_color_b = 0.05 + (0.15 - 0.05) * p
    glColor3f(dash_color_r, dash_color_g, dash_color_b)
    for seg in range(10):
        ys = -2000+seg*180
        if ys > -CANOPY_D-35: break
        glBegin(GL_QUADS)
        glVertex3f(ROAD_X-4,ys,1); glVertex3f(ROAD_X+4,ys,1)
        glVertex3f(ROAD_X+4,ys+110,1); glVertex3f(ROAD_X-4,ys+110,1)
        glEnd()


# ═══════════════════════════════════════════════════════════════════════════════
#  CANOPY
# ═══════════════════════════════════════════════════════════════════════════════
def draw_canopy():
    set_color_lit(0.09,0.12,0.44)
    draw_box(-CANOPY_W,-CANOPY_D,CANOPY_H, CANOPY_W,CANOPY_D,CANOPY_H+ROOF_T)

    t=15
    glColor3f(0.91,0.91,0.91)
    draw_box(-CANOPY_W,-CANOPY_D-t,CANOPY_H-14, CANOPY_W,-CANOPY_D,CANOPY_H)
    draw_box(-CANOPY_W,CANOPY_D,CANOPY_H-14,    CANOPY_W,CANOPY_D+t,CANOPY_H)
    draw_box(-CANOPY_W-t,-CANOPY_D,CANOPY_H-14,-CANOPY_W,CANOPY_D,CANOPY_H)
    draw_box(CANOPY_W,-CANOPY_D,CANOPY_H-14,    CANOPY_W+t,CANOPY_D,CANOPY_H)

    set_color_lit(0.06,0.08,0.35)
    draw_box(-320,-CANOPY_D-t-2, CANOPY_H-12,
              320,-CANOPY_D-t-16, CANOPY_H+ROOF_T+4)

    # Sign fascia
    glColor3f(1.0, 0.84, 0.0)
    bx1,bx2 = -320, 320
    by1,by2 = -CANOPY_D-t-2, -CANOPY_D-t-16
    bz1,bz2 = CANOPY_H-12, CANOPY_H+ROOF_T+4
    draw_box(bx1,by1,bz2-3, bx2,by2,bz2)
    draw_box(bx1,by1,bz1,   bx2,by2,bz1+3)
    draw_box(bx1,by1,bz1,   bx1+4,by2,bz2)
    draw_box(bx2-4,by1,bz1, bx2,by2,bz2)

    # Ceiling lights
    set_color_lit(0.96,0.96,0.88)
    for ys in [-280,-140,0,140,280]:
        draw_box(-CANOPY_W+55,ys-10,CANOPY_H-5, CANOPY_W-55,ys+10,CANOPY_H)

    # Pillars
    pw=22
    pillar_locs=[(-460,-345),(460,-345),(-460,345),(460,345),(-460,0),(460,0)]
    for px,py in pillar_locs:
        glColor3f(0.87,0.87,0.87)
        draw_box(px-pw,py-pw,0, px+pw,py+pw,CANOPY_H)
        glColor3f(0.65,0.65,0.65)
        draw_box(px-pw-3,py-pw-3,CANOPY_H-9, px+pw+3,py+pw+3,CANOPY_H)
        glColor3f(0.60,0.60,0.60)
        draw_box(px-pw-4,py-pw-4,0, px+pw+4,py+pw+4,12)

    # Sign board
    glColor3f(1.0,0.52,0.0)
    draw_box(-CANOPY_W+80,-CANOPY_D+8,CANOPY_H-42, CANOPY_W-80,-CANOPY_D+24,CANOPY_H-26)
    glColor3f(1.0,1.0,1.0)
    for xs in range(-400,400,60):
        draw_box(xs,-CANOPY_D+9,CANOPY_H-40, xs+32,-CANOPY_D+23,CANOPY_H-30)

    draw_station_name_on_fascia()


# ═══════════════════════════════════════════════════════════════════════════════
#  PRICE SIGN
# ═══════════════════════════════════════════════════════════════════════════════
def draw_entrance_gate():
    gate_y = -450  # Make it close to the pump station
    gate_x = ROAD_X
    
    # Sign Open / Closed on the corner of the roof of the pump
    sign_color = (0.2, 0.9, 0.2) if station_open else (0.9, 0.1, 0.1)
    sign_text = "OPEN" if station_open else "CLOSED"
    glColor3f(0.1, 0.1, 0.1)
    
    sx = -CANOPY_W + 50
    sy = -CANOPY_D + 50
    sz = CANOPY_H + ROOF_T
    draw_box(sx - 60, sy - 10, sz, sx + 60, sy + 10, sz + 60)
    glColor3f(*sign_color)
    draw_box(sx - 55, sy - 15, sz + 10, sx + 55, sy + 15, sz + 50)
    _draw_3d_text_overlay(sx - 35, sy - 26, sz + 25, sign_text)

    # Gate base
    glColor3f(0.9, 0.6, 0.1)
    draw_box(gate_x - 130, gate_y - 10, 0, gate_x - 110, gate_y + 10, 50)
    
    # Gate arm (rotates to block the road)
    glPushMatrix()
    glTranslatef(gate_x - 120, gate_y, 40)
    glRotatef(-gate_angle, 0, 1, 0)
    glColor3f(0.8, 0.1, 0.1)
    draw_box(-5, -5, -5, 260, 5, 5)
    glPopMatrix()

def draw_price_sign():
    glColor3f(0.26,0.26,0.30)
    draw_box(390,-394,0, 410,-376,350)
    glColor3f(0.07,0.09,0.36)
    draw_box(340,-398,148, 462,-378,342)
    glColor3f(0.88,0.88,0.88)
    draw_box(340,-399,148, 462,-380,151)
    draw_box(340,-399,339, 462,-380,342)
    draw_box(340,-399,148, 343,-380,342)
    draw_box(459,-399,148, 462,-380,342)
    glColor3f(0.78,0.10,0.12)
    draw_box(356,-399,302, 447,-381,335)
    glColor3f(1.0,1.0,1.0)
    draw_box(366,-400,312, 437,-382,328)
    glColor3f(0.78,0.10,0.12)
    draw_box(376,-401,318, 427,-383,322)
    row_data=[((0.10,0.65,0.18),260),((0.82,0.14,0.14),218),((0.80,0.54,0.08),176)]
    for (rc,rz) in row_data:
        glColor3f(*rc)
        draw_box(346,-399,rz, 460,-381,rz+34)
        glColor3f(0.92,0.92,0.92)
        draw_box(385,-400,rz+4, 458,-382,rz+28)
        glColor3f(0.06,0.06,0.06)
        for dxs in [390,405,415,430]:
            draw_box(dxs,-401,rz+6, dxs+8,-383,rz+26)
    glColor3f(0.78,0.10,0.12)
    draw_box(356,-399,153, 447,-381,170)
    glColor3f(0.35,0.35,0.35)
    draw_box(375,-400,0, 425,-375,12)



#MOHSINA
# This section contains helper functions for managing the simulation clock, recording statistics, and handling cheat mode.

def get_time_string():
    """Return formatted time string HH:MM"""
    hours = int(simulation_time_hours) % 24
    minutes = int(simulation_time_minutes)
    return f"{hours:02d}:{minutes:02d}"

def update_simulation_time(dt):
    """Update the simulation clock"""
    global simulation_time_hours, simulation_time_minutes
    
    total_sim_seconds = dt * time_scale
    simulation_time_minutes += total_sim_seconds / 60.0
    
    if simulation_time_minutes >= 60:
        simulation_time_hours += simulation_time_minutes // 60
        simulation_time_minutes %= 60
    
    if simulation_time_hours >= 24:
        simulation_time_hours %= 24

def reset_daily_statistics():
    """Reset daily counters"""
    global daily_vehicles_served, daily_fuel_dispensed, daily_revenue
    global time_since_last_reset, cheat_cars_served_this_cycle
    daily_vehicles_served = 0
    daily_fuel_dispensed = 0.0
    daily_revenue = 0.0
    time_since_last_reset = 0.0
    cheat_cars_served_this_cycle = 0
    print("  ✓ DAILY STATISTICS RESET – New day started!")

def record_vehicle_served(vehicle_type, fuel_amount):
    """Record a vehicle being served and calculate revenue"""
    global daily_vehicles_served, daily_fuel_dispensed, daily_revenue
    global lifetime_vehicles_served, lifetime_fuel_dispensed, lifetime_revenue
    global active_receipt
    
    tank_size = FUEL_LIMITS.get(vehicle_type, 10.0)
    percentage_filled = min(fuel_amount / tank_size, 1.0)
    revenue = PRICE_PER_FULL_TANK * percentage_filled
    
    daily_vehicles_served += 1
    daily_fuel_dispensed += fuel_amount
    daily_revenue += revenue
    
    lifetime_vehicles_served += 1
    lifetime_fuel_dispensed += fuel_amount
    lifetime_revenue += revenue
    
    time_str = get_time_string()
    active_receipt = Receipt(vehicle_type, fuel_amount, revenue, time_str)
    
    money_effects.append(MoneyEffect(sel_x, sel_y, 150, revenue))
    
    print(f"  ✓ Vehicle served: {vehicle_type.upper()} | "
          f"Fuel: {fuel_amount:.1f}L | Revenue: ${revenue:.2f}")


#MOHSINA
# ═══════════════════════════════════════════════════════════════════════════════
#   3D Display Boards (Statistics Board & Clock)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_3d_statistics_board():
    """Draw statistics board showing daily vehicles and fuel dispensed"""
    board_x = -CANOPY_W - 80
    board_y = 0
    board_z = 200
    
    # Board frame  #
    glColor3f(0.05, 0.05, 0.15)
    draw_box(board_x +100, board_y - 80, board_z, board_x + 10, board_y + 80, board_z + 160)
    
    # Border
    glColor3f(1.0, 0.85, 0.0)
    draw_box(board_x - 12, board_y - 82, board_z - 2, 
             board_x + 12, board_y + 82, board_z + 162)
    
    # Display area
    glColor3f(0.0, 0.0, 0.0)
    draw_box(board_x - 8, board_y - 78, board_z + 2, 
             board_x + 8, board_y + 78, board_z + 158)
    
    # Section 1: Vehicles (top)
    glColor3f(0.1, 1.0, 0.1)
    draw_box(board_x - 9, board_y - 70, board_z + 85, 
             board_x + 9, board_y + 70, board_z + 150)
    
    # Section 2: Liters (bottom)
    glColor3f(0.1, 0.6, 1.0)
    draw_box(board_x - 9, board_y - 70, board_z + 10, 
             board_x + 9, board_y + 70, board_z + 75)
             
    # Render aligned text to the block face
    _draw_board_text(board_x-50, board_y, board_z)

def _draw_board_text(bx, by, bz):
    # Perfect text vertical alignment using fixed 'by - 50' start coordinate
    vehicles_text = f"CARS: {daily_vehicles_served}"
    _draw_3d_text_overlay(bx , by +50, bz + 110, vehicles_text)
    
    liters_text = f"LITERS: {daily_fuel_dispensed:.1f}"
    _draw_3d_text_overlay(bx, by + 50, bz + 75, liters_text)





def draw_3d_clock():
    """Draw 3D digital clock on station"""
    clock_x = 400
    clock_y = 500
    clock_z = 200

    time_str = get_time_string()
    _draw_3d_text_overlay(clock_x + 20, clock_y + 25, clock_z + 207, time_str)    

    # Clock frame
    glColor3f(1, 1, 1)
    draw_box(clock_x - 50, clock_y - 100, clock_z +200,clock_x + 50, clock_y + 20, clock_z + 220)
    

def _draw_3d_text_overlay(x, y, z, text):

    glColor3f(0.0, 0.0, 0.0)  # black text
    glRasterPos3f(x, y, z)

    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))




def draw_corner_hud_statistics():
    #Draw corner HUD with revenue information
    hud_x = WIN_W - 380
    hud_y = WIN_H - 28
    
    draw_text(hud_x, hud_y,
              f"Daily Revenue: ${daily_revenue:.2f}",
              color=(0.20, 1.00, 0.20))
    
    draw_text(hud_x, hud_y - 24,
              f"Lifetime Revenue: ${lifetime_revenue:.2f}",
              color=(1.00, 0.85, 0.00))
    
    draw_text(hud_x, hud_y - 48,
              f"Served Today: {daily_vehicles_served} | Lifetime: {lifetime_vehicles_served}",
              color=(0.40, 0.90, 1.00))

def draw_receipt_display():
    #Drawing receipt when vehicle leaves
    global active_receipt
    
    if active_receipt is None:
        return
    
    active_receipt.elapsed += 0.016
    
    if active_receipt.elapsed >= active_receipt.display_time:
        active_receipt = None
        return
    
    receipt_w = 260
    receipt_h = 140

    receipt_x = WIN_W - receipt_w - 10   # closer to right
    receipt_y = 10                       # bottom margin
    
    # (DARK TEXT ON LIGHT BACKGROUND)
    text_y = receipt_y + receipt_h - 20

    draw_text(receipt_x + 60, text_y, "FUEL RECEIPT", color=(0,0,0))
    draw_text(receipt_x + 10, text_y - 20,f"Vehicle : {active_receipt.vehicle_type}",color=(0,0,0))
    draw_text(receipt_x + 10, text_y - 40,f"Fuel    : {active_receipt.fuel_amount:.2f} L",color=(0,0,0))
    draw_text(receipt_x + 10, text_y - 60,f"Price   : ${active_receipt.price:.2f}",color=(0,0,0))
    draw_text(receipt_x + 10, text_y - 80, f"Time    : {active_receipt.time}",color=(0,0,0))
    draw_text(receipt_x + 10, text_y - 100,"------------------------",color=(0,0,0))
    draw_text(receipt_x + 60, text_y - 120,"THANK YOU!",color=(0,0,0))



    _enter_ortho()
    
    # receipt background (cream color)
    glColor3f(0.95, 0.95, 0.85)
    glBegin(GL_QUADS)
    glVertex2f(receipt_x, receipt_y)
    glVertex2f(receipt_x + receipt_w, receipt_y)
    glVertex2f(receipt_x + receipt_w, receipt_y + receipt_h)
    glVertex2f(receipt_x, receipt_y + receipt_h)
    glEnd()
    
    #  border (dark)
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(3.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(receipt_x, receipt_y)
    glVertex2f(receipt_x + receipt_w, receipt_y)
    glVertex2f(receipt_x + receipt_w, receipt_y + receipt_h)
    glVertex2f(receipt_x, receipt_y + receipt_h)
    glEnd()
    glLineWidth(1.0)
    
    _exit_ortho()
    


def draw_money_effects():
    """Draw animated money effects after positions are updated"""
    quad = gluNewQuadric()
    for effect in money_effects:
        progress = effect.elapsed / effect.life_time
        brightness = max(0.0, 1.0 - progress)
        
        # Draw the coin
        glPushMatrix()
        glTranslatef(effect.x, effect.y, effect.z)
        glColor3f(brightness, brightness * 0.9, 0.0)
        gluSphere(quad, 12, 12, 12)  # Make coins bigger!
        glPopMatrix()
#MOHSINA
# ═══════════════════════════════════════════════════════════════════════════════
# Cheat Mode (Auto-serving with day/night cycle)
# ═══════════════════════════════════════════════════════════════════════════════

def toggle_cheat_mode():
    """Toggle cheat mode on/off"""
    global cheat_mode_active, cheat_auto_serve_timer, cheat_cars_served_this_cycle
    cheat_mode_active = not cheat_mode_active
    cheat_auto_serve_timer = 0.0
    cheat_cars_served_this_cycle = 0
    
    status = "ENABLED ⚡" if cheat_mode_active else "DISABLED"
    print(f"  🎮 CHEAT MODE {status}")
    print(f"     Auto-serves every {CHEAT_AUTO_SERVE_INTERVAL}s")
    print(f"     After {CHEAT_RESET_AT_CARS} cars → Night")
    print(f"     Morning → Auto day-reset")

def update_cheat_mode(dt):
    global cheat_mode_active, cheat_auto_serve_timer, cheat_cars_served_this_cycle
    global nozzle_connected, seller_fueling, seller_at_vehicle, seller_walking_backward
    global day_light, fuel_dispensed, fuel_limit_reached
    
    if not cheat_mode_active:
        return
    
    cheat_auto_serve_timer += dt
    
    if cheat_auto_serve_timer >= CHEAT_AUTO_SERVE_INTERVAL and vehicles:
        if not nozzle_connected and not seller_fueling and vehicles[0]["state"] == "waiting":
            front_veh = vehicles[0]
            snap_seller_to_vehicle(front_veh)
            nozzle_connected = True
            seller_fueling = True
            fuel_dispensed = 0.0
            fuel_limit_reached = False
            front_veh["state"] = "fuelling"
            cheat_auto_serve_timer = 0.0
            print(f"  🤖 [Cheat] Auto-serving {front_veh['type']}...")
    
    if nozzle_connected and vehicles and fuel_dispensed >= get_fuel_limit(vehicles[0]["type"]):
        record_vehicle_served(vehicles[0]["type"], fuel_dispensed)
        cheat_cars_served_this_cycle += 1
        
        nozzle_connected = False
        seller_fueling = False
        seller_at_vehicle = False
        seller_walking_backward = True
        vehicles[0]["state"] = "leaving"
    
    if cheat_cars_served_this_cycle >= CHEAT_RESET_AT_CARS:
        if not hasattr(update_cheat_mode, 'morning_transition'):
            update_cheat_mode.morning_transition = False

        if not update_cheat_mode.morning_transition:
            day_light = max(0.1, day_light - dt * 0.15)
            if day_light <= 0.15:
                if not hasattr(update_cheat_mode, 'night_start_time'):
                    update_cheat_mode.night_start_time = time.time()
                
                if time.time() - update_cheat_mode.night_start_time > 5:
                    update_cheat_mode.morning_transition = True
                    update_cheat_mode.night_start_time = None
        else:
            day_light = min(1.0, day_light + dt * 0.15)
            if day_light >= 1.0:
                reset_daily_statistics()
                cheat_cars_served_this_cycle = 0
                update_cheat_mode.morning_transition = False
                print("[Cheat MODE] Morning! Day auto-reset completed!")

def manual_reset_daily_stats_key_handler():
    """Manual reset with R key"""
    reset_daily_statistics()
    print("  Manual daily reset triggered!")






# ═══════════════════════════════════════════════════════════════════════════════
#  FUEL PUMP
# ═══════════════════════════════════════════════════════════════════════════════
def draw_fuel_pump():
    quad=gluNewQuadric()
    glColor3f(0.56,0.58,0.61)
    draw_box(-65,-100,0, 65,100,14)
    glColor3f(0.67,0.69,0.72)
    draw_box(-60,-95,14, 60,95,17)
    glColor3f(0.94,0.84,0.0)
    draw_box(-65,-100,8, -60,-95,14)
    draw_box(60,-100,8, 65,-95,14)
    set_color_lit(1.00,0.76,0.03)
    draw_box(-36,-31,17, 36,31,172)
    glColor3f(0.88,0.66,0.02)
    draw_box(-36,-31,17, -34,31,172)
    draw_box(34,-31,17,  36,31,172)
    draw_box(-36,29,17, 36,31,172)
    glColor3f(0.90,0.65,0.02)
    draw_box(-39,-34,172, 39,34,245)
    glColor3f(0.78,0.56,0.01)
    draw_box(-34,-29,245, 34,29,254)
    glColor3f(0.03,0.03,0.03)
    draw_box(-26,-32,82, 26,-34,158)
    glColor3f(0.04,0.90,0.18)
    for zd in [90,108,126,143]:
        draw_box(-21,-32.2,zd, 21,-34.2,zd+12)
    glColor3f(0.20,0.20,0.20)
    draw_box(-26,-32,140, 26,-34,142)
    glColor3f(0.35,0.35,0.35)
    for row in range(3):
        for col in range(3):
            bx=-16+col*13
            draw_box(bx,-32.2,52+row*11, bx+10,-34.2,52+row*11+8)
    for i,gc in enumerate([(0.95,0.85,0.0),(1.0,0.45,0.0),(0.85,0.10,0.10)]):
        glColor3f(*gc)
        draw_box(-24+i*17,-32.2,27, -24+i*17+13,-34.2,42)
    glColor3f(1.0,0.38,0.0)
    draw_box(-24,-33,194, 24,-35,238)
    glColor3f(0.96,0.96,0.96)
    draw_box(-16,-33.5,202, 16,-35.5,230)
    glColor3f(1.0,0.38,0.0)
    draw_box(-8,-34,210, 8,-36,222)
    glColor3f(0.18,0.18,0.18)
    draw_box(-36,-7,120, -60,7,124)
    glColor3f(0.22,0.22,0.22)
    glPushMatrix(); glTranslatef(-60,0,120); glRotatef(90,1,0,0)
    gluCylinder(quad,6,6,40,10,1); glPopMatrix()
    glColor3f(0.30,0.30,0.30)
    glPushMatrix(); glTranslatef(-60,25,92); glRotatef(-42,1,0,0)
    gluCylinder(quad,5,3,38,10,1); glPopMatrix()
    glColor3f(0.40,0.40,0.40)
    glPushMatrix(); glTranslatef(-60,25,92)
    gluSphere(quad,7,10,10); glPopMatrix()
    glColor3f(1.0,1.0,1.0)
    glPushMatrix(); glTranslatef(0,-33,60)
    gluSphere(quad,10,14,14); glPopMatrix()
    draw_box(-4,-33.5,68, 4,-34.5,78)
    for bx,by in [(-92,0),(92,0),(0,-118),(0,118)]:
        glColor3f(1.0,0.80,0.0)
        glPushMatrix(); glTranslatef(bx,by,0)
        draw_manual_solid_cylinder(10,10,74,14,lw=3.5); glPopMatrix()
        glColor3f(0.07,0.07,0.07)
        for bz in [14,38,60]:
            glPushMatrix(); glTranslatef(bx,by,bz)
            draw_manual_solid_cylinder(11,11,10,14,lw=2.0); glPopMatrix()
        glColor3f(0.94,0.84,0.0)
        glPushMatrix(); glTranslatef(bx,by,74)
        gluSphere(quad,11,10,10); glPopMatrix()

    if not nozzle_connected:
        draw_idle_nozzle_at_pump()


# ═══════════════════════════════════════════════════════════════════════════════
#  SELLER
# ═══════════════════════════════════════════════════════════════════════════════
def draw_seller(fueling=False, front_vehicle=None):
    quad=gluNewQuadric()
    glPushMatrix()
    glTranslatef(sel_x, sel_y, 0)
    glRotatef(-math.degrees(SEL_YAW),0,0,1)

    # Legs
    glColor3f(0.05, 0.05, 0.15)
    draw_box(-22, -15, 0, -4, 15, 47)
    glColor3f(0.05, 0.05, 0.15)
    draw_box(4, -15, 0, 22, 15, 47)

    glColor3f(0.05,0.05,0.05)
    draw_box(-22,-15,44, 22,15,53)
    glColor3f(0.65,0.55,0.20)
    draw_box(-6,-15.5,45, 6,16.5,52)

    glColor3f(0.08,0.05,0.03)
    draw_box(-20,-15,0, -4,15,10)
    draw_box(4,-15,0,   20,15,10)

    # Torso
    glColor3f(1.0,0.50,0.0)
    glPushMatrix(); glTranslatef(0,0,68); glScalef(0.80,0.48,1.30)
    glutSolidCube(55); glPopMatrix()
    glColor3f(0.85,0.42,0.0)
    draw_box(-2,-15.5,54, 2,16.5,96)

    glColor3f(0.92,0.92,0.16)
    draw_box(-23,-15,70, 23,-17,79)
    draw_box(-23,15,70,  23,17,79)
    draw_box(-23,-15,82, 23,-17,91)
    draw_box(-23,15,82,  23,17,91)

    # Arms
    glColor3f(0.84,0.63,0.43)
    if fueling and front_vehicle is not None:
        # Left arm raised for fueling
        glPushMatrix(); glTranslatef(-34,0,95)
        glRotatef(90, 0,1,0)
        glRotatef(-18, 1,0,0)
        draw_manual_solid_cylinder(8,7,80,14,lw=2.0); glPopMatrix()

        glColor3f(0.84,0.63,0.43)
        glPushMatrix(); glTranslatef(-116,-18,84)
        gluSphere(quad,9,10,10); glPopMatrix()

        glColor3f(0.22,0.22,0.26)
        draw_box(-124,-22,76, -109,-13,92)
        glColor3f(0.18,0.18,0.22)
        draw_box(-122,-21,68, -111,-14,78)

        # Right arm lowered
        glColor3f(0.84,0.63,0.43)
        glPushMatrix(); glTranslatef(34,0,95)
        glRotatef(95,0,1,0); glRotatef(-30,1,0,0)
        draw_manual_solid_cylinder(8,7,68,14,lw=2.0); glPopMatrix()
        glPushMatrix(); glTranslatef(96,-28,80)
        gluSphere(quad,9,10,10); glPopMatrix()
    else:
        # Both arms at sides
        glPushMatrix(); glTranslatef(-34,0,94); glRotatef(160,1,0,0)
        draw_manual_solid_cylinder(8,7,50,14,lw=2.0); glPopMatrix()
        glPushMatrix(); glTranslatef(-34,18,54)
        gluSphere(quad,8,10,10); glPopMatrix()

        glPushMatrix(); glTranslatef(34,0,95)
        glRotatef(95,0,1,0); glRotatef(-30,1,0,0)
        draw_manual_solid_cylinder(8,7,68,14,lw=2.0); glPopMatrix()
        glPushMatrix(); glTranslatef(96,-28,80)
        gluSphere(quad,9,10,10); glPopMatrix()

    # Neck and Head
    glColor3f(0.84,0.63,0.43)
    glPushMatrix(); glTranslatef(0,0,103)
    gluCylinder(quad,9,10,14,12,1); glPopMatrix()

    glColor3f(0.84,0.63,0.43)
    glPushMatrix(); glTranslatef(0,0,122)
    gluSphere(quad,20,16,16); glPopMatrix()

    glColor3f(0.15,0.10,0.05)
    glPushMatrix(); glTranslatef(-7,-19,126)
    gluSphere(quad,4,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(7,-19,126)
    gluSphere(quad,4,8,8); glPopMatrix()

    glColor3f(0.18,0.10,0.02)
    glPushMatrix(); glTranslatef(0,0,134); glScalef(1.0,1.0,0.42)
    gluSphere(quad,22,16,16); glPopMatrix()

    glColor3f(1.0,0.38,0.0)
    glPushMatrix(); glTranslatef(0,0,138); glScalef(1.16,1.16,0.54)
    gluSphere(quad,23,16,16); glPopMatrix()

    glColor3f(0.88,0.32,0.0)
    glPushMatrix(); glTranslatef(0,-16,132); glScalef(0.70,0.35,0.22)
    gluSphere(quad,28,12,12); glPopMatrix()

    glPopMatrix()

    if fueling and front_vehicle is not None:
        draw_nozzle_hose(front_vehicle)


# ═══════════════════════════════════════════════════════════════════════════════
#  VEHICLE DRAWERS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_wheel(r=14):
    quad = gluNewQuadric()
    glColor3f(0.10,0.10,0.10)
    glPushMatrix(); glRotatef(90,1,0,0)
    gluCylinder(quad,r,r,12,16,1)
    gluSphere(quad, r, 16, 16)
    glTranslatef(0,0,12); gluSphere(quad, r, 16, 16)
    glPopMatrix()
    glColor3f(0.65,0.65,0.65)
    glPushMatrix(); glRotatef(90,1,0,0)
    gluCylinder(quad,r*0.35,r*0.35,14,8,1); glPopMatrix()
    
def draw_bike(color):
    quad = gluNewQuadric()
    r, g, b = color
    glColor3f(r,g,b)
    draw_box(-12,-60,30, 12,60,75)
    glColor3f(r*0.85,g*0.85,b*0.85)
    draw_box(-14,-28,68, 14,20,90)
    glColor3f(0.15,0.15,0.15)
    draw_box(-12,-50,82, 12,10,90)
    glColor3f(0.55,0.55,0.55)
    draw_box(-20,18,88, 20,26,96)
    draw_box(-16,18,78, -12,26,96)
    draw_box(12,18,78, 16,26,96)
    glColor3f(0.55,0.55,0.55)
    draw_box(-6,34,20, 6,56,70)
    glColor3f(0.30,0.30,0.30)
    draw_box(-16,-20,22, 16,20,55)
    glColor3f(0.50,0.50,0.50)
    glPushMatrix(); glTranslatef(-18,0,28); glRotatef(90,0,1,0)
    gluCylinder(quad,5,3,8,8,1); glPopMatrix()
    glPushMatrix(); glTranslatef(0,50,18); draw_wheel(18); glPopMatrix()
    glPushMatrix(); glTranslatef(0,-50,18); draw_wheel(18); glPopMatrix()
    glColor3f(1.0,0.95,0.60)
    glPushMatrix(); glTranslatef(0,62,52); gluSphere(quad,9,8,8); glPopMatrix()
    glColor3f(0.20,0.30,0.75)
    draw_box(-14,-30,82, 14,10,128)
    glColor3f(r,g,b)
    glPushMatrix(); glTranslatef(0,-10,138)
    gluSphere(quad,18,12,12); glPopMatrix()
    glColor3f(0.20,0.30,0.75)
    draw_box(-22,-8,100, -14,22,112)
    draw_box(14,-8,100,   22,22,112)


def draw_car(color):
    quad = gluNewQuadric()
    r, g, b = color
    glColor3f(r,g,b)
    draw_box(-70,-120,15, 70,120,68)
    glColor3f(r*0.80,g*0.80,b*0.80)
    draw_box(-58,-80,68, 58,75,118)
    glColor3f(r*0.90,g*0.90,b*0.90)
    draw_box(-68,75,48, 68,120,68)
    draw_box(-68,-120,48, 68,-82,68)
    glColor3f(0.35,0.45,0.65)
    draw_box(-56,-76,72, 56,72,114)
    glColor3f(r*0.70,g*0.70,b*0.70)
    draw_box(-58,-76,68, -52,72,118)
    draw_box(52,-76,68,   58,72,118)
    draw_box(-58,-4,68,   58,2,118)
    glColor3f(0.15,0.15,0.15)
    draw_box(-45,116,28, 45,122,56)
    glColor3f(0.80,0.80,0.80)
    for gx in range(-40,44,12):
        draw_box(gx,116,32, gx+7,122,52)
    glColor3f(1.0,0.95,0.60)
    glPushMatrix(); glTranslatef(-48,118,48); gluSphere(quad,10,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(48,118,48);  gluSphere(quad,10,8,8); glPopMatrix()
    glColor3f(0.90,0.10,0.10)
    glPushMatrix(); glTranslatef(-52,-118,46); gluSphere(quad,9,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(52,-118,46);  gluSphere(quad,9,8,8); glPopMatrix()
    for wx,wy in [(-72,88),(72,88),(-72,-88),(72,-88)]:
        glPushMatrix(); glTranslatef(wx,wy,18); draw_wheel(20); glPopMatrix()
    glColor3f(r*0.60,g*0.60,b*0.60)
    draw_box(-70,-20,20, -68,-18,64)
    draw_box(68,-20,20,   70,-18,64)


def draw_truck(color):
    quad = gluNewQuadric()
    r, g, b = color
    glColor3f(r,g,b)
    draw_box(-80,-240,15, 80,60,170)
    glColor3f(r*0.75,g*0.75,b*0.75)
    draw_box(-80,-240,165, 80,60,172)
    glColor3f(r*0.88,g*0.88,b*0.88)
    draw_box(-78,60,15, 78,175,155)
    glColor3f(0.35,0.50,0.70)
    draw_box(-70,62,85, 70,172,148)
    glColor3f(r*0.70,g*0.70,b*0.70)
    draw_box(-78,60,82, -70,174,155)
    draw_box(70,60,82,   78,174,155)
    glColor3f(0.25,0.25,0.28)
    draw_box(-76,162,15, 76,178,78)
    glColor3f(0.60,0.60,0.62)
    draw_box(-74,164,18, 74,176,75)
    glColor3f(1.0,0.95,0.60)
    glPushMatrix(); glTranslatef(-58,174,55); gluSphere(quad,12,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(58,174,55);  gluSphere(quad,12,8,8); glPopMatrix()
    glColor3f(0.40,0.40,0.40)
    glPushMatrix(); glTranslatef(70,30,155)
    gluCylinder(quad,7,5,60,8,1); glPopMatrix()
    for wx,wy in [(-88,130),(88,130),(-88,-80),(88,-80),(-88,-180),(88,-180)]:
        glPushMatrix(); glTranslatef(wx,wy,20); draw_wheel(26); glPopMatrix()
    glColor3f(r*0.65,g*0.65,b*0.65)
    draw_box(-80,-240,15, -78,-80,170)
    draw_box(78,-240,15,   80,-80,170)
    draw_box(-80,-240,92,  80,-240+2,94)
    glColor3f(0.85,0.10,0.10)
    glPushMatrix(); glTranslatef(-70,-242,55); gluSphere(quad,11,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(70,-242,55);  gluSphere(quad,11,8,8); glPopMatrix()


def draw_vehicle(v):
    glPushMatrix()
    glTranslatef(v["x"], v["y"], 0)
    
    if v["type"] == "bike":
        draw_bike(v["color"])
    elif v["type"] == "car":
        draw_car(v["color"])
    else:
        draw_truck(v["color"])
    
    # Draw the driver
    anim = v.get("exit_anim", 0.0)
    
    glPushMatrix()
    if anim < 0.1:
        if v["type"] == "bike":
            glTranslatef(0, -10, 45)
            draw_human(is_standing=False)
    else:
        side_offset = 120 * anim
        glTranslatef(side_offset, -20 * anim, 0)
        draw_human(is_standing=True)
    glPopMatrix()
    
    if v["y"] > ROAD_Y_ENTRY + 300:
        draw_3d_fuel_bar(v.get("fuel_pct", 0.0), v["type"])
        
    glPopMatrix()


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTROLLED FUEL FILLING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

def get_fuel_limit(vtype):
    """Return the fuel limit in litres for a given vehicle type."""
    return FUEL_LIMITS.get(vtype, 10.0)


def update_fuel_dispensing(dt, front_vehicle):
    """
    Update fuel_dispensed for the current fueling session.
    Returns True if the fuel limit has just been reached (auto-disconnect).
    """
    global fuel_dispensed, fuel_limit_reached, fuel_limit_msg_timer

    if not nozzle_connected or front_vehicle is None:
        return False

    limit = get_fuel_limit(front_vehicle["type"])
    if fuel_dispensed >= limit:
        return False   # already at limit, caller handles auto-disconnect

    fuel_dispensed += FUEL_RATE * dt
    if fuel_dispensed >= limit:
        fuel_dispensed = limit
        fuel_limit_reached  = True
        fuel_limit_msg_timer = 4.0   # show message for 4 seconds
        return True   # signal auto-disconnect

    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  QUEUE / SIMULATION UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

def vehicle_length(vtype):
    if vtype == "bike":  return 130
    if vtype == "car":   return 260
    return 470


def update_simulation(dt):
    global spawn_timer, fuel_timer, vehicles
    global sel_x, sel_y, seller_walk_t
    global seller_walking_backward, seller_at_vehicle
    global nozzle_connected, seller_fueling
    global fuel_dispensed, fuel_limit_reached, fuel_limit_msg_timer
    global station_open, gate_angle

    spawn_timer += dt

    if spawn_timer >= SPAWN_INTERVAL and len(vehicles) < 6:
        new_veh = make_vehicle()
        if not station_open:
            new_veh["state"] = "leaving_side"
        vehicles.append(new_veh)
        spawn_timer = 0.0

    # Tick down the "tank full" message timer
    if fuel_limit_msg_timer > 0:
        fuel_limit_msg_timer = max(0.0, fuel_limit_msg_timer - dt)

    # Update station open/close status
    if simulation_time_hours >= 21 or simulation_time_hours < 6:
        station_open = False
    else:
        station_open = True
    #MOHSINA
    # After 9 PM, wait vehicles leave early
    if not station_open:
        for v in vehicles:
            if v["state"] in ["waiting", "moving"]:
                v["state"] = "leaving_side"
                v["speed"] = max(v["speed"], 200)

    # Update gate angle
    if not station_open:
        target_gate_angle = 0.0
    else:
        pump_occupied = False
        if vehicles:
            front = vehicles[0]
            if front["state"] in ["waiting", "fuelling"] and front["y"] >= PUMP_STOP_Y - 50:
                pump_occupied = True
        target_gate_angle = 0.0 if pump_occupied else 90.0
        
    if gate_angle < target_gate_angle:
        gate_angle = min(target_gate_angle, gate_angle + dt * 100)
    elif gate_angle > target_gate_angle:
        gate_angle = max(target_gate_angle, gate_angle - dt * 100)

    if not vehicles:
        seller_fueling    = False
        nozzle_connected  = False
        return

    front = vehicles[0]

    # Update exit animation for all vehicles
    for v in vehicles:
        if v.get("is_exited", False):
            v["exit_anim"] = min(1.0, v["exit_anim"] + dt * 2.5)
        else:
            v["exit_anim"] = max(0.0, v["exit_anim"] - dt * 2.5)

    if front["state"] == "moving":
        dist = PUMP_STOP_Y - front["y"]
        if dist <= 0:
            front["y"] = PUMP_STOP_Y
            front["state"] = "waiting"
        else:
            front["y"] += min(front["speed"] * dt, dist)

    elif front["state"] == "waiting":
        pass

    elif front["state"] == "fuelling":
        if nozzle_connected:
            fuel_timer += dt
            # Calculate fuel percentage for the bar
            limit = get_fuel_limit(front["type"])
            if limit > 0:
                front["fuel_pct"] = min(1.0, fuel_dispensed / limit)
            else:
                front["fuel_pct"] = min(1.0, fuel_timer / 6.0)
            
            # Trigger exit animation after half a second
            if fuel_timer > 0.5:
                front["exit_anim"] = min(1.0, front["exit_anim"] + dt * 2)
            
            # Update controlled dispensing; auto-disconnect on limit
            limit_hit = update_fuel_dispensing(dt, front)
            if limit_hit:
                _do_disconnect_auto(front)

    elif front["state"] in ("leaving", "leaving_side"):
        front["y"] += front["speed"] * dt
        if front["state"] == "leaving_side":
            front["x"] -= front["speed"] * dt * 0.5
        
        if front["y"] > CANOPY_D + 500:
            if front["state"] == "leaving" and fuel_dispensed > 0:
                record_vehicle_served(front["type"], fuel_dispensed)
            vehicles.pop(0)
            nozzle_connected  = False
            seller_fueling    = False
            seller_at_vehicle = False
            fuel_dispensed    = 0.0
            fuel_limit_reached = False

    # Smooth auto walk-back
    if seller_walking_backward:
        seller_walk_t = max(seller_walk_t - dt * (SELLER_SPEED / 300.0), 0.0)
        if vehicles:
            tx, ty = get_seller_target_pos(vehicles[0])
        else:
            tx, ty = SEL_X_HOME, SEL_Y_HOME
        sel_x = SEL_X_HOME + (tx - SEL_X_HOME) * seller_walk_t
        sel_y = SEL_Y_HOME + (ty - SEL_Y_HOME) * seller_walk_t

        BOLLARD_CLEAR_X = 130.0
        if sel_x < BOLLARD_CLEAR_X:
            sel_x = BOLLARD_CLEAR_X

        if seller_walk_t <= 0.0:
            sel_x                   = SEL_X_HOME
            sel_y                   = SEL_Y_HOME
            seller_walking_backward = False
            seller_at_vehicle       = False

    seller_fueling = nozzle_connected

    for i in range(1, len(vehicles)):
        v    = vehicles[i]
        prev = vehicles[i-1]
        
        if v["state"] == "leaving_side":
            v["y"] += v["speed"] * dt
            v["x"] -= v["speed"] * dt * 0.5
            continue
            
        gap      = VEHICLE_GAP + vehicle_length(prev["type"]) // 2 + vehicle_length(v["type"]) // 2
        target_y = prev["y"] - gap
        target_y = min(target_y, PUMP_STOP_Y - gap * i)
        dist = target_y - v["y"]
        if dist > 2:
            v["y"] += min(v["speed"] * dt, dist)
    
    #MOHSINA
    #Update time and statistics
    update_simulation_time(dt)
    
    # Auto-reset daily statistics
    global time_since_last_reset
    time_since_last_reset += dt
    if time_since_last_reset >= AUTO_RESET_INTERVAL:
        reset_daily_statistics()
    
    # Update cheat mode
    update_cheat_mode(dt)  

    to_remove_effects = []
    for effect in money_effects:
        effect.elapsed += dt
        if effect.elapsed < effect.life_time:
            effect.x += effect.vx * dt
            effect.y += effect.vy * dt
            effect.z += effect.vz * dt - 200 * dt * dt
        else:
            to_remove_effects.append(effect)
            
    for effect in to_remove_effects:
        money_effects.remove(effect)

    to_remove_vehicles = [v for v in vehicles if v["state"] == "leaving_side" and v["y"] > CANOPY_D + 500]
    for v in to_remove_vehicles:
        if v in vehicles:
            vehicles.remove(v)

def _do_disconnect_auto(front_veh):
    """
    Auto-disconnect when fuel limit is reached (no key press needed).
    """
    global nozzle_connected, seller_fueling, seller_at_vehicle
    global seller_walking_backward
    nozzle_connected        = False
    seller_fueling          = False
    seller_at_vehicle       = False
    seller_walking_backward = True
    if front_veh["state"] == "fuelling":
        front_veh["state"] = "leaving"
    print(f"  Fuel limit reached! Auto-disconnect. Vehicle leaving.")


# ═══════════════════════════════════════════════════════════════════════════════
#  SELLER SNAP HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_look_toward_cap(front_veh, from_x, from_y, eye_z=128.0):
    fcx, fcy, fcz = get_vehicle_fuel_cap(front_veh)
    dx = fcx - from_x
    dy = fcy - from_y
    dz = fcz - eye_z

    world_yaw = math.atan2(dx, dy)
    yaw_deg   = math.degrees(world_yaw - SEL_YAW)
    yaw_deg = max(-90.0, min(90.0, yaw_deg))

    horiz     = math.sqrt(dx*dx + dy*dy)
    pitch_deg = math.degrees(math.atan2(dz, max(horiz, 1.0)))
    pitch_deg = max(-60.0, min(60.0, pitch_deg))

    return yaw_deg, pitch_deg


def _orient_fp_toward_vehicle(front_veh, from_x, from_y):
    global fp_yaw, fp_pitch
    fp_yaw, fp_pitch = _compute_look_toward_cap(front_veh, from_x, from_y)


def snap_seller_to_vehicle(front_veh):
    global sel_x, sel_y, seller_walk_t, seller_at_vehicle, seller_walking_backward
    seller_walking_backward = False
    seller_walk_t           = 1.0
    seller_at_vehicle       = True
    tx, ty = get_seller_target_pos(front_veh)
    sel_x  = tx
    sel_y  = ty
    _orient_fp_toward_vehicle(front_veh, tx, ty)


# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════════════════════════════════════════════
def setup_camera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60.0, WIN_W/WIN_H, 1.0, 6000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if is_first_person:
        eye_x = sel_x
        eye_y = sel_y
        eye_z = 128.0

        front_veh = vehicles[0] if vehicles else None

        # If we have a vehicle and seller is at it, point directly at the fuel cap
        if seller_at_vehicle and front_veh is not None and \
                front_veh["state"] in ("waiting", "fuelling"):
            fcx, fcy, fcz = get_vehicle_fuel_cap(front_veh)
            total_yaw   = SEL_YAW + math.radians(fp_yaw)
            horiz       = math.cos(math.radians(fp_pitch))
            lx = fcx - eye_x
            ly = fcy - eye_y
            lz = fcz - eye_z
            length = math.sqrt(lx*lx + ly*ly + lz*lz)
            if length > 0:
                lx /= length
                ly /= length
                lz /= length
            gluLookAt(eye_x, eye_y, eye_z,
                      eye_x + lx * 400.0,
                      eye_y + ly * 400.0,
                      eye_z + lz * 400.0,
                      0, 0, 1)
        else:
            total_yaw   = SEL_YAW + math.radians(fp_yaw)
            horiz       = math.cos(math.radians(fp_pitch))
            lx = -math.sin(total_yaw) * horiz
            ly = -math.cos(total_yaw) * horiz
            lz =  math.sin(math.radians(fp_pitch))
            gluLookAt(eye_x, eye_y, eye_z,
                      eye_x + lx * 400.0,
                      eye_y + ly * 400.0,
                      eye_z + lz * 400.0,
                      0, 0, 1)
    else:
        
        cx = cam_radius * math.sin(cam_angle)
        cy = cam_radius * math.cos(cam_angle)
        gluLookAt(cx, cy, cam_height, 0, 0, 80, 0, 0, 1)


# ═══════════════════════════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════
def show_screen():
    # Get unified sky color
    sky_r, sky_g, sky_b = get_sky_color()
    
    # Use the same sky color for clear color
    glClearColor(sky_r, sky_g, sky_b, 1.0)
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    setup_camera()

    draw_ground()
    draw_canopy()
    draw_entrance_gate()
    draw_price_sign()
    draw_fuel_pump()
    draw_3d_statistics_board()
    draw_3d_clock()
    draw_money_effects()

    front_veh = vehicles[0] if vehicles else None

    if not is_first_person:
        draw_seller(fueling=seller_fueling,
                    front_vehicle=front_veh if seller_fueling else None)
    else:
        if seller_fueling and front_veh:
            draw_nozzle_hose(front_veh)

    for v in vehicles:
        draw_vehicle(v)


    draw_corner_hud_statistics()
    draw_receipt_display()
    # ── HUD ───────────────────────────────────────────────────────────────────
    mode = "First-Person (Seller's POV)" if is_first_person else "Third-Person (Overview)"
    draw_text(12, WIN_H-28, "View : "+mode, color=(0.88,1.0,0.88))

    fstates = [v["state"] for v in vehicles]
    draw_text(12, WIN_H-52, f"Queue: {len(vehicles)} vehicle(s)  {fstates}",
              color=(1.0,0.90,0.50))

    # ── Fuel limit message (tank full) ────────────────────────────────────────
    if fuel_limit_reached and fuel_limit_msg_timer > 0 and front_veh:
        limit = get_fuel_limit(front_veh["type"])
        draw_text_large(WIN_W//2 - 260, WIN_H//2 + 20,
                        f"  TANK FULL! {limit:.0f}L limit reached – nozzle disconnected",
                        color=(0.10, 1.0, 0.20))

    if seller_fueling and front_veh:
        elapsed   = int(fuel_timer)
        limit     = get_fuel_limit(front_veh["type"])
        dispensed = fuel_dispensed
        draw_text(12, WIN_H-76,
                  f"FUELING  {elapsed}s  |  {dispensed:.1f}L / {limit:.0f}L "
                  f"({front_veh['type'].upper()} limit)  |  O = Stop fueling",
                  color=(0.40,1.0,0.40))
    elif seller_at_vehicle and front_veh and front_veh["state"] == "waiting":
        draw_text(12, WIN_H-76,
                  "Seller AT vehicle  |  F = Connect nozzle & start fueling",
                  color=(0.40,0.90,1.00))
    elif seller_walking_backward:
        walk_pct = int(seller_walk_t * 100)
        draw_text(12, WIN_H-76,
                  f"Seller walking back home...  {walk_pct}%",
                  color=(1.0,0.70,0.30))
    elif front_veh and front_veh["state"] == "waiting":
        draw_text(12, WIN_H-76,
                  "Vehicle WAITING  |  F = Walk to vehicle & start fueling",
                  color=(1.0,0.70,0.20))
    elif front_veh and front_veh["state"] == "leaving":
        draw_text(12, WIN_H-76, "Vehicle leaving...", color=(0.80,0.80,0.80))
    else:
        draw_text(12, WIN_H-76, "Seller: Waiting for next vehicle",
                  color=(0.80,0.80,0.80))

    # ── Fuel limits legend ────────────────────────────────────────────────────
    if seller_fueling and front_veh:
        limit = get_fuel_limit(front_veh["type"])
        bar_w = 300
        filled = int(bar_w * min(fuel_dispensed / max(limit, 1), 1.0))
        draw_text(12, WIN_H-124,
                  f"Fuel Limits — Bike: {FUEL_LIMITS['bike']:.0f}L  "
                  f"Car: {FUEL_LIMITS['car']:.0f}L  "
                  f"Truck: {FUEL_LIMITS['truck']:.0f}L",
                  color=(0.90,0.90,0.50))

    walk_pct = int(seller_walk_t * 100)
    draw_text(12, WIN_H-100,
              f"Seller position: {walk_pct}%  |  nozzle={'CONNECTED' if nozzle_connected else 'idle'}",
              color=(0.70,0.90,1.00))

    # Day/Night indicator
    if day_light < 0.5:
        draw_text(WIN_W - 120, WIN_H - 28, "NIGHT MODE", color=(0.80, 0.50, 0.20))
    else:
        draw_text(WIN_W - 120, WIN_H - 28, "DAY MODE", color=(1.0, 0.90, 0.40))

    if is_first_person:
        draw_text(12, 66,
                  "Arrow Keys : Adjust Look Direction (works in ALL modes)",
                  color=(0.76,0.76,0.76))
    else:
        draw_text(12, 66,
                  "UP/DOWN : Camera Height     LEFT/RIGHT : Rotate Camera",
                  color=(0.76,0.76,0.76))

    draw_text(12, 42,
              "F : Snap to vehicle & start fueling     O / D : Stop fueling & walk home",
              color=(0.76,0.76,0.76))
    draw_text(12, 18, 
              "E : Exit/Enter driver    D/N : Day/Night mode     Right-Click : Toggle POV     ESC : Quit",
              color=(0.76,0.76,0.76))

    glutSwapBuffers()


# ═══════════════════════════════════════════════════════════════════════════════
#  TIMER / ANIMATION
# ═══════════════════════════════════════════════════════════════════════════════

def idle_func():
    global last_time
    now = time.time()
    dt = now - last_time
    last_time = now
    if dt > 0.1: dt = 0.1
    update_simulation(dt * sim_speed)
    glutPostRedisplay()


# ═══════════════════════════════════════════════════════════════════════════════
#  INPUT
# ═══════════════════════════════════════════════════════════════════════════════
def mouse_listener(button, state, x, y):
    global is_first_person, fp_yaw, fp_pitch
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        is_first_person = not is_first_person
        if is_first_person:
            front_veh = vehicles[0] if vehicles else None
            if front_veh and front_veh["state"] in ("waiting", "fuelling"):
                _orient_fp_toward_vehicle(front_veh, sel_x, sel_y)
            else:
                fp_yaw   = 0.0
                fp_pitch = 0.0
        else:
            fp_yaw   = 0.0
            fp_pitch = 0.0
        print(f"  View -> {'First-Person' if is_first_person else 'Third-Person'}")
    glutPostRedisplay()


def special_key(key, x, y):
    global cam_angle, cam_height, fp_yaw, fp_pitch
    if is_first_person:
        if key == GLUT_KEY_LEFT:   fp_yaw  -= 5
        if key == GLUT_KEY_RIGHT:  fp_yaw  += 5
        if key == GLUT_KEY_UP:     fp_pitch = min(fp_pitch + 3,  80)
        if key == GLUT_KEY_DOWN:   fp_pitch = max(fp_pitch - 3, -80)
    else:
        if key == GLUT_KEY_UP:     cam_height = min(cam_height + 30, 2000)
        if key == GLUT_KEY_DOWN:   cam_height = max(cam_height - 30, 60)
        if key == GLUT_KEY_LEFT:   cam_angle -= 0.05
        if key == GLUT_KEY_RIGHT:  cam_angle += 0.05
    glutPostRedisplay()


def _do_disconnect():
    """Manual disconnect: O or D key pressed."""
    global nozzle_connected, seller_fueling, seller_at_vehicle
    global seller_walking_backward, fp_yaw, fp_pitch
    global fuel_dispensed
    if nozzle_connected:
        nozzle_connected        = False
        seller_fueling          = False
        seller_at_vehicle       = False
        seller_walking_backward = True
        fp_yaw   = 0.0
        fp_pitch = -10.0
        if vehicles and vehicles[0]["state"] == "fuelling":
            vehicles[0]["state"] = "leaving"
        print("  Nozzle DISCONNECTED – seller walking back home, vehicle leaving")
    else:
        print("  Nozzle is not connected.")


def keyboard_listener(key, x, y):
    global sel_x, sel_y, seller_walk_t
    global seller_walking_backward, seller_at_vehicle
    global nozzle_connected, seller_fueling, fuel_timer
    global fuel_dispensed, fuel_limit_reached, day_light

    if key == b'\x1b':
        sys.exit(0)

    #cheat
    if key == b'c' or key == b'C':
        toggle_cheat_mode()
        glutPostRedisplay()
        return
    
    global sim_speed
    if key == b's':
        sim_speed = max(0.2, sim_speed - 0.2)
        print(f"Simulation speed: {sim_speed:.1f}x")
    if key == b'S':
        sim_speed = min(5.0, sim_speed + 0.2)
        print(f"Simulation speed: {sim_speed:.1f}x")
    
    # Manual reset
    if key == b'r' or key == b'R':
        manual_reset_daily_stats_key_handler()
        glutPostRedisplay()
        return    

    # Day/Night controls
    if key == b'd' or key == b'D':
        day_light = min(1.0, day_light + 0.05)
    elif key == b'n' or key == b'N':
        day_light = max(0.1, day_light - 0.05)
    
    # Exit/Enter driver control
    if key == b'e' or key == b'E':
        if vehicles:
            front = vehicles[0]
            if front["state"] in ["fuelling", "waiting"]:
                front["is_exited"] = not front["is_exited"]

    front_veh = vehicles[0] if vehicles else None

    if key in (b'f', b'F'):
        if front_veh and front_veh["state"] in ("waiting", "fuelling"):
            snap_seller_to_vehicle(front_veh)
            if not nozzle_connected:
                nozzle_connected   = True
                seller_fueling     = True
                fuel_dispensed     = 0.0
                fuel_limit_reached = False
                if front_veh["state"] == "waiting":
                    front_veh["state"] = "fuelling"
                    fuel_timer = 0.0
                limit = get_fuel_limit(front_veh["type"])
                print(f"  Nozzle CONNECTED – fueling {front_veh['type']} "
                      f"(limit {limit:.0f}L @ {FUEL_RATE}L/s). Press O to stop early.")
            else:
                print("  Nozzle already connected.")
        else:
            print("  No vehicle waiting at pump.")

    elif key in (b'o', b'O'):
        _do_disconnect()

    glutPostRedisplay()


def keyboard_up_listener(key, x, y):
    glutPostRedisplay()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    global last_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(80, 60)
    glutCreateWindow(b"openGL Filling Station")

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(show_screen)
    glutSpecialFunc(special_key)
    glutKeyboardFunc(keyboard_listener)
    glutKeyboardUpFunc(keyboard_up_listener)
    glutMouseFunc(mouse_listener)

    last_time = time.time()
    glutIdleFunc(idle_func)

    print("=" * 64)
    print("   openGL Filling Station  –  Controlled Fueling Simulation")
    print("=" * 64)
    print("   Right-Click        : Toggle 3rd / 1st person POV")
    print("   Arrow Keys (3rd)   : UP/DOWN=height | L/R=rotate")
    print("   Arrow Keys (1st)   : Look around")
    print()
    print("   FUELING CONTROLS:")
    print("   F  : Snap seller beside vehicle & connect nozzle")
    print("   O  : Disconnect nozzle early & seller walks home")
    print("   D  : Same as O (also Day mode)")
    print("   N  : Night mode")
    print("   E  : Exit/Enter driver from vehicle")
    print()
    print("   FUEL LIMITS (auto-disconnect at limit):")
    print(f"   Bike  : {FUEL_LIMITS['bike']:.0f} litres")
    print(f"   Car   : {FUEL_LIMITS['car']:.0f} litres")
    print(f"   Truck : {FUEL_LIMITS['truck']:.0f} litres")
    print(f"   Rate  : {FUEL_RATE} litres/second")
    print()
    print("   WORKFLOW: wait for vehicle → press F → fueling begins →")
    print("             auto-stops at limit OR press O to stop early")
    print("=" * 64)


    print()
    print("   YOUR FEATURES - STATISTICS, REVENUE & CHEAT MODE:")
    print("   ────────────────────────────────────────────────")
    print("   R  : Manual reset daily statistics")
    print("   C  : Toggle cheat mode (auto-serves vehicles)")
    print()
    print("   STATISTICS DISPLAY:")
    print("   • 3D board on LEFT: vehicles served & liters today")
    print("   • 3D clock on RIGHT: simulation time (8:00 AM start)")
    print("   • Corner HUD: Daily & lifetime revenue")
    print("   • Receipt: Auto-displays when vehicle leaves")
    print("   • Coins: Animate upward when vehicle pays")
    print()
    print("   REVENUE SYSTEM:")
    print(f"   • Full tank price: ${PRICE_PER_FULL_TANK:.2f}")
    print(f"   • Bike (5L):  ${PRICE_PER_FULL_TANK * 0.5:.2f} max")
    print(f"   • Car (10L):  ${PRICE_PER_FULL_TANK:.2f} max")
    print(f"   • Truck (20L): ${PRICE_PER_FULL_TANK * 2:.2f} max")
    print()
    print("   CHEAT MODE:")
    print(f"   • Auto-serves every {CHEAT_AUTO_SERVE_INTERVAL}s")
    print(f"   • After {CHEAT_RESET_AT_CARS} cars: night transition")
    print("   • Morning arrival: auto day-reset")
    print("=" * 64)



    glutMainLoop()

if __name__ == "__main__":
    main()
