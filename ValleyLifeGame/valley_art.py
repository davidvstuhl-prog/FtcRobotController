"""Valley Life art. Every sprite is drawn with code, no image files.

Shapes are drawn 3x bigger and smooth-scaled down, which gives soft anti-aliased edges.
Light comes from the top-left. Things get a dark outline, a shaded side, a highlight and a
ground shadow; that is what gives the 2.5D "toy diorama" look.

The browser version uses these exact sprites: build_web.py packs them into one image atlas.
"""
import math
import random

import pygame

SS = 3                      # supersampling factor
OUT = (40, 30, 38)          # outline colour

GRASS, SAND, SHALLOW, DEEP, PATH, CAVE, WALL, MOUNT, BRIDGE, PLOTT = range(10)
TILE_COL = {GRASS: (92, 166, 74), SAND: (220, 202, 140), SHALLOW: (74, 160, 218), DEEP: (36, 100, 182),
            PATH: (184, 152, 108), CAVE: (88, 80, 92), WALL: (52, 44, 60), MOUNT: (124, 120, 112),
            BRIDGE: (150, 106, 64), PLOTT: (116, 80, 50)}
WATER = (SHALLOW, DEEP)

_FONTS = {}


def font(size):
    if size not in _FONTS:
        f = pygame.font.Font(None, max(8, round(size)))
        f.set_bold(True)
        _FONTS[size] = f
    return _FONTS[size]


def sh(c, d):
    return tuple(max(0, min(255, int(k + d))) for k in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Pen:
    """Draws on a 3x surface using final-size coordinates."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.s = pygame.Surface((w * SS, h * SS), pygame.SRCALPHA)

    def _p(self, x, y):
        return (round(x * SS), round(y * SS))

    def circle(self, col, x, y, r):
        if r > 0:
            pygame.draw.circle(self.s, col, self._p(x, y), max(1, round(r * SS)))

    def ell(self, col, cx, cy, rx, ry):
        if rx > 0 and ry > 0:
            pygame.draw.ellipse(self.s, col, pygame.Rect(round((cx - rx) * SS), round((cy - ry) * SS),
                                                          max(1, round(2 * rx * SS)), max(1, round(2 * ry * SS))))

    def rect(self, col, x, y, w, h, r=0):
        pygame.draw.rect(self.s, col, pygame.Rect(round(x * SS), round(y * SS), max(1, round(w * SS)), max(1, round(h * SS))),
                         border_radius=max(0, round(r * SS)))

    def poly(self, col, pts):
        pygame.draw.polygon(self.s, col, [self._p(x, y) for x, y in pts])

    def line(self, col, x1, y1, x2, y2, w=1.0):
        pygame.draw.line(self.s, col, self._p(x1, y1), self._p(x2, y2), max(1, round(w * SS)))
        if w >= 1.5:
            self.circle(col, x1, y1, w / 2)
            self.circle(col, x2, y2, w / 2)

    def path(self, col, pts, w=1.0):
        for a, b in zip(pts, pts[1:]):
            self.line(col, a[0], a[1], b[0], b[1], w)

    # outlined shapes
    def oc(self, col, x, y, r, o=1.3):
        self.circle(OUT, x, y, r + o)
        self.circle(col, x, y, r)

    def oe(self, col, cx, cy, rx, ry, o=1.3):
        self.ell(OUT, cx, cy, rx + o, ry + o)
        self.ell(col, cx, cy, rx, ry)

    def orr(self, col, x, y, w, h, r=0, o=1.3):
        self.rect(OUT, x - o, y - o, w + 2 * o, h + 2 * o, r + o if r else 0)
        self.rect(col, x, y, w, h, r)

    def op(self, col, pts, o=1.3):
        P = [self._p(x, y) for x, y in pts]
        pygame.draw.polygon(self.s, OUT, P, max(1, round(2 * o * SS)))
        for x, y in pts:
            self.circle(OUT, x, y, o)
        pygame.draw.polygon(self.s, col, P)

    def ol(self, col, pts, w=2.0, o=1.2):
        self.path(OUT, pts, w + 2 * o)
        self.path(col, pts, w)

    def shadow(self, cx, cy, rx, ry, a=80):
        self.ell((0, 0, 0, a), cx, cy, rx, ry)

    def ball(self, col, x, y, r, o=1.3):
        self.oc(sh(col, -42), x, y, r, o)
        self.circle(col, x - r * 0.1, y - r * 0.12, r * 0.84)
        self.circle(sh(col, 40), x - r * 0.36, y - r * 0.4, r * 0.3)

    def sparkle(self, x, y, r, col=(255, 255, 230)):
        self.poly(col, [(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25),
                        (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)])

    def text(self, s, x, y, size, col=(255, 255, 255)):
        f = font(size * SS)
        img, shd = f.render(s, True, col), f.render(s, True, (0, 0, 0))
        r = img.get_rect(center=self._p(x, y))
        self.s.blit(shd, r.move(SS, SS))
        self.s.blit(img, r)

    def done(self):
        return pygame.transform.smoothscale(self.s, (self.w, self.h))


# ====================================================================== nature
TRUNK = {"Oak": (112, 76, 46), "Pine": (96, 62, 40), "Birch": (236, 232, 220), "Maple": (108, 68, 42), "Ancient": (150, 108, 60)}


def tree(name, col):
    p = Pen(96, 124)
    bx, by = 48, 112
    p.shadow(bx + 12, by - 1, 34, 10)
    tc = TRUNK[name]
    p.op(tc, [(bx - 12, by), (bx - 5, by - 12), (bx + 5, by - 12), (bx + 12, by)])
    p.orr(tc, bx - 6, by - 46, 12, 44, 3)
    p.rect(sh(tc, -35), bx + 1.5, by - 45, 4.5, 43, 2)
    p.rect(sh(tc, 28), bx - 5, by - 44, 2.2, 40, 1)
    if name == "Birch":
        for yy in (by - 40, by - 30, by - 19, by - 10):
            p.rect((40, 36, 40), bx - 5 + (yy % 3), yy, 6, 2)
    if name == "Pine":
        for i in range(4):
            w, yb = 30 - i * 6, by - 30 - i * 15
            tri = [(bx - w, yb), (bx + w, yb), (bx, yb - 30)]
            p.op(col, tri, 1.4)
            p.poly(sh(col, 22), [(bx - w + 2, yb - 1), (bx, yb - 1), (bx, yb - 28)])
            p.poly(sh(col, -24), [(bx, yb - 1), (bx + w - 2, yb - 1), (bx, yb - 28)])
            p.line(sh(col, 45), bx - w * 0.55, yb - 6, bx - w * 0.2, yb - 14, 1.2)
        return p.done(), bx, by
    big = 1.2 if name == "Ancient" else 1.0
    cy = by - 62
    blobs = [(-20, 8, 17), (20, 8, 17), (0, 12, 20), (-12, -10, 17), (12, -10, 17), (0, -22, 16)]
    blobs = [(x * big, y * big, r * big) for x, y, r in blobs]
    for x, y, r in blobs:
        p.circle(OUT, bx + x + 1, cy + y + 1.5, r + 1.8)
    for x, y, r in blobs:
        p.circle(sh(col, -48), bx + x + 2, cy + y + 3, r)
    rnd = random.Random(name)
    for x, y, r in blobs:
        c = col
        if name == "Maple" and rnd.random() < 0.4:
            c = (205, 60, 40)
        p.circle(c, bx + x - 1, cy + y - 1, r * 0.86)
    for x, y, r in blobs:
        p.circle(sh(col, 30), bx + x - r * 0.32, cy + y - r * 0.36, r * 0.42)
    for _ in range(14):
        x, y, r = rnd.choice(blobs)
        a = rnd.random() * math.tau
        p.circle(sh(col, 55), bx + x + math.cos(a) * r * 0.5, cy + y + math.sin(a) * r * 0.5, 1.4)
    if name == "Maple":
        for _ in range(5):
            x, y, r = rnd.choice(blobs)
            p.circle((255, 170, 70), bx + x + rnd.uniform(-6, 6), cy + y + rnd.uniform(-6, 6), 2)
    if name == "Ancient":
        for _ in range(6):
            x, y, r = rnd.choice(blobs)
            p.sparkle(bx + x + rnd.uniform(-8, 8), cy + y + rnd.uniform(-8, 8), 3.5)
    return p.done(), bx, by


def stump(name):
    p = Pen(96, 124)
    bx, by = 48, 112
    tc = TRUNK[name]
    p.shadow(bx + 6, by - 1, 16, 5)
    p.op(tc, [(bx - 12, by), (bx - 8, by - 6), (bx + 8, by - 6), (bx + 12, by)])
    p.orr(tc, bx - 9, by - 15, 18, 13, 3)
    p.rect(sh(tc, -35), bx + 2, by - 14, 6, 11, 2)
    p.oe((214, 172, 116), bx, by - 15, 9, 4)
    p.ell((180, 136, 88), bx, by - 15, 5.5, 2.4)
    p.ell((214, 172, 116), bx, by - 15, 3.5, 1.4)
    p.circle((150, 110, 70), bx, by - 15, 0.9)
    return p.done(), bx, by


def ore(name, tier, col):
    p = Pen(64, 60)
    p.shadow(36, 49, 25, 7)
    base = (120, 116, 128)
    if name == "Coal":
        base = (90, 86, 96)
    pts = [(9, 48), (7, 34), (17, 20), (33, 14), (50, 20), (57, 35), (55, 48)]
    p.op(base, pts, 1.5)
    p.poly(sh(base, 36), [(12, 31), (18, 22), (33, 16), (48, 22), (45, 31), (29, 34)])
    p.poly(sh(base, -30), [(45, 31), (48, 22), (50, 21), (56, 35), (54, 47), (44, 47)])
    p.path(sh(base, -45), [(29, 34), (30, 44)], 1.2)
    p.path(sh(base, -45), [(45, 31), (44, 46)], 1.2)
    rnd = random.Random(name)
    if name == "Stone":
        for _ in range(6):
            p.circle(sh(base, rnd.choice((-25, 30))), rnd.uniform(16, 48), rnd.uniform(24, 42), rnd.uniform(1.2, 2.2))
    elif name == "Coal":
        for x, y in ((20, 30), (34, 25), (28, 40), (44, 38)):
            p.oc((30, 28, 34), x, y, 4.5)
            p.circle((90, 90, 110), x - 1.5, y - 1.5, 1.3)
    else:
        spots = [(21, 30), (37, 24), (29, 41), (46, 38)][:2 + min(2, tier)]
        for x, y in spots:
            s = 6.5 if tier >= 3 else 5.5
            gem = [(x, y - s * 1.3), (x + s * 0.75, y), (x, y + s), (x - s * 0.75, y)]
            p.op(col, gem, 1.1)
            p.poly(sh(col, 45), [(x, y - s * 1.3), (x, y + s), (x - s * 0.75, y)])
            p.line((255, 255, 255), x - s * 0.35, y - s * 0.4, x - s * 0.15, y - s * 0.85, 1)
    return p.done(), 32, 50


def rubble():
    p = Pen(64, 60)
    for x, y, r in ((20, 46, 5), (32, 48, 6), (44, 46, 4.5)):
        p.shadow(x + 2, y + 3, r, r * 0.35, 60)
        p.ball((120, 116, 128), x, y, r)
    return p.done(), 32, 50


# ====================================================================== buildings
def building(name, col, w, h, wtile=32):
    W, H = w * wtile, h * wtile
    p = Pen(W + 48, H + 70)
    fx, fy = 22, 60
    bottom = fy + H
    wall_h = 76
    wy = bottom - wall_h
    p.poly((0, 0, 0, 70), [(fx + W, bottom), (fx + W + 20, bottom - 10), (fx + W + 20, wy - 10), (fx + W, wy)])
    p.shadow(fx + W / 2 + 8, bottom + 1, W / 2 + 8, 6, 60)
    wall = (234, 216, 186) if name != "GEM STORE" else (214, 236, 246)
    # wall
    p.orr(wall, fx, wy, W, wall_h, 0, 1.5)
    for yy in range(int(wy) + 9, int(bottom) - 8, 9):
        p.line(sh(wall, -22), fx + 1, yy, fx + W - 1, yy, 1)
    p.rect(sh(wall, -26), fx + W - 12, wy + 1, 11, wall_h - 2)
    p.rect(sh(wall, -40), fx + 1, wy + 1, W - 2, 8)
    post = (140, 98, 64)
    for px_ in (fx, fx + W - 7):
        p.orr(post, px_, wy, 7, wall_h, 0, 1)
    stone = (150, 146, 150)
    p.orr(stone, fx - 2, bottom - 9, W + 4, 9, 2, 1.2)
    for i in range(int(W / 16) + 1):
        p.line(sh(stone, -30), fx + 6 + i * 16, bottom - 8, fx + 6 + i * 16, bottom - 1, 1)
    # roof (seen from above and in front)
    rc = col
    roof = [(fx - 10, wy + 4), (fx + W + 10, wy + 4), (fx + W - 4, fy - 36), (fx + 4, fy - 36)]
    p.op(rc, roof, 1.6)
    rows = int((wy + 4 - (fy - 36)) / 10)
    for i in range(1, rows + 1):
        t = i / (rows + 1)
        y = fy - 36 + (wy + 4 - (fy - 36)) * t
        xl, xr = fx + 4 - 14 * t, fx + W - 4 + 14 * t
        p.line(sh(rc, -28), xl + 2, y, xr - 2, y, 1.2)
        for k in range(int((xr - xl) / 14)):
            p.line(sh(rc, -28), xl + 7 + k * 14 + (i % 2) * 7, y - 9, xl + 7 + k * 14 + (i % 2) * 7, y, 1)
    p.poly(sh(rc, 30), [(fx + 6, fy - 34), (fx + W - 6, fy - 34), (fx + W - 7, fy - 29), (fx + 7, fy - 29)])
    p.orr(sh(rc, -45), fx - 12, wy + 2, W + 24, 9, 3, 1.4)
    dx = fx + W / 2
    # chimney / roof decoration
    if name in ("HOME", "KITCHEN"):
        cxm = fx + W - 38
        p.orr((160, 90, 70), cxm, fy - 52, 16, 30, 2)
        p.rect((120, 64, 50), cxm + 10, fy - 51, 5, 28)
        p.orr((110, 60, 48), cxm - 2, fy - 56, 20, 6, 2)
    if name == "GEM STORE":
        gx, gy = dx, fy - 40
        p.op((90, 230, 245), [(gx, gy - 26), (gx + 15, gy - 8), (gx, gy + 14), (gx - 15, gy - 8)], 1.6)
        p.poly((190, 250, 255), [(gx, gy - 26), (gx, gy + 14), (gx - 15, gy - 8)])
        p.sparkle(gx - 18, gy - 20, 4)
        p.sparkle(gx + 16, gy + 6, 3)
    if name == "PET HATCHERY":
        p.ball((255, 236, 220), dx, fy - 40, 13)
        for x, y in ((dx - 4, fy - 44), (dx + 5, fy - 38), (dx - 2, fy - 34)):
            p.circle((255, 150, 200), x, y, 2.3)
    if name == "UPGRADES":
        for bxp in (fx + 14, fx + W - 30):
            p.op((240, 200, 70), [(bxp, wy + 10), (bxp + 16, wy + 10), (bxp + 16, wy + 44), (bxp + 8, wy + 38), (bxp, wy + 44)], 1.1)
            p.sparkle(bxp + 8, wy + 22, 4, (130, 80, 200))
    # windows
    if name != "UPGRADES":
        for wx in (fx + 16, fx + W - 46):
            p.orr((248, 242, 232), wx - 2, wy + 22, 34, 28, 3, 1.3)
            p.rect((140, 200, 240), wx + 1, wy + 25, 28, 22)
            p.rect((190, 228, 250), wx + 1, wy + 25, 28, 8)
            p.line((248, 242, 232), wx + 15, wy + 25, wx + 15, wy + 47, 2)
            p.line((248, 242, 232), wx + 1, wy + 36, wx + 29, wy + 36, 2)
            p.line((255, 255, 255), wx + 4, wy + 44, wx + 11, wy + 28, 1.4)
            p.orr((130, 86, 54), wx - 3, wy + 50, 36, 6, 1, 1.1)
            for k, fc in enumerate(((255, 120, 150), (255, 220, 90), (180, 120, 255))):
                p.circle((70, 150, 60), wx + 4 + k * 12, wy + 49, 3.2)
                p.circle(fc, wx + 4 + k * 12, wy + 48, 2.2)
    # awnings
    if name in ("SHOP", "MARKET"):
        ac = (240, 240, 240)
        aw, ax0 = W - 44, fx + 22
        n = 8
        for k in range(n):
            c = col if k % 2 == 0 else ac
            x0 = ax0 + k * aw / n
            p.poly(OUT, [(x0 - 0.8, wy + 6), (x0 + aw / n + 0.8, wy + 6), (x0 + aw / n + 0.8, wy + 22), (x0 - 0.8, wy + 22)])
        for k in range(n):
            c = col if k % 2 == 0 else ac
            x0 = ax0 + k * aw / n
            p.poly(c, [(x0, wy + 7), (x0 + aw / n, wy + 7), (x0 + aw / n, wy + 21), (x0, wy + 21)])
            p.oc(c, x0 + aw / n / 2, wy + 21, aw / n / 2, 0.9)
    # door
    p.orr((104, 68, 44), dx - 18, bottom - 52, 36, 46, 4, 1.4)
    p.rect((156, 104, 62), dx - 14, bottom - 48, 28, 42, 3)
    for k in range(1, 4):
        p.line(sh((156, 104, 62), -25), dx - 14 + k * 7, bottom - 47, dx - 14 + k * 7, bottom - 7, 1)
    p.rect(sh((156, 104, 62), -40), dx + 7, bottom - 47, 7, 41)
    p.oc((255, 210, 70), dx + 8, bottom - 26, 2.2, 0.8)
    p.oe((170, 166, 170), dx, bottom - 3, 22, 4.5, 1.1)
    # extras
    if name == "MARKET":
        for cx0 in (fx + 6, fx + W - 30):
            p.orr((176, 124, 70), cx0, bottom - 26, 24, 18, 2)
            p.line(sh((176, 124, 70), -35), cx0, bottom - 17, cx0 + 24, bottom - 17, 1.2)
            for k, fc in enumerate(((240, 80, 60), (255, 200, 60), (120, 200, 80))):
                p.ball(fc, cx0 + 5 + k * 7, bottom - 28, 3.5, 0.8)
    if name == "KITCHEN":
        p.orr((150, 100, 60), fx + W - 30, bottom - 30, 20, 24, 6)
        p.line((90, 60, 40), fx + W - 30, bottom - 22, fx + W - 10, bottom - 22, 1.4)
        p.line((90, 60, 40), fx + W - 30, bottom - 13, fx + W - 10, bottom - 13, 1.4)
    if name == "HOME":
        p.orr((90, 90, 110), fx + W - 18, bottom - 34, 4, 28, 1)
        p.orr((70, 120, 200), fx + W - 26, bottom - 44, 18, 12, 4)
    # hanging sign
    sw = font(19 * SS).size(name)[0] / SS + 18
    sy = wy + 10 if name not in ("SHOP", "MARKET") else wy - 14
    p.line((70, 50, 40), dx - sw / 2 + 6, sy - 6, dx - sw / 2 + 6, sy, 1.2)
    p.line((70, 50, 40), dx + sw / 2 - 6, sy - 6, dx + sw / 2 - 6, sy, 1.2)
    p.orr(sh(col, -70), dx - sw / 2, sy, sw, 20, 4, 1.4)
    p.rect(sh(col, -40), dx - sw / 2 + 2, sy + 2, sw - 4, 3, 1)
    p.text(name, dx, sy + 11, 19)
    return p.done(), fx, fy


# ====================================================================== people
PALETTES = {}


def person(pal, d, f, swim=False):
    skin, shirt, pants, hair, hat = pal
    p = Pen(44, 62)
    cx, fy = 22, 56
    step = (0, 1, -1)[f]
    side = d in ("left", "right")
    s = 1 if d == "right" else -1
    if swim:
        hy = fy - 18
        p.orr(shirt, cx - 9, fy - 12, 18, 8, 4)
    else:
        p.shadow(cx, fy, 12, 4.2)
        hy = fy - 40
        legc, shoe = pants, (60, 44, 40)
        if not side:
            for k, sx_ in ((1, -1), (-1, 1)):
                lift = 2.5 if step == k else 0
                x0 = cx + sx_ * 4 - 3
                p.orr(legc, x0, fy - 15, 6, 12 - lift, 2)
                p.oe(shoe, x0 + 3, fy - 3 - lift, 3.8, 2.4, 1)
        else:
            for k, off in ((1, 4), (-1, -4)):
                o = off * step
                c = sh(legc, -25) if k == -1 else legc
                p.orr(c, cx - 3 + o, fy - 15, 6, 12, 2)
                p.oe(shoe, cx + o + s * 1.2, fy - 3, 4.2, 2.4, 1)
        # arms (behind body when walking sideways)
        if side:
            p.orr(sh(shirt, -30), cx - 2 - s * step * 3, fy - 30, 5, 13, 2.5)
        # body
        p.orr(shirt, cx - 9, fy - 31, 18, 18, 6)
        p.rect(sh(shirt, -32), cx + 3.5, fy - 30, 5, 16, 4)
        p.rect(sh(shirt, 26), cx - 8, fy - 29, 3, 12, 2)
        p.rect(sh(pants, -20), cx - 9, fy - 17, 18, 3)
        if not side:
            for sx_, a in ((-1, step), (1, -step)):
                ax = cx + sx_ * 11.5 - 2.5
                p.orr(shirt, ax, fy - 30 + a * 1.5, 5, 11, 2.5)
                p.oc(skin, ax + 2.5, fy - 18 + a * 1.5, 2.6, 1)
        else:
            p.orr(shirt, cx - 2 + s * step * 3, fy - 30, 5, 12, 2.5)
            p.oc(skin, cx + 0.5 + s * step * 3, fy - 17, 2.6, 1)
    # head
    p.oc(sh(skin, -26), cx, hy, 11)
    p.circle(skin, cx - 1.2, hy - 1.2, 9.8)
    p.circle(sh(skin, 25), cx - 4, hy - 4.5, 3.2)
    if d == "up":
        p.oc(hair, cx, hy - 1, 11)
        p.circle(sh(hair, 25), cx - 4, hy - 6, 3.5)
    else:
        p.ell(OUT, cx, hy - 7, 12.3, 6.8)
        p.ell(hair, cx, hy - 7, 11, 5.6)
        if side:
            p.circle(OUT, cx - s * 6, hy - 2.5, 6.6)
            p.circle(hair, cx - s * 6, hy - 2.5, 5.4)
        else:
            for k in (-2, -1, 1, 2):
                p.circle(hair, cx + k * 4, hy - 4 + abs(k) * 0.8, 2.6)
        p.circle(sh(hair, 30), cx - 4, hy - 9, 2.2)
        eyes = [(cx - 4, hy + 2.5), (cx + 4, hy + 2.5)] if not side else [(cx + s * 5.5, hy + 2.5)]
        for ex, ey in eyes:
            p.ell((30, 24, 30), ex, ey, 1.6, 2.3)
            p.circle((255, 255, 255), ex - 0.5, ey - 1, 0.7)
        cheeks = [(cx - 7, hy + 6), (cx + 7, hy + 6)] if not side else [(cx + s * 2, hy + 6)]
        for ex, ey in cheeks:
            p.ell((255, 150, 150), ex, ey, 2, 1.1)
    if hat:
        p.oe(hat, cx, hy - 9, 11.5, 5.4)
        p.circle(sh(hat, 30), cx - 4, hy - 11, 2)
        if d == "down":
            p.oe(sh(hat, -30), cx, hy - 5, 12, 2.4, 1)
        elif side:
            p.oe(sh(hat, -30), cx + s * 9, hy - 5, 7, 2.4, 1)
    return p.done(), cx, fy


# ====================================================================== animals
ANIMAL_LOOK = {
    "Rabbit": dict(z=9, col=(210, 200, 190), belly=(248, 244, 238), leg=0.25, lw=0.32, rx=0.85, ry=0.7, head=0.55),
    "Deer": dict(z=14, col=(178, 124, 74), belly=(242, 226, 200), leg=1.05, lw=0.2, rx=1.05, ry=0.55, head=0.42),
    "Boar": dict(z=13, col=(104, 76, 58), belly=(146, 116, 94), leg=0.5, lw=0.3, rx=1.0, ry=0.62, head=0.5),
    "Wolf": dict(z=12, col=(130, 130, 144), belly=(218, 218, 228), leg=0.75, lw=0.25, rx=1.0, ry=0.5, head=0.45),
    "Bear": dict(z=20, col=(98, 66, 44), belly=(152, 112, 78), leg=0.5, lw=0.42, rx=1.05, ry=0.75, head=0.5),
    "Golden Stag": dict(z=15, col=(242, 196, 62), belly=(255, 242, 176), leg=1.05, lw=0.2, rx=1.1, ry=0.58, head=0.42),
}


def animal(kind, f):
    L = ANIMAL_LOOK[kind]
    z, col, belly = L["z"], L["col"], L["belly"]
    W, H = int(z * 5.4 + 22), int(z * 4.8 + 22)
    p = Pen(W, H)
    cx, gy = W / 2 - z * 0.2, H - 8
    step = (0, 1, -1)[f]
    legL, lw, rx, ry = z * L["leg"], z * L["lw"], z * L["rx"], z * L["ry"]
    hop = -z * 0.35 if (kind == "Rabbit" and f == 1) else 0
    by = gy - legL - ry * 0.75 + hop
    p.shadow(cx + 2, gy, z * 1.3, z * 0.33)
    dark = sh(col, -38)
    # far legs
    if kind != "Rabbit":
        for lx, o in ((cx - rx * 0.5 + z * 0.2, -step), (cx + rx * 0.55 + z * 0.2, step)):
            x = lx + o * z * 0.15
            p.orr(sh(col, -50), x - lw / 2, by, lw, gy - by - 1, lw / 2, 1.1)
    # tail
    if kind == "Rabbit":
        p.oc((255, 255, 255), cx - rx * 0.95, by - ry * 0.2, z * 0.32)
    elif kind in ("Deer", "Golden Stag"):
        p.oe(belly, cx - rx * 0.98, by - ry * 0.45, z * 0.16, z * 0.24)
    elif kind == "Wolf":
        p.op(col, [(cx - rx * 0.8, by - ry * 0.4), (cx - rx * 1.55, by - ry * 1.1), (cx - rx * 1.45, by - ry * 0.2), (cx - rx * 0.8, by + ry * 0.2)])
        p.circle(belly, cx - rx * 1.45, by - ry * 0.8, z * 0.13)
    elif kind == "Boar":
        p.path(OUT, [(cx - rx, by - ry * 0.2), (cx - rx * 1.25, by - ry * 0.5), (cx - rx * 1.15, by - ry * 0.8)], 2.6)
        p.path(dark, [(cx - rx, by - ry * 0.2), (cx - rx * 1.25, by - ry * 0.5), (cx - rx * 1.15, by - ry * 0.8)], 1.4)
    else:
        p.oc(dark, cx - rx * 0.95, by - ry * 0.3, z * 0.16)
    # body
    p.oe(dark, cx, by, rx, ry, 1.4)
    p.ell(col, cx - 1, by - 1.3, rx * 0.93, ry * 0.85)
    p.ell(belly, cx + rx * 0.05, by + ry * 0.5, rx * 0.6, ry * 0.32)
    p.ell(sh(col, 32), cx - rx * 0.3, by - ry * 0.48, rx * 0.42, ry * 0.22)
    if kind in ("Deer", "Golden Stag"):
        for k in range(5):
            p.circle((255, 248, 230), cx - rx * 0.5 + k * rx * 0.22, by - ry * 0.25 + (k % 2) * ry * 0.25, z * 0.07)
    if kind == "Boar":
        for k in range(6):
            x = cx - rx * 0.6 + k * rx * 0.22
            p.poly(sh(col, -55), [(x - 2.5, by - ry * 0.82), (x, by - ry * 1.25), (x + 2.5, by - ry * 0.82)])
    # near legs
    if kind == "Rabbit":
        p.oe(sh(col, -10), cx - rx * 0.45, gy - 2 + hop * 0.3, z * 0.42, z * 0.2, 1.1)
        p.oe(sh(col, -10), cx + rx * 0.45, gy - 2 + hop * 0.3, z * 0.3, z * 0.18, 1.1)
    else:
        for lx, o in ((cx - rx * 0.5, step), (cx + rx * 0.55, -step)):
            x = lx + o * z * 0.15
            p.orr(sh(col, -12), x - lw / 2, by + ry * 0.2, lw, gy - by - ry * 0.2, lw / 2, 1.2)
            hc = (60, 44, 36) if kind in ("Deer", "Golden Stag", "Boar") else sh(col, -45)
            p.oe(hc, x, gy - 1, lw * 0.62, lw * 0.4, 0.9)
    # neck + head
    hr = z * L["head"]
    if kind in ("Deer", "Golden Stag"):
        hx, hy = cx + rx * 1.0, by - ry * 1.55
        p.op(col, [(cx + rx * 0.45, by - ry * 0.5), (hx - hr * 0.7, hy), (hx + hr * 0.2, hy + hr * 0.8), (cx + rx * 0.9, by + ry * 0.2)])
    elif kind == "Wolf":
        hx, hy = cx + rx * 1.0, by - ry * 0.9
    elif kind == "Rabbit":
        hx, hy = cx + rx * 0.75, by - ry * 0.75
    else:
        hx, hy = cx + rx * 0.95, by - ry * 0.3
    # ears behind head
    if kind == "Rabbit":
        for ox, c in ((-0.15, sh(col, -20)), (-0.45, col)):
            p.oe(c, hx + hr * ox, hy - hr * 1.5, hr * 0.28, hr * 0.85)
            p.ell((245, 170, 180), hx + hr * ox, hy - hr * 1.45, hr * 0.13, hr * 0.6)
    elif kind == "Wolf":
        for ox in (-0.55, 0.05):
            p.op(sh(col, -15), [(hx + hr * ox - hr * 0.3, hy - hr * 0.5), (hx + hr * ox, hy - hr * 1.5), (hx + hr * ox + hr * 0.35, hy - hr * 0.55)])
    elif kind == "Bear":
        for ox in (-0.65, 0.35):
            p.oc(col, hx + hr * ox, hy - hr * 0.85, hr * 0.35)
            p.circle(belly, hx + hr * ox, hy - hr * 0.85, hr * 0.17)
    elif kind == "Boar":
        p.op(dark, [(hx - hr * 0.6, hy - hr * 0.5), (hx - hr * 0.35, hy - hr * 1.35), (hx - hr * 0.05, hy - hr * 0.6)])
    elif kind in ("Deer", "Golden Stag"):
        ac = (255, 244, 180) if kind == "Golden Stag" else (130, 96, 64)
        big = 1.35 if kind == "Golden Stag" else 1.0
        for sx_ in (-0.4, 0.15):
            bx_ = hx + hr * sx_
            p.ol(ac, [(bx_, hy - hr * 0.6), (bx_ - hr * 0.3 * big, hy - hr * 2.0 * big), (bx_ - hr * 0.9 * big, hy - hr * 2.8 * big)], 1.8, 1)
            p.ol(ac, [(bx_ - hr * 0.2 * big, hy - hr * 1.5 * big), (bx_ + hr * 0.5 * big, hy - hr * 2.3 * big)], 1.6, 1)
            p.ol(ac, [(bx_ - hr * 0.55 * big, hy - hr * 2.4 * big), (bx_ - hr * 0.1 * big, hy - hr * 3.0 * big)], 1.4, 1)
        p.op(col, [(hx - hr * 0.7, hy - hr * 0.3), (hx - hr * 1.5, hy - hr * 0.9), (hx - hr * 0.6, hy - hr * 0.8)])
    p.oc(dark, hx, hy, hr, 1.3)
    p.circle(col, hx - hr * 0.1, hy - hr * 0.12, hr * 0.86)
    p.circle(sh(col, 34), hx - hr * 0.35, hy - hr * 0.4, hr * 0.3)
    snout = {"Bear": belly, "Boar": (220, 150, 140), "Wolf": belly, "Rabbit": belly}.get(kind, sh(col, 20))
    snl = 0.75 if kind in ("Wolf", "Deer", "Golden Stag") else 0.5
    p.oe(snout, hx + hr * 0.75, hy + hr * 0.25, hr * snl, hr * 0.42, 1.1)
    p.oc((40, 30, 34), hx + hr * (0.75 + snl * 0.85), hy + hr * 0.15, hr * 0.17, 0.6)
    if kind == "Boar":
        p.op((250, 246, 230), [(hx + hr * 0.7, hy + hr * 0.55), (hx + hr * 1.05, hy + hr * 0.05), (hx + hr * 0.95, hy + hr * 0.6)], 0.9)
    p.circle((30, 24, 30), hx + hr * 0.25, hy - hr * 0.22, hr * 0.17)
    p.circle((255, 255, 255), hx + hr * 0.2, hy - hr * 0.3, hr * 0.07)
    if kind == "Golden Stag":
        p.sparkle(cx - rx * 0.4, by - ry * 1.2, 3.5)
        p.sparkle(cx + rx * 0.5, by + ry * 0.2, 2.5)
    return p.done(), W / 2, gy


# ====================================================================== pets
def pet(name, col, rar_i):
    p = Pen(72, 76)
    cx, cy = 36, 46
    p.shadow(cx, 70, 18, 5)
    belly = sh(col, 45) if sum(col) < 600 else sh(col, -18)
    if name == "Panda":
        belly = (250, 250, 250)
    if name == "Penguin":
        belly = (250, 250, 250)
    # behind-body features
    if name == "Hedgehog":
        for k in range(9):
            a = math.pi * (0.95 + k * 0.14)
            p.op((120, 92, 74), [(cx + math.cos(a) * 14, cy + math.sin(a) * 14), (cx + math.cos(a) * 26, cy + math.sin(a) * 26),
                                (cx + math.cos(a + 0.2) * 15, cy + math.sin(a + 0.2) * 15)], 1)
    if name in ("Phoenix", "Dragon", "Owl", "Duck", "Bee"):
        wc = {"Phoenix": (255, 200, 60), "Dragon": (180, 30, 30), "Owl": (140, 110, 80), "Duck": (240, 200, 70), "Bee": (220, 240, 255)}[name]
        for s in (-1, 1):
            p.op(wc, [(cx + s * 12, cy - 6), (cx + s * 30, cy - 18), (cx + s * 26, cy + 2), (cx + s * 14, cy + 6)])
    if name in ("Fox", "Beaver", "Cosmic Cat", "Kraken"):
        if name == "Fox":
            p.op(col, [(cx + 12, cy + 10), (cx + 32, cy - 8), (cx + 26, cy + 14)])
            p.circle((255, 255, 255), cx + 30, cy - 5, 3)
        elif name == "Beaver":
            p.oe((90, 60, 40), cx + 20, cy + 16, 12, 6)
        elif name == "Cosmic Cat":
            p.ol(col, [(cx + 14, cy + 12), (cx + 26, cy), (cx + 24, cy - 14)], 4)
    if name == "Kraken":
        for k in range(5):
            x = cx - 16 + k * 8
            p.ol(col, [(x, cy + 10), (x - 3, cy + 20), (x + 2, cy + 27)], 4.5)
    # ears
    if name == "Bunny":
        for s in (-1, 1):
            p.oe(col, cx + s * 7, cy - 26, 4.5, 13)
            p.ell((250, 180, 190), cx + s * 7, cy - 25, 2.2, 9)
    elif name in ("Fox", "Cosmic Cat"):
        for s in (-1, 1):
            p.op(col, [(cx + s * 4, cy - 14), (cx + s * 15, cy - 30), (cx + s * 17, cy - 10)])
            p.poly((40, 30, 30) if name == "Fox" else (240, 190, 255), [(cx + s * 8, cy - 15), (cx + s * 14, cy - 25), (cx + s * 15, cy - 13)])
    elif name in ("Panda", "Otter", "Mole", "Hedgehog", "Beaver"):
        for s in (-1, 1):
            p.oc((40, 40, 44) if name == "Panda" else sh(col, -20), cx + s * 12, cy - 15, 5.5)
    elif name == "Golden Retriever":
        for s in (-1, 1):
            p.oe(sh(col, -30), cx + s * 16, cy - 4, 5.5, 10)
    elif name == "Owl":
        for s in (-1, 1):
            p.op(sh(col, -25), [(cx + s * 6, cy - 16), (cx + s * 15, cy - 27), (cx + s * 16, cy - 12)])
    elif name == "Unicorn":
        for k, mc in enumerate(((255, 120, 160), (255, 210, 90), (120, 220, 255), (180, 140, 255))):
            p.oc(mc, cx + 12 - k * 2, cy - 14 + k * 6, 5)
    elif name == "Dragon":
        for s in (-1, 1):
            p.op((255, 230, 160), [(cx + s * 6, cy - 16), (cx + s * 11, cy - 30), (cx + s * 13, cy - 14)])
    elif name == "Phoenix":
        for k, fc in enumerate(((255, 90, 40), (255, 170, 40), (255, 230, 90))):
            p.op(fc, [(cx - 6 + k * 6, cy - 16), (cx - 3 + k * 6, cy - 32 + k * 3), (cx + k * 6, cy - 16)], 1)
    elif name == "Bee":
        for s in (-1, 1):
            p.ol((40, 34, 30), [(cx + s * 4, cy - 16), (cx + s * 9, cy - 28)], 1.6)
            p.oc((40, 34, 30), cx + s * 9, cy - 28, 2.5)
    # body
    p.oc(sh(col, -40), cx, cy, 18, 1.5)
    p.circle(col, cx - 1.5, cy - 1.8, 15.8)
    p.ell(belly, cx, cy + 7, 11, 8)
    p.circle(sh(col, 40), cx - 7, cy - 8, 4.5)
    if name == "Bee":
        for yy in (cy - 3, cy + 6):
            p.rect((40, 34, 30), cx - 15, yy, 30, 4, 2)
    if name == "Panda":
        for s in (-1, 1):
            p.ell((40, 40, 44), cx + s * 6, cy - 2, 4.5, 5.5)
    if name == "Unicorn":
        p.op((255, 220, 90), [(cx - 3, cy - 15), (cx, cy - 33), (cx + 3, cy - 15)], 1)
    if name == "Cosmic Cat":
        rnd = random.Random(1)
        for _ in range(6):
            p.sparkle(cx + rnd.uniform(-12, 12), cy + rnd.uniform(-12, 12), 2.2, (255, 255, 200))
    if name == "Dragon":
        for k in range(3):
            p.rect((255, 210, 120), cx - 5, cy + 2 + k * 4, 10, 2.5, 1)
    # feet
    fc = (240, 150, 40) if name in ("Duck", "Penguin") else sh(col, -30)
    for s in (-1, 1):
        p.oe(fc, cx + s * 8, cy + 17, 5, 3, 1)
    # face
    eye_c = (30, 24, 30)
    if name == "Frog":
        for s in (-1, 1):
            p.oc(col, cx + s * 8, cy - 14, 6)
            p.circle((255, 255, 255), cx + s * 8, cy - 14, 4)
            p.circle(eye_c, cx + s * 8.5, cy - 13.5, 2.3)
        p.path(OUT, [(cx - 8, cy + 2), (cx, cy + 5), (cx + 8, cy + 2)], 1.4)
    else:
        ey = cy - 3
        for s in (-1, 1):
            if name == "Owl":
                p.oc((255, 170, 60), cx + s * 6.5, ey, 6)
            if name == "Mole":
                p.ell(eye_c, cx + s * 5, ey, 1.4, 1)
                continue
            p.ell(eye_c if name != "Panda" else (255, 255, 255), cx + s * 6, ey, 3, 3.8)
            if name == "Panda":
                p.ell(eye_c, cx + s * 6, ey, 1.8, 2.4)
            p.circle((255, 255, 255), cx + s * 6 - 1, ey - 1.6, 1.2)
            p.ell((255, 150, 160), cx + s * 10, ey + 5, 2.3, 1.2)
        if name in ("Duck", "Penguin", "Owl"):
            p.op((250, 160, 40), [(cx - 4, cy + 2), (cx + 4, cy + 2), (cx, cy + 7)], 0.9)
        elif name == "Mole":
            p.oc((255, 140, 170), cx, cy + 2, 3.2)
        elif name == "Beaver":
            p.oc((60, 40, 30), cx, cy + 1, 2)
            p.orr((255, 255, 245), cx - 2.6, cy + 3, 5.2, 4.5, 1, 0.8)
        elif name == "Golden Retriever":
            p.oc((60, 40, 30), cx, cy + 2, 2.2)
            p.oe((255, 120, 140), cx, cy + 7, 2.5, 3, 0.8)
        else:
            p.oc((60, 40, 40), cx, cy + 2, 1.6, 0.6)
            p.path(OUT, [(cx - 3, cy + 5), (cx, cy + 6), (cx + 3, cy + 5)], 1)
    if rar_i >= 4:
        p.sparkle(cx - 20, cy - 18, 3.5)
        p.sparkle(cx + 21, cy - 4, 2.5)
    return p.done(), 36, 70


# ====================================================================== item icons
LOG_LOOK = {"Oak Log": ((124, 84, 50), (216, 172, 114)), "Pine Log": ((88, 54, 36), (232, 196, 136)),
            "Birch Log": ((238, 234, 224), (232, 206, 160)), "Maple Log": ((170, 70, 44), (236, 164, 124)),
            "Ancient Log": ((224, 172, 52), (255, 236, 150))}


def _fish(p, col, kind="fish"):
    if kind == "eel":
        p.ol(col, [(6, 30), (14, 20), (24, 28), (34, 18), (42, 22)], 6, 1.3)
        p.circle((30, 24, 30), 40, 20, 1.6)
        return
    p.op(col, [(11, 24), (3, 15), (6, 24), (3, 33)], 1.2)
    p.op(sh(col, -20), [(18, 17), (26, 10), (32, 17)], 1.1)
    p.oe(sh(col, -35), 25, 25, 16, 9.5)
    p.ell(col, 24.5, 24, 15, 8.3)
    p.ell(sh(col, 45), 26, 28, 10, 4)
    p.ell(sh(col, 55), 22, 20, 7, 2.2)
    p.path(sh(col, -50), [(33, 19), (31, 25), (33, 31)], 1.2)
    p.circle((255, 255, 255), 36, 22, 2.8)
    p.circle((30, 24, 30), 36.6, 22.2, 1.6)
    if kind == "sword":
        p.ol(sh(col, 30), [(40, 24), (47, 22)], 1.6, 0.8)
    if kind == "shark":
        p.op(sh(col, -10), [(20, 17), (24, 5), (30, 17)], 1.1)


def _plate(p):
    p.oe((236, 236, 240), 24, 33, 20, 9)
    p.ell((210, 214, 222), 24, 33, 14, 5.5)


def _glass(p, col):
    p.op((220, 236, 250), [(14, 10), (34, 10), (31, 42), (17, 42)], 1.3)
    p.poly(col, [(15.5, 18), (32.5, 18), (30.5, 40), (17.5, 40)])
    p.poly(sh(col, 40), [(15.5, 18), (20, 18), (19, 40), (17.5, 40)])
    p.ol((255, 120, 150), [(28, 4), (25, 22)], 2, 0.8)


def _rock(p, col, crystal=True):
    p.op((128, 124, 136), [(6, 38), (8, 22), (20, 12), (36, 14), (44, 28), (40, 40)], 1.3)
    p.poly((160, 156, 168), [(10, 24), (20, 14), (35, 16), (32, 24), (18, 28)])
    if crystal:
        for x, y, s in ((19, 26, 6), (31, 28, 7)):
            p.op(col, [(x, y - s * 1.3), (x + s * 0.75, y), (x, y + s), (x - s * 0.75, y)], 1)
            p.poly(sh(col, 45), [(x, y - s * 1.3), (x, y + s), (x - s * 0.75, y)])


def icon(name, cat, col):
    p = Pen(48, 48)
    if cat == "fish":
        if name == "Old Boot":
            p.op((112, 78, 50), [(12, 8), (24, 8), (24, 28), (40, 32), (40, 40), (10, 40)], 1.3)
            p.rect((80, 52, 34), 10, 37, 30, 4)
            for y in (14, 20, 26):
                p.line((230, 220, 200), 13, y, 23, y, 1)
        elif name == "Seaweed":
            for x, c in ((14, (60, 150, 70)), (24, (80, 180, 80)), (34, (50, 130, 60))):
                p.ol(c, [(x, 42), (x - 4, 32), (x + 3, 22), (x - 2, 10)], 3.5)
        elif name == "Glow Shrimp":
            p.ol(col, [(10, 30), (16, 38), (28, 38), (36, 28), (34, 16)], 7, 1.3)
            for k in range(4):
                p.line(sh(col, -40), 14 + k * 6, 31, 16 + k * 6, 37, 1)
            p.circle((30, 24, 30), 34, 17, 1.5)
            p.sparkle(40, 10, 4, (220, 255, 240))
        elif name in ("Crystal Eel", "Lake Serpent", "Abyss Leviathan"):
            _fish(p, col, "eel")
            if name != "Crystal Eel":
                p.sparkle(10, 12, 4)
        elif name == "Fish Fillet":
            p.op((248, 160, 140), [(6, 30), (14, 16), (38, 14), (44, 24), (34, 36), (12, 38)], 1.3)
            for k in range(4):
                p.path((255, 225, 215), [(14 + k * 7, 18), (18 + k * 7, 26), (14 + k * 7, 35)], 1.4)
        elif name == "Fish Scales":
            for x, y in ((16, 30), (28, 30), (22, 22), (34, 22), (28, 14)):
                p.oc(col, x, y, 7)
                p.circle(sh(col, 50), x - 2, y - 2, 2.5)
        else:
            _fish(p, col, "sword" if name == "Swordfish" else "shark" if name == "Ghost Shark" else "fish")
            if name in ("Golden Carp", "River King", "Moonfish"):
                p.sparkle(40, 10, 4)
    elif cat == "wood":
        bark, end = LOG_LOOK.get(name, (col, sh(col, 60)))
        p.orr(bark, 5, 15, 33, 19, 8, 1.4)
        p.rect(sh(bark, -30), 7, 28, 30, 5, 2)
        p.rect(sh(bark, 25), 8, 17, 28, 3, 1)
        if name == "Birch Log":
            for x, y in ((11, 21), (20, 27), (27, 19), (15, 30)):
                p.rect((40, 36, 40), x, y, 5, 1.8)
        else:
            for y in (21, 26):
                p.path(sh(bark, -40), [(9, y), (17, y + 1.5), (25, y - 1), (33, y)], 1.1)
        p.oe(end, 37, 24.5, 6.5, 9.5)
        p.ell(sh(end, -30), 37, 24.5, 4, 6)
        p.ell(end, 37, 24.5, 2.4, 3.6)
        p.circle(sh(end, -45), 37, 24.5, 0.9)
        if name == "Ancient Log":
            p.sparkle(14, 9, 4)
            p.sparkle(42, 40, 3)
    elif cat == "ore":
        if name == "Stone":
            p.ball((150, 146, 156), 24, 26, 15)
        elif name == "Coal":
            for x, y, r in ((18, 28, 9), (30, 24, 10), (26, 35, 7)):
                p.ball((52, 50, 58), x, y, r)
        else:
            _rock(p, col)
    elif cat == "crop":
        if name == "Carrot":
            p.op(col, [(12, 14), (34, 20), (40, 44)], 1.3)
            for y in (20, 26, 32):
                p.line(sh(col, -40), 20 + (y - 20) * 0.6, y, 26 + (y - 20) * 0.6, y + 2, 1)
            for a in (-0.5, 0, 0.5):
                p.ol((70, 170, 70), [(14, 14), (14 + math.cos(-2.2 + a) * 12, 14 + math.sin(-2.2 + a) * 12)], 2.4, 0.9)
        elif name == "Wheat":
            for x in (17, 24, 31):
                p.ol((190, 160, 70), [(x, 44), (x, 14)], 1.6, 0.8)
                for k in range(4):
                    p.oe(col, x - 2.3, 12 + k * 5, 2.2, 3, 0.8)
                    p.oe(col, x + 2.3, 14 + k * 5, 2.2, 3, 0.8)
        elif name == "Corn":
            p.op((90, 170, 70), [(24, 44), (10, 26), (18, 20)], 1.1)
            p.op((90, 170, 70), [(24, 44), (38, 26), (30, 20)], 1.1)
            p.oe(col, 24, 22, 7, 16)
            for y in range(10, 34, 4):
                for x in (20, 24, 28):
                    p.circle(sh(col, 30), x, y, 1.4)
        elif name == "Berry":
            for x, y in ((18, 28), (30, 28), (24, 19), (24, 34)):
                p.ball(col, x, y, 7)
            p.op((80, 170, 80), [(24, 12), (34, 6), (32, 14)], 1)
        elif name == "Pumpkin":
            for x, r in ((14, 10), (34, 10), (24, 12)):
                p.oe(col if x == 24 else sh(col, -20), x, 28, r, 13)
            p.circle(sh(col, 45), 20, 22, 3)
            p.orr((100, 140, 60), 22, 10, 5, 7, 1, 1)
        elif name == "Watermelon":
            p.op((70, 160, 70), [(4, 18), (44, 18), (24, 44)], 1.3)
            p.poly((240, 80, 90), [(9, 20), (39, 20), (24, 38)])
            for x, y in ((18, 24), (24, 28), (30, 24), (24, 22)):
                p.ell((40, 30, 30), x, y, 1.1, 1.7)
        elif name == "Dragonfruit":
            p.oe(col, 24, 27, 13, 16)
            for x, y in ((16, 18), (32, 20), (14, 32), (34, 34), (24, 12)):
                p.op((110, 200, 90), [(x - 3, y + 2), (x, y - 6), (x + 3, y + 2)], 0.9)
            p.circle(sh(col, 50), 19, 22, 3)
        elif name == "Starfruit":
            pts = []
            for k in range(10):
                r = 19 if k % 2 == 0 else 8
                a = -math.pi / 2 + k * math.pi / 5
                pts.append((24 + math.cos(a) * r, 25 + math.sin(a) * r))
            p.op(col, pts, 1.3)
            p.circle(sh(col, 50), 20, 20, 3)
            p.sparkle(40, 8, 4)
        else:   # Tomato and fallback
            p.ball(col, 24, 27, 15)
            p.op((80, 170, 80), [(16, 13), (24, 16), (32, 13), (26, 18), (24, 24), (22, 18)], 1)
    elif cat == "food":
        if name in ("Berry Juice", "Melon Smoothie"):
            _glass(p, col)
        elif name in ("Veggie Stew", "Pumpkin Soup"):
            p.op((200, 160, 120), [(6, 24), (42, 24), (36, 40), (12, 40)], 1.3)
            p.oe(col, 24, 24, 18, 6)
            for x in (16, 24, 31):
                p.circle(sh(col, -40) if x != 24 else (90, 170, 80), x, 23, 2.4)
            for x in (18, 28):
                p.path((235, 235, 240), [(x, 18), (x - 2, 12), (x + 1, 6)], 1.2)
        elif name == "Berry Pie":
            p.op((230, 180, 110), [(6, 34), (24, 10), (42, 34)], 1.3)
            p.poly(col, [(12, 32), (24, 16), (36, 32)])
            p.rect((240, 200, 140), 6, 32, 36, 6, 2)
        elif name == "Fish Tacos":
            _plate(p)
            p.op((240, 200, 90), [(8, 30), (24, 12), (40, 30)], 1.3)
            for x, c in ((16, (90, 170, 80)), (24, (230, 60, 50)), (32, (250, 170, 140))):
                p.circle(c, x, 26, 3.5)
        elif name == "Roast Meat":
            _plate(p)
            p.ol((240, 236, 225), [(30, 30), (40, 16)], 3, 1)
            p.oc((240, 236, 225), 41, 14, 3, 1)
            p.oe((160, 80, 40), 22, 30, 12, 9)
            p.ell((200, 120, 60), 20, 27, 8, 4)
        elif name == "Hunter's Feast":
            _plate(p)
            p.oe((160, 80, 40), 16, 28, 9, 7)
            p.oe((230, 150, 90), 32, 29, 9, 5)
            for x in (22, 27):
                p.circle((90, 170, 80), x, 22, 3.5)
            p.sparkle(40, 10, 3.5)
        else:   # Grilled Fish
            _plate(p)
            p.op((210, 130, 70), [(10, 30), (16, 24), (34, 23), (40, 28), (34, 34), (16, 34)], 1.2)
            p.op((210, 130, 70), [(10, 30), (4, 24), (4, 36)], 1)
            for x in (18, 24, 30):
                p.line((120, 60, 30), x, 25, x + 3, 33, 1.4)
    elif cat == "animal":
        if name == "Raw Meat":
            p.oe((250, 240, 230), 24, 26, 18, 13)
            p.ell((205, 60, 70), 23, 25, 15, 10)
            p.ell((235, 110, 120), 19, 21, 6, 3)
            p.oc((250, 246, 236), 32, 28, 3.5, 1)
        elif name in ("Hide", "Bear Pelt"):
            c = (160, 118, 78) if name == "Hide" else (100, 66, 44)
            p.op(c, [(8, 12), (16, 16), (32, 16), (40, 12), (38, 26), (42, 40), (30, 36), (18, 36), (6, 40), (10, 26)], 1.3)
            p.ell(sh(c, 30), 24, 24, 9, 7)
            if name == "Bear Pelt":
                p.oc(c, 24, 10, 7)
                p.circle((30, 24, 30), 21, 9, 1.3)
                p.circle((30, 24, 30), 27, 9, 1.3)
        elif name == "Rabbit Foot":
            p.ol((200, 170, 60), [(24, 6), (24, 14)], 1.4)
            p.oe((245, 240, 235), 24, 28, 9, 14)
            for x in (19, 24, 29):
                p.circle((240, 180, 190), x, 38, 2)
        elif name in ("Antler", "Golden Antler"):
            c = (232, 214, 170) if name == "Antler" else (255, 210, 60)
            p.ol(c, [(10, 42), (18, 28), (22, 14), (20, 4)], 3.5)
            p.ol(c, [(18, 28), (32, 22), (40, 10)], 3)
            p.ol(c, [(21, 18), (12, 10)], 2.5)
            if name == "Golden Antler":
                p.sparkle(38, 34, 4.5)
        elif name in ("Tusk", "Wolf Fang"):
            p.op((250, 246, 230), [(12, 40), (20, 10), (36, 6), (24, 18), (20, 40)], 1.3)
            p.path((210, 200, 180), [(17, 36), (21, 18), (30, 10)], 1.2)
            if name == "Wolf Fang":
                p.ol((140, 100, 60), [(8, 42), (40, 42)], 1.4, 0.8)
        else:
            p.ball(col, 24, 24, 14)
    elif cat == "misc":
        if name == "Bandage":
            p.orr((240, 220, 190), 8, 18, 32, 12, 4)
            p.orr((240, 220, 190), 18, 8, 12, 32, 4)
            p.rect((230, 70, 70), 21, 16, 6, 16)
            p.rect((230, 70, 70), 16, 21, 16, 6)
        elif name == "Water Bottle":
            p.orr((120, 190, 255), 14, 14, 20, 30, 7)
            p.rect((180, 225, 255), 17, 18, 5, 22, 2)
            p.orr((60, 110, 200), 18, 6, 12, 9, 2)
        else:
            p.op((230, 80, 70), [(6, 20), (42, 14), (44, 30), (8, 36)], 1.3)
            p.poly((255, 210, 90), [(16, 19), (32, 16), (33, 30), (17, 33)])
    else:   # dig / dive treasures
        if name == "Dirt":
            p.oe((122, 86, 56), 24, 32, 18, 10)
            p.oe((140, 100, 66), 24, 25, 12, 9, 1)
            for x, y in ((18, 28), (28, 24), (24, 34), (31, 32)):
                p.circle((90, 62, 40), x, y, 1.5)
        elif name in ("Pebble", "Pearl"):
            if name == "Pearl":
                p.op((240, 200, 210), [(4, 36), (24, 44), (44, 36), (24, 30)], 1.2)
            p.ball(col, 24, 26 if name == "Pebble" else 28, 12 if name == "Pebble" else 9)
        elif name == "Worm":
            p.ol(col, [(8, 34), (16, 24), (24, 32), (32, 22), (40, 28)], 6, 1.3)
            p.circle((30, 24, 30), 39, 26, 1.2)
        elif name == "Old Bottle":
            p.orr(col, 16, 18, 16, 26, 5)
            p.orr(col, 20, 8, 8, 12, 2)
            p.orr((170, 120, 70), 20, 4, 8, 5, 1, 1)
            p.rect(sh(col, 50), 19, 22, 3, 18, 1)
        elif name == "Bone":
            p.orr((240, 234, 214), 12, 21, 24, 7, 3)
            for x in (10, 38):
                for y in (20, 29):
                    p.oc((240, 234, 214), x, y, 4.5)
        elif name in ("Copper Coin", "Pirate Coin"):
            p.oc(sh(col, -30), 24, 24, 16)
            p.circle(col, 23, 23, 14)
            p.circle(sh(col, -20), 24, 24, 10)
            p.circle(col, 24, 24, 8.5)
            if name == "Pirate Coin":
                p.circle((60, 40, 30), 24, 22, 4)
                p.rect((60, 40, 30), 21, 25, 6, 3)
            p.sparkle(14, 12, 3)
        elif name in ("Arrowhead", "Trident"):
            if name == "Trident":
                p.ol(col, [(24, 46), (24, 14)], 3)
                for x in (12, 24, 36):
                    p.ol(col, [(x, 20), (x, 4)], 2.5)
                p.ol(col, [(12, 20), (36, 20)], 3)
                p.sparkle(40, 36, 4)
            else:
                p.op(col, [(24, 4), (36, 34), (24, 28), (12, 34)], 1.3)
                p.poly(sh(col, 40), [(24, 4), (24, 28), (12, 34)])
                p.ol((140, 100, 60), [(24, 30), (24, 46)], 3)
        elif name == "Silver Ring":
            p.circle(OUT, 24, 28, 15)
            p.circle(col, 24, 28, 13.5)
            p.circle(OUT, 24, 28, 9.5)
            p.circle((0, 0, 0, 0), 24, 28, 8.2)
            p.op((90, 200, 255), [(24, 6), (30, 12), (24, 18), (18, 12)], 1)
        elif name == "Fossil":
            p.ball((200, 180, 140), 24, 24, 17)
            for r in (12, 8, 4.5):
                p.circle(OUT, 25, 25, r + 0.7)
                p.circle((210, 190, 150), 25, 25, r - 0.7)
        elif name in ("Gold Idol",):
            p.op(col, [(14, 44), (18, 22), (30, 22), (34, 44)], 1.3)
            p.ball(col, 24, 14, 8)
            p.circle((140, 90, 20), 21, 14, 1.3)
            p.circle((140, 90, 20), 27, 14, 1.3)
            p.sparkle(40, 10, 4)
        elif name == "Dino Skull":
            p.op(col, [(6, 22), (16, 8), (36, 10), (44, 22), (40, 36), (14, 36)], 1.3)
            p.oc((60, 50, 40), 18, 20, 5)
            for x in range(16, 40, 5):
                p.op((250, 250, 245), [(x, 33), (x + 2.5, 40), (x + 5, 33)], 0.7)
        elif name == "Ancient Crown":
            p.op(col, [(6, 40), (8, 14), (16, 26), (24, 8), (32, 26), (40, 14), (42, 40)], 1.3)
            p.poly(sh(col, 40), [(8, 36), (8, 18), (14, 28)])
            for x, c in ((15, (255, 60, 80)), (24, (80, 200, 255)), (33, (80, 230, 120))):
                p.oc(c, x, 33, 3, 0.9)
            p.sparkle(40, 6, 4)
        elif name == "Alien Egg":
            p.oe(col, 24, 26, 13, 17)
            for x, y in ((19, 18), (29, 24), (21, 32), (30, 34)):
                p.circle(sh(col, -60), x, y, 2.8)
            p.circle(sh(col, 60), 18, 16, 3)
            p.sparkle(41, 9, 4, (200, 255, 200))
        elif name == "Seashell":
            p.op(col, [(24, 42), (4, 18), (14, 8), (24, 6), (34, 8), (44, 18)], 1.3)
            for x in (10, 17, 24, 31, 38):
                p.line(sh(col, -40), 24, 40, x, 12, 1.1)
        elif name == "Sand Dollar":
            p.oc(col, 24, 24, 16)
            for k in range(5):
                a = -math.pi / 2 + k * math.tau / 5
                p.ell(sh(col, -35), 24 + math.cos(a) * 7, 24 + math.sin(a) * 7, 2, 2)
        elif name == "Coral":
            p.ol(col, [(24, 44), (24, 24), (16, 12)], 4.5)
            p.ol(col, [(24, 30), (34, 18), (36, 8)], 4)
            p.ol(col, [(20, 20), (10, 18)], 3.5)
        elif name == "Sunken Chest":
            p.orr((150, 100, 50), 6, 20, 36, 22, 3)
            p.op((170, 116, 60), [(6, 20), (10, 8), (38, 8), (42, 20)], 1.3)
            p.rect((255, 210, 70), 4, 18, 40, 4, 1)
            p.orr((255, 210, 70), 20, 22, 8, 9, 2, 1)
            p.sparkle(40, 6, 4)
        elif name == "Mermaid Scale":
            p.op(col, [(24, 4), (42, 18), (36, 40), (24, 44), (12, 40), (6, 18)], 1.3)
            p.poly(sh(col, 50), [(24, 6), (24, 42), (12, 38), (8, 18)])
            p.sparkle(38, 10, 4)
        else:
            p.ball(col, 24, 24, 14)
    return p.done(), 24, 24


# ====================================================================== map
def render_map(T, MW, MH, TS):
    """Render the whole valley once, with 2.5D cliffs, banks, raised garden beds and a railed bridge."""
    R = random.Random(9091)
    surf = pygame.Surface((MW * TS, MH * TS))

    def t(x, y):
        return T[y][x] if 0 <= x < MW and 0 <= y < MH else MOUNT

    def land(v):
        return v not in WATER and v != BRIDGE

    for y in range(MH):
        for x in range(MW):
            v = T[y][x]
            X, Y = x * TS, y * TS
            c = sh(TILE_COL[v], R.randint(-6, 6))
            surf.fill(c, (X, Y, TS, TS))
            north, south, west, east = t(x, y - 1), t(x, y + 1), t(x - 1, y), t(x + 1, y)
            if v == GRASS:
                for _ in range(3):
                    gx, gy = X + R.randint(3, 28), Y + R.randint(8, 29)
                    pygame.draw.line(surf, sh(c, -34), (gx, gy), (gx - 2, gy - 5), 2)
                    pygame.draw.line(surf, sh(c, -34), (gx, gy), (gx + 2, gy - 6), 2)
                    pygame.draw.line(surf, sh(c, 22), (gx + 2, gy - 6), (gx + 2, gy - 7), 1)
                r = R.random()
                if r < 0.05:
                    fc = R.choice([(255, 240, 120), (255, 150, 200), (200, 200, 255), (255, 255, 255), (255, 170, 90)])
                    fx_, fy_ = X + R.randint(8, 24), Y + R.randint(8, 24)
                    for a in range(5):
                        pygame.draw.circle(surf, fc, (fx_ + round(math.cos(a * 1.26) * 3), fy_ + round(math.sin(a * 1.26) * 3)), 2)
                    pygame.draw.circle(surf, (255, 220, 80), (fx_, fy_), 1)
                elif r < 0.08:
                    rx_, ry_ = X + R.randint(6, 24), Y + R.randint(10, 24)
                    pygame.draw.ellipse(surf, sh(c, -45), (rx_ + 1, ry_ + 2, 8, 5))
                    pygame.draw.ellipse(surf, (150, 148, 140), (rx_, ry_, 8, 5))
            elif v == SAND:
                for _ in range(5):
                    surf.fill(sh(c, R.choice((-22, 18))), (X + R.randint(2, 29), Y + R.randint(2, 29), 2, 2))
            elif v in WATER:
                for _ in range(2):
                    if R.random() < 0.5:
                        lx, ly = X + R.randint(2, 18), Y + R.randint(8, 26)
                        pygame.draw.line(surf, sh(c, 30), (lx, ly), (lx + 9, ly), 2)
                if v == SHALLOW and any(t(x + i, y + j) == DEEP for i in (-1, 0, 1) for j in (-1, 0, 1)):
                    surf.fill(mix(c, TILE_COL[DEEP], 0.25), (X, Y + 20, TS, 12))
                if land(north):
                    surf.fill(sh(c, -55), (X, Y, TS, 7))
                    surf.fill(sh(c, -30), (X, Y + 7, TS, 3))
                    for k in range(0, TS, 6):
                        pygame.draw.circle(surf, (210, 236, 250), (X + k + 3, Y + 11), 2)
                elif north == BRIDGE:
                    surf.fill(sh(c, -60), (X, Y, TS, 9))
                if land(west):
                    surf.fill(sh(c, -40), (X, Y, 4, TS))
                if land(east):
                    surf.fill(sh(c, -25), (X + TS - 3, Y, 3, TS))
            elif v in (MOUNT, WALL):
                top = sh(c, 14)
                surf.fill(top, (X, Y, TS, TS))
                for _ in range(3):
                    bx_, by_ = X + R.randint(2, 22), Y + R.randint(2, 18)
                    pygame.draw.ellipse(surf, sh(top, -16), (bx_, by_ + 2, 10, 7))
                    pygame.draw.ellipse(surf, sh(top, 14), (bx_, by_, 10, 6))
                if south != v:
                    face = sh(c, -38)
                    surf.fill(face, (X, Y + 14, TS, 18))
                    pygame.draw.line(surf, sh(top, 28), (X, Y + 14), (X + TS, Y + 14), 2)
                    for k in range(3):
                        sx_ = X + 4 + k * 10 + R.randint(-2, 2)
                        pygame.draw.line(surf, sh(face, -22), (sx_, Y + 17), (sx_ + R.randint(-2, 2), Y + 30), 2)
                        pygame.draw.line(surf, sh(face, 15), (sx_ + 2, Y + 17), (sx_ + 2, Y + 22), 1)
                if west != v:
                    surf.fill(sh(top, 18), (X, Y, 3, TS))
                if east != v:
                    surf.fill(sh(top, -26), (X + TS - 4, Y, 4, TS))
            elif v == CAVE:
                for _ in range(4):
                    surf.fill(sh(c, R.choice((-20, 12))), (X + R.randint(2, 28), Y + R.randint(2, 28), 3, 3))
                if R.random() < 0.15:
                    pygame.draw.line(surf, sh(c, -25), (X + 6, Y + 10), (X + 18, Y + 16), 1)
            elif v == PATH:
                for _ in range(4):
                    px_, py_ = X + R.randint(4, 27), Y + R.randint(4, 27)
                    pygame.draw.circle(surf, sh(c, -25), (px_, py_ + 1), 2)
                    pygame.draw.circle(surf, sh(c, 18), (px_, py_), 2)
                for nb, rect in ((north, (X, Y, TS, 3)), (south, (X, Y + TS - 3, TS, 3)), (west, (X, Y, 3, TS)), (east, (X + TS - 3, Y, 3, TS))):
                    if nb in (GRASS, SAND):
                        surf.fill(sh(c, -22), rect)
            elif v == BRIDGE:
                for k in range(0, TS, 8):
                    pygame.draw.rect(surf, sh(c, R.randint(-10, 10)), (X + k, Y, 7, TS))
                    pygame.draw.line(surf, sh(c, -45), (X + k + 7, Y), (X + k + 7, Y + TS), 1)
                    pygame.draw.circle(surf, sh(c, -50), (X + k + 3, Y + 4), 1)
                    pygame.draw.circle(surf, sh(c, -50), (X + k + 3, Y + TS - 5), 1)
                if north != BRIDGE:
                    surf.fill((100, 66, 40), (X, Y, TS, 5))
                    surf.fill((150, 104, 62), (X, Y, TS, 2))
                    surf.fill((80, 52, 32), (X + 2, Y, 4, 9))
                if south != BRIDGE:
                    surf.fill((100, 66, 40), (X, Y + TS - 6, TS, 6))
                    surf.fill((150, 104, 62), (X, Y + TS - 6, TS, 2))
                    surf.fill((80, 52, 32), (X + 2, Y + TS - 10, 4, 10))
            elif v == PLOTT:
                for k in range(3, TS, 7):
                    pygame.draw.line(surf, sh(c, -28), (X, Y + k), (X + TS, Y + k), 3)
                    pygame.draw.line(surf, sh(c, 16), (X, Y + k - 2), (X + TS, Y + k - 2), 1)
                if south != PLOTT:
                    surf.fill(sh(c, -45), (X, Y + TS - 7, TS, 7))
                    surf.fill((150, 104, 62), (X, Y + TS - 9, TS, 3))
                if north != PLOTT:
                    surf.fill((170, 120, 74), (X, Y, TS, 3))
                if west != PLOTT:
                    surf.fill((150, 104, 62), (X, Y, 3, TS))
                if east != PLOTT:
                    surf.fill((120, 82, 50), (X + TS - 3, Y, 3, TS))
            # shadows cast onto this tile by taller neighbours
            if v not in (MOUNT, WALL) and north in (MOUNT, WALL):
                surf.fill(sh(surf.get_at((X + 16, Y + 10))[:3], -40), (X, Y, TS, 6))
            if land(v) and v not in (MOUNT, WALL) and south in WATER:
                surf.fill(sh(surf.get_at((X + 16, Y + 16))[:3], -28), (X, Y + TS - 4, TS, 4))
    return surf


# ====================================================================== everything
PERSON_DIRS = ("down", "up", "left", "right")


def build_all(trees, ores, buildings, buyers, items, pets, rarities):
    """Return {sprite name: (surface, anchor_x, anchor_y)}."""
    out = {}
    for name, col in trees:
        out["tree_" + name] = tree(name, col)
        out["stump_" + name] = stump(name)
    for name, tier, col in ores:
        out["ore_" + name] = ore(name, tier, col)
    out["rubble"] = rubble()
    for name, col, w, h in buildings:
        out["bld_" + name] = building(name, col, w, h)
    pals = {"player": ((255, 214, 172), (60, 120, 220), (52, 62, 96), (96, 62, 40), (40, 160, 90)),
            "hurt": ((255, 176, 160), (226, 72, 72), (52, 62, 96), (96, 62, 40), (40, 160, 90))}
    hairs = [(60, 40, 30), (230, 190, 100), (150, 70, 40), (40, 36, 40), (200, 200, 205), (120, 80, 50), (90, 50, 30)]
    hats = [(170, 50, 50), None, (90, 90, 100), (240, 240, 240), None, (110, 80, 50), (120, 170, 80)]
    for i, (bname, cat, col) in enumerate(buyers):
        pals[f"npc{i}"] = ((250, 208, 170) if i % 2 else (210, 160, 120), col, (70, 64, 80), hairs[i % len(hairs)], hats[i % len(hats)])
    for i, col in enumerate([(220, 120, 120), (120, 160, 230), (140, 210, 140), (230, 200, 110)]):
        pals[f"diner{i}"] = ((250, 210, 175) if i % 2 == 0 else (190, 140, 100), col, (60, 60, 80), hairs[(i + 2) % len(hairs)], None)
    for key, pal in pals.items():
        for d in PERSON_DIRS:
            for f in range(3):
                out[f"p_{key}_{d}_{f}"] = person(pal, d, f)
        if key in ("player", "hurt"):
            for d in PERSON_DIRS:
                out[f"p_{key}_{d}_swim"] = person(pal, d, 0, swim=True)
    for kind in ANIMAL_LOOK:
        for f in range(3):
            s, ax, ay = animal(kind, f)
            out[f"a_{kind}_r_{f}"] = (s, ax, ay)
            out[f"a_{kind}_l_{f}"] = (pygame.transform.flip(s, True, False), s.get_width() - ax, ay)
    for name, rar, col in pets:
        out["pet_" + name] = pet(name, col, rarities.index(rar))
    for name, (cat, col) in items.items():
        out["icon_" + name] = icon(name, cat, col)
    return out
