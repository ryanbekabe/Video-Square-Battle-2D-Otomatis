"""Sumo — bola saling dorong di ring bundar; yang terdorong keluar ring tereliminasi."""
import math
import random

from engine import (FPS, GRAY, PARTICIPANTS, WHITE, WINNER_SECONDS, Canvas, VideoWriter,
                    run_cli)
import pygame

CENTER = (540, 910)
RING = 430
MAX_SECONDS = 60
MODES = ("klasik", "menyusut")
SHRINK_START, SHRINK_END, MIN_RING = 10, 45, 190   # detik, detik, piksel
FALL_FRAMES = 40
MAX_SPEED = 11
FRICTION = 0.985
RESTITUTION = 1.15     # > 1: tabrakan menambah energi agar dorongan terasa kuat
POWER_START, POWER_GROWTH = 0.20, 0.006   # agresi bertambah tiap detik -> ada klimaks
EDGE_PULL = 0.35                          # naluri bertahan, melemah seiring waktu
FINAL_BOOST = 1.8                         # duel terakhir lebih agresif agar tidak buntu
SUDDEN_DEATH = 8                          # detik duel final sebelum ring ikut menyusut
SUDDEN_SHRINK = 0.35                      # piksel per frame

CONCEPT = {
    "id": "sumo",
    "nama": "Sumo Bola",
    "deskripsi": "6 bola dengan berat berbeda saling dorong di ring bundar; yang keluar ring kalah.",
    "mode": MODES,
    "durasi_maks": MAX_SECONDS,
}


class Wrestler:
    def __init__(self, name, color, angle, rng):
        self.name, self.color = name, color
        self.mass = rng.uniform(0.8, 1.3)
        self.r = 34 * math.sqrt(self.mass)
        self.x = CENTER[0] + RING * 0.6 * math.cos(angle)
        self.y = CENTER[1] + RING * 0.6 * math.sin(angle)
        self.vx = self.vy = 0.0
        self.target, self.retarget_at = None, 0
        self.flash, self.falling, self.out_frame, self.pushes = 0, 0, None, 0

    @property
    def in_ring(self):
        return self.out_frame is None

    def think(self, others, frame, ring, rng):
        if self.target is None or not self.target.in_ring or frame >= self.retarget_at:
            # Lebih suka menyerang lawan yang dekat
            weights = [1 / (1 + math.hypot(o.x - self.x, o.y - self.y)) for o in others]
            self.target = rng.choices(others, weights)[0]
            self.retarget_at = frame + rng.randint(60, 180)
        dx, dy = self.target.x - self.x, self.target.y - self.y
        d = math.hypot(dx, dy) or 1
        t = frame / FPS
        final = len(others) == 1
        power = (POWER_START + POWER_GROWTH * t) / math.sqrt(self.mass)
        if final:
            power *= FINAL_BOOST
        ax, ay = dx / d * power, dy / d * power
        # Naluri bertahan: menjauh dari tepi ring
        cx, cy = CENTER[0] - self.x, CENTER[1] - self.y
        dc = math.hypot(cx, cy) or 1
        edge = dc / ring
        if edge > 0.72:
            pull = EDGE_PULL * max(0.2, 1 - t / 50) * (edge - 0.72) / 0.28
            if final:
                pull *= 0.5
            ax += cx / dc * pull
            ay += cy / dc * pull
        ax += rng.uniform(-0.08, 0.08)
        ay += rng.uniform(-0.08, 0.08)
        self.vx += ax
        self.vy += ay

    def move(self):
        self.vx *= FRICTION
        self.vy *= FRICTION
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            self.vx, self.vy = self.vx / speed * MAX_SPEED, self.vy / speed * MAX_SPEED
        self.x += self.vx
        self.y += self.vy
        if self.flash: self.flash -= 1


def ring_at(frame, mode):
    if mode != "menyusut":
        return RING
    k = (frame / FPS - SHRINK_START) / (SHRINK_END - SHRINK_START)
    k = min(max(k, 0.0), 1.0)
    return RING - (RING - MIN_RING) * k


def collide(a, b):
    """Tabrakan dua bola bermassa. True jika benturannya cukup keras untuk diberi suara."""
    dx, dy = b.x - a.x, b.y - a.y
    dist = math.hypot(dx, dy)
    if dist >= a.r + b.r:
        return False
    nx, ny = (dx / dist, dy / dist) if dist else (1.0, 0.0)
    overlap = a.r + b.r - dist
    total = a.mass + b.mass
    a.x -= nx * overlap * b.mass / total; a.y -= ny * overlap * b.mass / total
    b.x += nx * overlap * a.mass / total; b.y += ny * overlap * a.mass / total
    rv = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
    if rv >= 0:
        return False
    a_attack = a.vx * nx + a.vy * ny          # kecepatan a menuju b
    b_attack = -(b.vx * nx + b.vy * ny)       # kecepatan b menuju a
    j = -(1 + RESTITUTION) * rv / (1 / a.mass + 1 / b.mass)
    a.vx -= j * nx / a.mass; a.vy -= j * ny / a.mass
    b.vx += j * nx / b.mass; b.vy += j * ny / b.mass
    if -rv > 2:
        a.flash = b.flash = 6
        (a if a_attack >= b_attack else b).pushes += 1
        return True
    return False


class Renderer(Canvas):
    def draw_wrestler(self, w):
        scale = 1 - w.falling / FALL_FRAMES if w.falling else 1
        if scale <= 0:
            return
        r = max(1, int(w.r * scale))
        pos = (int(w.x), int(w.y))
        pygame.draw.circle(self.screen, w.color, pos, r)
        pygame.draw.circle(self.screen, WHITE if w.flash else (20, 20, 30), pos, r, 4)
        # Mata menghadap arah gerak
        speed = math.hypot(w.vx, w.vy) or 1
        fx, fy = w.vx / speed, w.vy / speed
        for side in (-1, 1):
            ex = w.x + (fx * 0.35 - fy * 0.35 * side) * r
            ey = w.y + (fy * 0.35 + fx * 0.35 * side) * r
            pygame.draw.circle(self.screen, WHITE, (int(ex), int(ey)), max(1, int(r * 0.24)))
            pygame.draw.circle(self.screen, (15, 15, 20),
                               (int(ex + fx * r * 0.09), int(ey + fy * r * 0.09)),
                               max(1, int(r * 0.12)))

    def draw(self, wrestlers, ring, sudden, seconds, max_seconds, mode, winner, reason):
        s = self.screen
        self.header("SUMO BOLA", mode, seconds, max_seconds)
        pygame.draw.circle(s, (40, 26, 34), CENTER, RING)
        pygame.draw.circle(s, (52, 48, 70), CENTER, int(ring))
        pygame.draw.circle(s, (235, 80, 80) if ring < RING else WHITE, CENTER, int(ring), 6)
        pygame.draw.circle(s, (80, 76, 100), CENTER, int(ring * 0.35), 3)
        if sudden and not winner:
            self.text(self.font_small, "SUDDEN DEATH!", (235, 80, 80), (CENTER[0], 1385))
        # Yang jatuh digambar di bawah yang masih bertanding
        for w in sorted(wrestlers, key=lambda w: w.in_ring):
            self.draw_wrestler(w)

        for i, w in enumerate(wrestlers):
            x, y = 130 + (i % 2) * 450, 1430 + (i // 2) * 90
            pygame.draw.circle(s, w.color if w.in_ring else GRAY, (x + 25, y + 25), 25)
            name = self.font_small.render(w.name, True, WHITE if w.in_ring else GRAY)
            s.blit(name, (x + 70, y + 6))
            status = ("BERTAHAN", (90, 220, 120)) if w.in_ring else \
                     (f"JATUH {w.out_frame // FPS}s", GRAY)
            st = self.font_small.render(status[0], True, status[1])
            s.blit(st, (x + 380 - st.get_width(), y + 6))

        if winner:
            self.banner(f"{winner.name.upper()} MENANG!", winner.color, reason, CENTER)


def render(output="sumo.mp4", seed=None, mode="klasik", with_audio=True,
           max_seconds=MAX_SECONDS, progress=None):
    if mode not in MODES:
        raise ValueError(f"Mode tidak dikenal: {mode} (pilihan: {', '.join(MODES)})")
    if seed is None:
        seed = random.randrange(2 ** 31)
    rng = random.Random(seed)
    offset = rng.uniform(0, 2 * math.pi)
    order = list(PARTICIPANTS)
    rng.shuffle(order)
    wrestlers = [Wrestler(n, c, offset + i * math.pi / 3, rng) for i, (n, c) in enumerate(order)]
    wrestlers.sort(key=lambda w: [n for n, _ in PARTICIPANTS].index(w.name))
    renderer = Renderer()

    def dist_center(w):
        return math.hypot(w.x - CENTER[0], w.y - CENTER[1])

    with VideoWriter(output, with_audio, progress) as video:
        video.write_intro(renderer, CONCEPT["nama"])
        frame, winner, end_frame, reason = 0, None, None, ""
        events, eliminations = [], []
        ring, duel_start, sudden_ring = RING, None, None
        while True:
            for w in wrestlers:
                if w.falling:
                    w.falling = min(w.falling + 1, FALL_FRAMES)
                    w.x += w.vx * 0.6
                    w.y += w.vy * 0.6
            if winner is None:
                ring = ring_at(frame, mode)
                if duel_start is not None and frame - duel_start >= SUDDEN_DEATH * FPS:
                    sudden_ring = ring if sudden_ring is None else max(0.0, sudden_ring - SUDDEN_SHRINK)
                    ring = min(ring, sudden_ring)
                fighters = [w for w in wrestlers if w.in_ring]
                for w in fighters:
                    w.think([o for o in fighters if o is not w], frame, ring, rng)
                    w.move()
                for i in range(len(fighters)):
                    for j in range(i + 1, len(fighters)):
                        if collide(fighters[i], fighters[j]):
                            events.append(("hit", frame))
                for w in fighters:
                    if dist_center(w) > ring:
                        w.out_frame, w.falling = frame, 1
                        events.append(("elim", frame))
                        eliminations.append({"nama": w.name, "detik": round(frame / FPS, 2)})
                fighters = [w for w in wrestlers if w.in_ring]
                if len(fighters) == 2 and duel_start is None:
                    duel_start = frame
                if len(fighters) <= 1 or frame >= max_seconds * FPS:
                    if fighters:
                        winner = min(fighters, key=dist_center)
                    else:   # jatuh bersamaan: yang paling dekat ke ring menang
                        winner = min((w for w in wrestlers if w.out_frame == frame), key=dist_center)
                    end_frame = frame
                    reason = ("Satu-satunya yang bertahan di ring!" if len(fighters) <= 1
                              else "Waktu habis - paling dekat ke tengah")
                    events.append(("win", frame))
            elif frame - end_frame >= WINNER_SECONDS * FPS:
                break
            seconds = (frame if end_frame is None else end_frame) // FPS
            renderer.draw(wrestlers, ring, sudden_ring is not None, seconds, max_seconds, mode, winner, reason)
            video.write(renderer)
            frame += 1
        video.finish(events, seed)

    return {
        "konsep": CONCEPT["id"],
        "output": output,
        "seed": seed,
        "mode": mode,
        "pemenang": winner.name,
        "alasan": reason,
        "durasi_pertandingan": round(end_frame / FPS, 2),
        "durasi_video": round(video.frames / FPS, 2),
        "eliminasi": eliminations,
        "statistik": {
            "massa": {w.name: round(w.mass, 2) for w in wrestlers},
            "dorongan": {w.name: w.pushes for w in wrestlers},
            "jumlah_benturan": sum(1 for k, _ in events if k == "hit"),
            "sudden_death": sudden_ring is not None,
        },
    }


if __name__ == "__main__":
    run_cli(CONCEPT, render)
