"""Perebutan Wilayah — kotak mengecat lantai arena; wilayah terluas saat waktu habis menang."""
import math
import random

from engine import (BG, FPS, PARTICIPANTS, WHITE, WINNER_SECONDS, Canvas, VideoWriter,
                    run_cli)
import pygame

ARENA = pygame.Rect(90, 460, 900, 900)
CELL = 30
GRID = ARENA.width // CELL
SIZE = 60
MAX_SECONDS = 45
MODES = ("klasik", "power-up")
POWERUP_EVERY = 4          # detik
SPLASH_CELLS = 4           # jari-jari cipratan power-up (dalam sel)
STAR_R = 26
FLOOR = (30, 30, 44)

CONCEPT = {
    "id": "wilayah",
    "nama": "Perebutan Wilayah",
    "deskripsi": "6 kotak mengecat lantai arena dengan warnanya; yang menguasai wilayah terluas "
                 "saat waktu habis menang.",
    "mode": MODES,
    "durasi_maks": MAX_SECONDS,
}


def blend(c, base, k):
    return tuple(int(a * k + b * (1 - k)) for a, b in zip(c, base))


class Painter:
    def __init__(self, idx, name, color, rng):
        self.idx, self.name, self.color = idx, name, color
        self.paint = blend(color, FLOOR, 0.6)
        self.x = rng.uniform(ARENA.left, ARENA.right - SIZE)
        self.y = rng.uniform(ARENA.top, ARENA.bottom - SIZE)
        ang, spd = rng.uniform(0, 2 * math.pi), rng.uniform(7, 9)
        self.vx, self.vy = spd * math.cos(ang), spd * math.sin(ang)
        self.flash, self.powerups = 0, 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), SIZE, SIZE)

    def turn(self, rng):
        """Belokan kecil acak saat memantul agar lintasan tidak berulang."""
        ang = rng.uniform(-0.35, 0.35)
        c, s = math.cos(ang), math.sin(ang)
        self.vx, self.vy = self.vx * c - self.vy * s, self.vx * s + self.vy * c

    def move(self, rng):
        self.x += self.vx
        self.y += self.vy
        bounced = False
        if self.x < ARENA.left: self.x, self.vx, bounced = ARENA.left, abs(self.vx), True
        if self.x + SIZE > ARENA.right: self.x, self.vx, bounced = ARENA.right - SIZE, -abs(self.vx), True
        if self.y < ARENA.top: self.y, self.vy, bounced = ARENA.top, abs(self.vy), True
        if self.y + SIZE > ARENA.bottom: self.y, self.vy, bounced = ARENA.bottom - SIZE, -abs(self.vy), True
        if bounced:
            self.turn(rng)
        if self.flash: self.flash -= 1


def collide(a, b):
    ra, rb = a.rect, b.rect
    if not ra.colliderect(rb):
        return False
    dx, dy = ra.centerx - rb.centerx, ra.centery - rb.centery
    ox, oy = SIZE - abs(dx), SIZE - abs(dy)
    if ox < oy:
        p = ox / 2 * (1 if dx >= 0 else -1)
        a.x += p; b.x -= p
        if (a.vx - b.vx) * dx < 0:
            a.vx, b.vx = b.vx, a.vx
            return True
    else:
        p = oy / 2 * (1 if dy >= 0 else -1)
        a.y += p; b.y -= p
        if (a.vy - b.vy) * dy < 0:
            a.vy, b.vy = b.vy, a.vy
            return True
    return False


class Floor:
    def __init__(self, n):
        self.owner = [-1] * (GRID * GRID)
        self.counts = [0] * n
        self.surface = pygame.Surface(ARENA.size)
        self.surface.fill(FLOOR)
        for i in range(1, GRID):
            pygame.draw.line(self.surface, (38, 38, 54), (i * CELL, 0), (i * CELL, ARENA.height))
            pygame.draw.line(self.surface, (38, 38, 54), (0, i * CELL), (ARENA.width, i * CELL))

    def set(self, gx, gy, p):
        if not (0 <= gx < GRID and 0 <= gy < GRID):
            return
        i = gy * GRID + gx
        if self.owner[i] == p.idx:
            return
        if self.owner[i] >= 0:
            self.counts[self.owner[i]] -= 1
        self.owner[i] = p.idx
        self.counts[p.idx] += 1
        self.surface.fill(p.paint, (gx * CELL, gy * CELL, CELL, CELL))

    def paint_under(self, p):
        r = p.rect.move(-ARENA.left, -ARENA.top)
        for gx in range(r.left // CELL, (r.right - 1) // CELL + 1):
            for gy in range(r.top // CELL, (r.bottom - 1) // CELL + 1):
                self.set(gx, gy, p)

    def splash(self, p):
        cx = int((p.x + SIZE / 2 - ARENA.left) // CELL)
        cy = int((p.y + SIZE / 2 - ARENA.top) // CELL)
        for gx in range(cx - SPLASH_CELLS, cx + SPLASH_CELLS + 1):
            for gy in range(cy - SPLASH_CELLS, cy + SPLASH_CELLS + 1):
                if (gx - cx) ** 2 + (gy - cy) ** 2 <= SPLASH_CELLS ** 2:
                    self.set(gx, gy, p)


def star_points(cx, cy, r, rot):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = rot + i * math.pi / 5
        pts.append((cx + rr * math.sin(a), cy - rr * math.cos(a)))
    return pts


class Renderer(Canvas):
    def draw(self, painters, floor, star, frame, seconds, max_seconds, mode, winner, reason):
        s = self.screen
        self.header("PEREBUTAN WILAYAH", mode, seconds, max_seconds)
        s.blit(floor.surface, ARENA)
        pygame.draw.rect(s, WHITE, ARENA, 6)
        if star:
            pulse = 1 + 0.15 * math.sin(frame / 6)
            pygame.draw.polygon(s, (255, 230, 90), star_points(*star, STAR_R * pulse, frame / 30))
            pygame.draw.polygon(s, WHITE, star_points(*star, STAR_R * pulse, frame / 30), 3)
        for p in painters:
            pygame.draw.rect(s, WHITE if p.flash else p.color, p.rect)
            pygame.draw.rect(s, BG, p.rect, 3)

        total = GRID * GRID
        ranking = sorted(painters, key=lambda p: -floor.counts[p.idx])
        for rank, p in enumerate(ranking):
            x, y = 130 + (rank % 2) * 450, 1430 + (rank // 2) * 90
            pygame.draw.rect(s, p.color, (x, y, 50, 50))
            name = self.font_small.render(f"{rank + 1}. {p.name}", True, WHITE)
            s.blit(name, (x + 70, y + 6))
            pct = self.font_small.render(f"{100 * floor.counts[p.idx] / total:.1f}%", True, p.color)
            s.blit(pct, (x + 380 - pct.get_width(), y + 6))

        if winner:
            self.banner(f"{winner.name.upper()} MENANG!", winner.color, reason, ARENA.center)


def render(output="wilayah.mp4", seed=None, mode="klasik", with_audio=True,
           max_seconds=MAX_SECONDS, progress=None):
    if mode not in MODES:
        raise ValueError(f"Mode tidak dikenal: {mode} (pilihan: {', '.join(MODES)})")
    if seed is None:
        seed = random.randrange(2 ** 31)
    rng = random.Random(seed)
    painters = [Painter(i, n, c, rng) for i, (n, c) in enumerate(PARTICIPANTS)]
    floor = Floor(len(painters))
    renderer = Renderer()

    with VideoWriter(output, with_audio, progress) as video:
        frame, winner, end_frame, reason = 0, None, None, ""
        events, star = [], None
        while True:
            if winner is None:
                for p in painters:
                    p.move(rng)
                for i in range(len(painters)):
                    for j in range(i + 1, len(painters)):
                        if collide(painters[i], painters[j]):
                            painters[i].flash = painters[j].flash = 5
                            events.append(("hit", frame))
                for p in painters:
                    floor.paint_under(p)
                if mode == "power-up":
                    if star is None and frame > 0 and frame % (POWERUP_EVERY * FPS) == 0:
                        star = (rng.uniform(ARENA.left + 60, ARENA.right - 60),
                                rng.uniform(ARENA.top + 60, ARENA.bottom - 60))
                    if star:
                        for p in painters:
                            if p.rect.inflate(STAR_R, STAR_R).collidepoint(star):
                                floor.splash(p)
                                p.powerups += 1
                                p.flash = 12
                                events.append(("pickup", frame))
                                star = None
                                break
                if frame >= max_seconds * FPS:
                    winner = max(painters, key=lambda p: floor.counts[p.idx])
                    end_frame = frame
                    pct = 100 * floor.counts[winner.idx] / (GRID * GRID)
                    reason = f"Wilayah terluas: {pct:.1f}%"
                    star = None
                    events.append(("win", frame))
            elif frame - end_frame >= WINNER_SECONDS * FPS:
                break
            seconds = (frame if end_frame is None else end_frame) // FPS
            renderer.draw(painters, floor, star, frame, seconds, max_seconds, mode, winner, reason)
            video.write(renderer)
            frame += 1
        video.finish(events, seed)

    total = GRID * GRID
    return {
        "konsep": CONCEPT["id"],
        "output": output,
        "seed": seed,
        "mode": mode,
        "pemenang": winner.name,
        "alasan": reason,
        "durasi_pertandingan": round(end_frame / FPS, 2),
        "durasi_video": round(frame / FPS, 2),
        "eliminasi": [],
        "statistik": {
            "wilayah_persen": {p.name: round(100 * floor.counts[p.idx] / total, 1) for p in painters},
            "power_up": {p.name: p.powerups for p in painters} if mode == "power-up" else None,
        },
    }


if __name__ == "__main__":
    run_cli(CONCEPT, render)
