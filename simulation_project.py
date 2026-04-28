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
SEL_X   =  115.0
SEL_Y   =  -50.0
SEL_YAW = math.pi * 1.12

# ─── Camera – 3rd person ─────────────────────────────────────────────────────
cam_angle  = 0.35
cam_height = 700.0
cam_radius = 1000.0

# ─── Camera – 1st person ─────────────────────────────────────────────────────
is_first_person = False
fp_yaw   = 0.0
fp_pitch = 0.0

# ─── Road / Queue constants ───────────────────────────────────────────────────
ROAD_Y_ENTRY  = -1800   # vehicles spawn here
ROAD_Y_PUMP   =    0    # fuelling stop (Y)
ROAD_X        = -200    # X lane centre for approaching vehicles
PUMP_STOP_Y   = -130    # where front vehicle stops (in front of pump)
VEHICLE_GAP   =  200    # minimum gap between queued vehicles (world units)

# ─── Simulation state ─────────────────────────────────────────────────────────
last_time        = 0.0
spawn_timer      = 0.0
SPAWN_INTERVAL   = 3.5   # seconds between spawns
FUEL_TIME        = 6.0   # seconds to fuel front vehicle
fuel_timer       = 0.0
vehicles         = []    # list of dicts

VTYPES = ["bike", "car", "truck"]

def make_vehicle():
    vtype = random.choice(VTYPES)
    color_body  = (random.uniform(0.4,1.0), random.uniform(0.1,0.8), random.uniform(0.1,0.8))
    return {
        "type"   : vtype,
        "x"      : ROAD_X,
        "y"      : ROAD_Y_ENTRY,
        "speed"  : random.uniform(180, 260),   # world-units / second
        "color"  : color_body,
        "state"  : "moving",   # moving | fuelling | leaving
        "fuel_t" : 0.0,
    }


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


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUND
# ═══════════════════════════════════════════════════════════════════════════════
def draw_ground():
    # Dark asphalt
    glColor3f(0.18,0.18,0.18)
    glBegin(GL_QUADS)
    glVertex3f(-2000,-2000,-2); glVertex3f(2000,-2000,-2)
    glVertex3f(2000,2000,-2);   glVertex3f(-2000,2000,-2)
    glEnd()

    # Concrete pad
    glColor3f(0.70,0.70,0.70)
    glBegin(GL_QUADS)
    glVertex3f(-CANOPY_W-35,-CANOPY_D-35,0); glVertex3f(CANOPY_W+35,-CANOPY_D-35,0)
    glVertex3f(CANOPY_W+35,CANOPY_D+35,0);   glVertex3f(-CANOPY_W-35,CANOPY_D+35,0)
    glEnd()

    glColor3f(0.76,0.76,0.76)
    glBegin(GL_QUADS)
    glVertex3f(-CANOPY_W+15,-CANOPY_D+15,0.5); glVertex3f(CANOPY_W-15,-CANOPY_D+15,0.5)
    glVertex3f(CANOPY_W-15,CANOPY_D-15,0.5);   glVertex3f(-CANOPY_W+15,CANOPY_D-15,0.5)
    glEnd()

    # Oil stains
    for ox,oy,ow,od in [(-40,-60,80,50),(60,80,70,45),(-80,20,60,40)]:
        glColor3f(0.58,0.58,0.58)
        glBegin(GL_QUADS)
        glVertex3f(ox,oy,1); glVertex3f(ox+ow,oy,1)
        glVertex3f(ox+ow,oy+od,1); glVertex3f(ox,oy+od,1)
        glEnd()

    # Yellow lane dividers
    glColor3f(0.94,0.84,0.0)
    for lx in [-210,210]:
        glBegin(GL_QUADS)
        glVertex3f(lx-5,-CANOPY_D-35,2); glVertex3f(lx+5,-CANOPY_D-35,2)
        glVertex3f(lx+5,CANOPY_D+35,2);  glVertex3f(lx-5,CANOPY_D+35,2)
        glEnd()

    # Road centre dashes
    glColor3f(0.82,0.82,0.10)
    for seg in range(6):
        ys = -2000+seg*260
        glBegin(GL_QUADS)
        glVertex3f(-6,ys,1); glVertex3f(6,ys,1)
        glVertex3f(6,ys+160,1); glVertex3f(-6,ys+160,1)
        glEnd()

    # Curbs
    glColor3f(0.92,0.92,0.92)
    cw=10; cy1=CANOPY_D+35; cx1=CANOPY_W+35
    draw_box(-cx1-cw,-cy1-cw,0, cx1+cw,-cy1,8)
    draw_box(-cx1-cw,cy1,0,     cx1+cw,cy1+cw,8)
    draw_box(-cx1-cw,-cy1-cw,0,-cx1,cy1+cw,8)
    draw_box(cx1,-cy1-cw,0,     cx1+cw,cy1+cw,8)

    # ── Approach road (vehicle lane) ─────────────────────────────────────────
    # Asphalt road strip in front of station
    glColor3f(0.22,0.22,0.22)
    glBegin(GL_QUADS)
    glVertex3f(ROAD_X-120,-2000,0); glVertex3f(ROAD_X+120,-2000,0)
    glVertex3f(ROAD_X+120,-CANOPY_D-35,0); glVertex3f(ROAD_X-120,-CANOPY_D-35,0)
    glEnd()

    # Road edge lines
    glColor3f(0.85,0.85,0.20)
    glBegin(GL_QUADS)
    glVertex3f(ROAD_X-118,-2000,1); glVertex3f(ROAD_X-112,-2000,1)
    glVertex3f(ROAD_X-112,-CANOPY_D-35,1); glVertex3f(ROAD_X-118,-CANOPY_D-35,1)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(ROAD_X+112,-2000,1); glVertex3f(ROAD_X+118,-2000,1)
    glVertex3f(ROAD_X+118,-CANOPY_D-35,1); glVertex3f(ROAD_X+112,-CANOPY_D-35,1)
    glEnd()

    # Dashed centre line on approach road
    glColor3f(0.85,0.85,0.10)
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
    # Roof slab
    glColor3f(0.09,0.12,0.44)
    draw_box(-CANOPY_W,-CANOPY_D,CANOPY_H, CANOPY_W,CANOPY_D,CANOPY_H+ROOF_T)

    # White perimeter trim
    t=15
    glColor3f(0.91,0.91,0.91)
    draw_box(-CANOPY_W,-CANOPY_D-t,CANOPY_H-14, CANOPY_W,-CANOPY_D,CANOPY_H)
    draw_box(-CANOPY_W,CANOPY_D,CANOPY_H-14,    CANOPY_W,CANOPY_D+t,CANOPY_H)
    draw_box(-CANOPY_W-t,-CANOPY_D,CANOPY_H-14,-CANOPY_W,CANOPY_D,CANOPY_H)
    draw_box(CANOPY_W,-CANOPY_D,CANOPY_H-14,    CANOPY_W+t,CANOPY_D,CANOPY_H)

    # ── Station name banner panel – fitted into front fascia ──────────────────
    # Dark navy background panel on front fascia
    glColor3f(0.06,0.08,0.35)
    draw_box(-320,-CANOPY_D-t-2, CANOPY_H-12,
              320,-CANOPY_D-t-16, CANOPY_H+ROOF_T+4)

    # Bright border around name panel
    glColor3f(1.0, 0.84, 0.0)
    bx1,bx2 = -320, 320
    by1,by2 = -CANOPY_D-t-2, -CANOPY_D-t-16
    bz1,bz2 = CANOPY_H-12, CANOPY_H+ROOF_T+4
    # top/bottom/left/right thin borders
    draw_box(bx1,by1,bz2-3, bx2,by2,bz2)
    draw_box(bx1,by1,bz1,   bx2,by2,bz1+3)
    draw_box(bx1,by1,bz1,   bx1+4,by2,bz2)
    draw_box(bx2-4,by1,bz1, bx2,by2,bz2)

    # Canopy light strips (underside)
    glColor3f(0.96,0.96,0.88)
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

    # Orange banner
    glColor3f(1.0,0.52,0.0)
    draw_box(-CANOPY_W+80,-CANOPY_D+8,CANOPY_H-42, CANOPY_W-80,-CANOPY_D+24,CANOPY_H-26)
    glColor3f(1.0,1.0,1.0)
    for xs in range(-400,400,60):
        draw_box(xs,-CANOPY_D+9,CANOPY_H-40, xs+32,-CANOPY_D+23,CANOPY_H-30)


# ═══════════════════════════════════════════════════════════════════════════════
#  PRICE SIGN
# ═══════════════════════════════════════════════════════════════════════════════
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
    glColor3f(1.00,0.76,0.03)
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


# ═══════════════════════════════════════════════════════════════════════════════
#  SELLER
# ═══════════════════════════════════════════════════════════════════════════════
def draw_seller():
    quad=gluNewQuadric()
    glPushMatrix()
    glTranslatef(SEL_X,SEL_Y,0)
    glRotatef(-math.degrees(SEL_YAW),0,0,1)
    glColor3f(0.08,0.05,0.03)
    draw_box(-18,-15,0, -4,15,10)
    draw_box(4,-15,0,   18,15,10)
    glColor3f(0.12,0.12,0.35)
    glPushMatrix(); glTranslatef(-13,0,10); glRotatef(180,1,0,0)
    gluCylinder(quad,12,17,37,16,1); glPopMatrix()
    glPushMatrix(); glTranslatef(13,0,10); glRotatef(180,1,0,0)
    gluCylinder(quad,12,17,37,16,1); glPopMatrix()
    glColor3f(0.05,0.05,0.05)
    draw_box(-22,-15,46, 22,15,53)
    glColor3f(0.65,0.55,0.20)
    draw_box(-6,-15.5,47, 6,16.5,52)
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
    glColor3f(0.84,0.63,0.43)
    glPushMatrix(); glTranslatef(-34,0,94); glRotatef(160,1,0,0)
    draw_manual_solid_cylinder(8,7,50,14,lw=2.0); glPopMatrix()
    glPushMatrix(); glTranslatef(-34,18,54)
    gluSphere(quad,8,10,10); glPopMatrix()
    glColor3f(0.84,0.63,0.43)
    glPushMatrix(); glTranslatef(34,0,95)
    glRotatef(95,0,1,0); glRotatef(-30,1,0,0)
    draw_manual_solid_cylinder(8,7,68,14,lw=2.0); glPopMatrix()
    glPushMatrix(); glTranslatef(96,-28,80)
    gluSphere(quad,9,10,10); glPopMatrix()
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


# ═══════════════════════════════════════════════════════════════════════════════
#  VEHICLE DRAWERS  (all built from draw_box + spheres)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_wheel(r=14):
    """Draw a wheel (dark torus approximation using a cylinder stack)."""
    quad = gluNewQuadric()
    glColor3f(0.10,0.10,0.10)
    glPushMatrix(); glRotatef(90,1,0,0)
    gluCylinder(quad,r,r,12,16,1)
    gluDisk(quad,0,r,16,1)
    glTranslatef(0,0,12); gluDisk(quad,0,r,16,1); glPopMatrix()
    # Hub
    glColor3f(0.65,0.65,0.65)
    glPushMatrix(); glRotatef(90,1,0,0)
    gluCylinder(quad,r*0.35,r*0.35,14,8,1); glPopMatrix()


def draw_bike(color):
    """Motorbike – side view oriented along Y axis (front = +Y)."""
    quad = gluNewQuadric()
    r, g, b = color

    # Frame (thin box)
    glColor3f(r,g,b)
    draw_box(-12,-60,30, 12,60,75)

    # Fuel tank (box on top of frame)
    glColor3f(r*0.85,g*0.85,b*0.85)
    draw_box(-14,-28,68, 14,20,90)

    # Seat (darker, slightly elevated)
    glColor3f(0.15,0.15,0.15)
    draw_box(-12,-50,82, 12,10,90)

    # Handlebars
    glColor3f(0.55,0.55,0.55)
    draw_box(-20,18,88, 20,26,96)    # horizontal bar
    draw_box(-16,18,78, -12,26,96)   # left grip
    draw_box(12,18,78, 16,26,96)     # right grip

    # Front fork
    glColor3f(0.55,0.55,0.55)
    draw_box(-6,34,20, 6,56,70)

    # Engine block
    glColor3f(0.30,0.30,0.30)
    draw_box(-16,-20,22, 16,20,55)

    # Exhaust pipe
    glColor3f(0.50,0.50,0.50)
    glPushMatrix(); glTranslatef(-18,0,28); glRotatef(90,0,1,0)
    gluCylinder(quad,5,3,8,8,1); glPopMatrix()

    # Wheels
    glPushMatrix(); glTranslatef(0,50,18); draw_wheel(18); glPopMatrix()   # front
    glPushMatrix(); glTranslatef(0,-50,18); draw_wheel(18); glPopMatrix()  # rear

    # Headlight
    glColor3f(1.0,0.95,0.60)
    glPushMatrix(); glTranslatef(0,62,52); gluSphere(quad,9,8,8); glPopMatrix()

    # Rider (simple figure)
    # Body
    glColor3f(0.20,0.30,0.75)
    draw_box(-14,-30,82, 14,10,128)
    # Helmet
    glColor3f(r,g,b)
    glPushMatrix(); glTranslatef(0,-10,138)
    gluSphere(quad,18,12,12); glPopMatrix()
    # Arms
    glColor3f(0.20,0.30,0.75)
    draw_box(-22,-8,100, -14,22,112)
    draw_box(14,-8,100,   22,22,112)


def draw_car(color):
    """Sedan car oriented along Y axis (front = +Y)."""
    quad = gluNewQuadric()
    r, g, b = color

    # Main body lower
    glColor3f(r,g,b)
    draw_box(-70,-120,15, 70,120,68)

    # Cabin / roof
    glColor3f(r*0.80,g*0.80,b*0.80)
    draw_box(-58,-80,68, 58,75,118)

    # Hood (slightly raised)
    glColor3f(r*0.90,g*0.90,b*0.90)
    draw_box(-68,75,48, 68,120,68)

    # Trunk
    glColor3f(r*0.90,g*0.90,b*0.90)
    draw_box(-68,-120,48, 68,-82,68)

    # Windows (dark blue tint)
    glColor3f(0.35,0.45,0.65)
    draw_box(-56,-76,72, 56,72,114)

    # Window pillars
    glColor3f(r*0.70,g*0.70,b*0.70)
    draw_box(-58,-76,68, -52,72,118)
    draw_box(52,-76,68,   58,72,118)
    draw_box(-58,-4,68,   58,2,118)

    # Grille
    glColor3f(0.15,0.15,0.15)
    draw_box(-45,116,28, 45,122,56)
    glColor3f(0.80,0.80,0.80)
    for gx in range(-40,44,12):
        draw_box(gx,116,32, gx+7,122,52)

    # Headlights
    glColor3f(1.0,0.95,0.60)
    glPushMatrix(); glTranslatef(-48,118,48)
    gluSphere(quad,10,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(48,118,48)
    gluSphere(quad,10,8,8); glPopMatrix()

    # Tail lights
    glColor3f(0.90,0.10,0.10)
    glPushMatrix(); glTranslatef(-52,-118,46)
    gluSphere(quad,9,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(52,-118,46)
    gluSphere(quad,9,8,8); glPopMatrix()

    # Wheels (4)
    for wx,wy in [(-72,88),(72,88),(-72,-88),(72,-88)]:
        glPushMatrix(); glTranslatef(wx,wy,18); draw_wheel(20); glPopMatrix()

    # Door lines
    glColor3f(r*0.60,g*0.60,b*0.60)
    draw_box(-70,-20,20, -68,-18,64)
    draw_box(68,-20,20,   70,-18,64)


def draw_truck(color):
    """Simple truck (cab + cargo box) oriented along Y axis (front = +Y)."""
    quad = gluNewQuadric()
    r, g, b = color

    # Cargo box (long, at rear)
    glColor3f(r,g,b)
    draw_box(-80,-240,15, 80,60,170)

    # Cargo box roof strip
    glColor3f(r*0.75,g*0.75,b*0.75)
    draw_box(-80,-240,165, 80,60,172)

    # Cab (shorter, at front)
    glColor3f(r*0.88,g*0.88,b*0.88)
    draw_box(-78,60,15, 78,175,155)

    # Cab windshield
    glColor3f(0.35,0.50,0.70)
    draw_box(-70,62,85, 70,172,148)

    # Cab pillars
    glColor3f(r*0.70,g*0.70,b*0.70)
    draw_box(-78,60,82, -70,174,155)
    draw_box(70,60,82,   78,174,155)

    # Grille / front bumper
    glColor3f(0.25,0.25,0.28)
    draw_box(-76,162,15, 76,178,78)
    glColor3f(0.60,0.60,0.62)
    draw_box(-74,164,18, 74,176,75)

    # Headlights
    glColor3f(1.0,0.95,0.60)
    glPushMatrix(); glTranslatef(-58,174,55)
    gluSphere(quad,12,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(58,174,55)
    gluSphere(quad,12,8,8); glPopMatrix()

    # Exhaust stack
    glColor3f(0.40,0.40,0.40)
    glPushMatrix(); glTranslatef(70,30,155); glRotatef(0,0,0,1)
    gluCylinder(quad,7,5,60,8,1); glPopMatrix()

    # Wheels (6 – dual rear)
    for wx,wy in [(-88,130),(88,130),(-88,-80),(88,-80),(-88,-180),(88,-180)]:
        glPushMatrix(); glTranslatef(wx,wy,20); draw_wheel(26); glPopMatrix()

    # Cargo box door lines
    glColor3f(r*0.65,g*0.65,b*0.65)
    draw_box(-80,-240,15, -78,-80,170)
    draw_box(78,-240,15,   80,-80,170)
    # Horizontal stripe
    draw_box(-80,-240,92,  80,-240+2,94)

    # Tail lights
    glColor3f(0.85,0.10,0.10)
    glPushMatrix(); glTranslatef(-70,-242,55)
    gluSphere(quad,11,8,8); glPopMatrix()
    glPushMatrix(); glTranslatef(70,-242,55)
    gluSphere(quad,11,8,8); glPopMatrix()


def draw_vehicle(v):
    """Draw a vehicle dict at its current (x, y) position."""
    glPushMatrix()
    glTranslatef(v["x"], v["y"], 0)
    if v["type"] == "bike":
        draw_bike(v["color"])
    elif v["type"] == "car":
        draw_car(v["color"])
    else:
        draw_truck(v["color"])
    glPopMatrix()


# ═══════════════════════════════════════════════════════════════════════════════
#  QUEUE / SIMULATION UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

def vehicle_length(vtype):
    if vtype == "bike":  return 130
    if vtype == "car":   return 260
    return 470   # truck

def update_simulation(dt):
    global spawn_timer, fuel_timer, vehicles

    spawn_timer += dt

    # Spawn new vehicle periodically (max 6 in queue)
    if spawn_timer >= SPAWN_INTERVAL and len(vehicles) < 6:
        vehicles.append(make_vehicle())
        spawn_timer = 0.0

    if not vehicles:
        return

    # ── Front vehicle ────────────────────────────────────────────────────────
    front = vehicles[0]
    if front["state"] == "moving":
        # Move toward pump stop
        dist = PUMP_STOP_Y - front["y"]
        if dist <= 0:
            front["y"] = PUMP_STOP_Y
            front["state"] = "fuelling"
            fuel_timer = 0.0
        else:
            front["y"] += min(front["speed"] * dt, dist)

    elif front["state"] == "fuelling":
        fuel_timer += dt
        if fuel_timer >= FUEL_TIME:
            front["state"] = "leaving"

    elif front["state"] == "leaving":
        # Drive past the pump into the station area
        front["y"] += front["speed"] * dt
        if front["y"] > CANOPY_D + 500:
            vehicles.pop(0)   # remove from queue

    # ── Vehicles behind front ────────────────────────────────────────────────
    for i in range(1, len(vehicles)):
        v    = vehicles[i]
        prev = vehicles[i-1]

        # Target stop: behind the previous vehicle with a gap
        gap      = VEHICLE_GAP + vehicle_length(prev["type"]) // 2 + vehicle_length(v["type"]) // 2
        target_y = prev["y"] - gap

        # Don't overshoot; also don't move past the pump stop
        target_y = min(target_y, PUMP_STOP_Y - gap * i)

        dist = target_y - v["y"]
        if dist > 2:
            v["y"] += min(v["speed"] * dt, dist)


# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════════════════════════════════════════════
def setup_camera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60.0, WIN_W/WIN_H, 1.0, 6000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if is_first_person:
        # ── Seller's eye – positioned AT head, looking OUTWARD toward the road ──
        eye_x = SEL_X
        eye_y = SEL_Y
        eye_z = 148    # head centre Z

        # Seller faces toward the road (negative Y = toward incoming vehicles)
        # SEL_YAW = math.pi * 1.12  →  the seller is roughly facing -Y / slightly -X
        # Base direction: seller faces the pump (-X, slightly -Y from SEL pos)
        # We want eyes to look out from the seller toward the vehicles / road.
        # The seller's facing yaw puts -Y as forward from his perspective.
        base_yaw_rad = SEL_YAW   # world yaw of seller (rad)

        # Apply fp_yaw offset (degrees)
        total_yaw = base_yaw_rad + math.radians(fp_yaw)
        horiz = math.cos(math.radians(fp_pitch))
        look_dx = math.sin(total_yaw) * horiz
        look_dy = math.cos(total_yaw) * horiz
        look_dz = math.sin(math.radians(fp_pitch))

        gluLookAt(eye_x, eye_y, eye_z,
                  eye_x + look_dx*400,
                  eye_y + look_dy*400,
                  eye_z + look_dz*400,
                  0, 0, 1)
    else:
        cx = cam_radius * math.sin(cam_angle)
        cy = cam_radius * math.cos(cam_angle)
        gluLookAt(cx, cy, cam_height, 0, 0, 80, 0, 0, 1)


# ═══════════════════════════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════
def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    setup_camera()

    draw_ground()
    draw_canopy()
    draw_price_sign()
    draw_fuel_pump()
    draw_seller()

    # Draw all vehicles
    for v in vehicles:
        draw_vehicle(v)

    # ── HUD overlay ──────────────────────────────────────────────────────────
    # Station name rendered in the canopy fascia area on screen
    # (no longer at top of window – the 3D panel on the canopy carries it)
    # We keep a small mode label
    mode = "First-Person (Seller's POV)" if is_first_person else "Third-Person (Overview)"
    draw_text(12, WIN_H-38, "View : "+mode, color=(0.88,1.0,0.88))

    # Queue status
    fstates = [v["state"] for v in vehicles]
    draw_text(12, WIN_H-62, f"Queue: {len(vehicles)} vehicle(s)  {fstates}", color=(1.0,0.90,0.50))

    # Controls
    if is_first_person:
        draw_text(12, 42, "Arrow Keys : Look Around", color=(0.76,0.76,0.76))
    else:
        draw_text(12, 42,
                  "UP/DOWN : Camera Height     LEFT/RIGHT : Rotate Camera",
                  color=(0.76,0.76,0.76))
    draw_text(12, 18, "Right-Click : Toggle POV     ESC : Quit",
              color=(0.76,0.76,0.76))

    # ── Station name drawn as 3D-world billboard on canopy fascia ────────────
    # This text appears physically ON the canopy sign panel in 3D space
    # We draw it as a 2D overlay positioned to match the 3D panel
    # (approximate screen position; works well in default 3rd-person view)
    draw_text_large(WIN_W//2-178, 468,
                    "openGL Filling Station", color=(1.0, 0.92, 0.15))

    glutSwapBuffers()


# ═══════════════════════════════════════════════════════════════════════════════
#  TIMER / ANIMATION
# ═══════════════════════════════════════════════════════════════════════════════
def timer_func(value):
    global last_time
    now = time.time()
    dt  = now - last_time
    last_time = now
    if dt > 0.1: dt = 0.1   # clamp large gaps

    update_simulation(dt)
    glutPostRedisplay()
    glutTimerFunc(16, timer_func, 0)   # ~60 fps


# ═══════════════════════════════════════════════════════════════════════════════
#  INPUT
# ═══════════════════════════════════════════════════════════════════════════════
def mouse_listener(button, state, x, y):
    global is_first_person
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        is_first_person = not is_first_person
        mode = "First-Person" if is_first_person else "Third-Person"
        print(f"  View -> {mode}")
    glutPostRedisplay()

def special_key(key, x, y):
    global cam_angle, cam_height, fp_yaw, fp_pitch
    if is_first_person:
        if key == GLUT_KEY_LEFT:   fp_yaw  -= 5
        if key == GLUT_KEY_RIGHT:  fp_yaw  += 5
        if key == GLUT_KEY_UP:     fp_pitch = min(fp_pitch+3, 60)
        if key == GLUT_KEY_DOWN:   fp_pitch = max(fp_pitch-3,-60)
    else:
        if key == GLUT_KEY_UP:     cam_height = min(cam_height+30, 2000)
        if key == GLUT_KEY_DOWN:   cam_height = max(cam_height-30, 60)
        if key == GLUT_KEY_LEFT:   cam_angle -= 0.05
        if key == GLUT_KEY_RIGHT:  cam_angle += 0.05
    glutPostRedisplay()

def keyboard_listener(key, x, y):
    if key == b'\x1b':
        sys.exit(0)
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
    glClearColor(0.46, 0.68, 0.86, 1.0)

    glutDisplayFunc(show_screen)
    glutSpecialFunc(special_key)
    glutKeyboardFunc(keyboard_listener)
    glutMouseFunc(mouse_listener)

    last_time = time.time()
    glutTimerFunc(16, timer_func, 0)

    print("=" * 58)
    print("   openGL Filling Station  –  Vehicle Queue Simulation")
    print("=" * 58)
    print("   Right-Click        : Toggle 3rd / 1st person POV")
    print("   Arrow Keys (3rd)   : UP/DOWN=height | L/R=rotate")
    print("   Arrow Keys (1st)   : Look around (seller's eye)")
    print("   ESC                : Quit")
    print("   Vehicles spawn automatically and queue at the pump")
    print("=" * 58)

    glutMainLoop()

if __name__ == "__main__":
    main()