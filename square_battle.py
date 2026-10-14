"""Square Battle 2D — generator video pertandingan kotak secara otomatis."""
import math
import random

from engine import (BG, FPS, GRAY, PARTICIPANTS, WHITE, WINNER_SECONDS, Canvas, VideoWriter,
                    run_cli)
import pygame

ARENA = pygame.Rect(90, 460, 900, 900)
MAX_SECONDS = 90
SIZE = 70
HIT_IFRAMES = 6            # frame kebal setelah terkena, agar satu tabrakan = satu damage
MODES = ("klasik", "menyusut")
SHRINK_START, SHRINK_END, MIN_ARENA = 10, 60, 360   # detik, detik, piksel

CONCEPT = {
    "id": "square_battle",
    "nama": "Square Battle",
    "deskripsi": "6 kotak saling bertabrakan dan kehilangan HP; kotak terakhir yang bertahan menang.",
    "mode": MODES,
    "durasi_maks": MAX_SECONDS,
}


class Square:
    def __init__(self, name, color, rng):
        self.name, self.color, self.size = name, color, SIZE
        self.x = rng.uniform(ARENA.left, ARENA.right - self.size)
        self.y = rng.uniform(ARENA.top, ARENA.bottom - self.size)
        ang, spd = rng.uniform(0, 2 * math.pi), rng.uniform(6, 9)
        self.vx, self.vy = spd * math.cos(ang), spd * math.sin(ang)
        self.hp, self.flash, self.out_frame = 100, 0, None

    @property
    def alive(self):
        return self.hp > 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def move(self, arena):
        self.x += self.vx
        self.y += self.vy
        if self.x < arena.left: self.x, self.vx = arena.left, abs(self.vx)
        if self.x + self.size > arena.right: self.x, self.vx = arena.right - self.size, -abs(self.vx)
        if self.y < arena.top: self.y, self.vy = arena.top, abs(self.vy)
        if self.y + self.size > arena.bottom: self.y, self.vy = arena.bottom - self.size, -abs(self.vy)
        if self.flash: self.flash -= 1


def arena_at(frame, mode):
    if mode != "menyusut":
        return ARENA
    k = (frame / FPS - SHRINK_START) / (SHRINK_END - SHRINK_START)
    k = min(max(k, 0.0), 1.0)
    side = round(ARENA.width - (ARENA.width - MIN_ARENA) * k)
    r = pygame.Rect(0, 0, side, side)
    r.center = ARENA.center
    return r


def collide(a, b, rng):
    """Pisahkan dua kotak yang bertumpuk, pantulkan, dan kurangi HP. True jika ada damage."""
    ra, rb = a.rect, b.rect
    if not ra.colliderect(rb):
        return False
    dx, dy = ra.centerx - rb.centerx, ra.centery - rb.centery
    ox, oy = a.size - abs(dx), a.size - abs(dy)
    if ox < oy:   # tabrakan dari samping
        p = ox / 2 * (1 if dx >= 0 else -1)
        a.x += p; b.x -= p
        if (a.vx - b.vx) * dx < 0:   # tukar kecepatan hanya jika saling mendekat
            a.vx, b.vx = b.vx, a.vx
    else:         # tabrakan dari atas/bawah
        p = oy / 2 * (1 if dy >= 0 else -1)
        a.y += p; b.y -= p
        if (a.vy - b.vy) * dy < 0:
            a.vy, b.vy = b.vy, a.vy
    hit = False
    for s in (a, b):
        if s.flash == 0:
            s.hp -= rng.randint(5, 15)
            s.flash = HIT_IFRAMES
            hit = True
    return hit


def hp_color(hp):
    r = max(hp, 0) / 100
    return (int(230 * (1 - r) + 80 * r), int(60 * (1 - r) + 220 * r), 90)


class Renderer(Canvas):
    def draw(self, squares, arena, seconds, max_seconds, mode, winner, reason):
        s = self.screen
        self.header("SQUARE BATTLE", mode, seconds, max_seconds)

        if arena != ARENA:
            pygame.draw.rect(s, (55, 30, 40), ARENA)
            pygame.draw.rect(s, BG, arena)
            pygame.draw.rect(s, (235, 80, 80), arena, 6)
        else:
            pygame.draw.rect(s, WHITE, ARENA, 6)

        for sq in squares:
            if not sq.alive:
                continue
            r = sq.rect
            pygame.draw.rect(s, WHITE if sq.flash else sq.color, r)
            bar = pygame.Rect(r.x, r.y - 16, sq.size, 8)
            pygame.draw.rect(s, (60, 60, 60), bar)
            pygame.draw.rect(s, hp_color(sq.hp), (bar.x, bar.y, int(sq.size * sq.hp / 100), 8))

        # Papan skor: 2 kolom x 3 baris
        for i, sq in enumerate(squares):
            x, y = 130 + (i % 2) * 450, 1430 + (i // 2) * 90
            color = sq.color if sq.alive else GRAY
            pygame.draw.rect(s, color, (x, y, 50, 50))
            name = self.font_small.render(sq.name, True, WHITE if sq.alive else GRAY)
            s.blit(name, (x + 70, y + 6))
            hp = f"{max(sq.hp, 0)} HP" if sq.alive else "KO"
            hp_img = self.font_small.render(hp, True, hp_color(sq.hp) if sq.alive else GRAY)
            s.blit(hp_img, (x + 360 - hp_img.get_width(), y + 6))

        if winner:
            self.banner(f"{winner.name.upper()} MENANG!", winner.color, reason, ARENA.center)


def pick_winner(squares, frame):
    alive = [s for s in squares if s.alive]
    if alive:
        return max(alive, key=lambda s: s.hp)
    # Semua tumbang bersamaan: menang yang tumbang terakhir dengan sisa HP tertinggi
    last = [s for s in squares if s.out_frame == frame]
    return max(last, key=lambda s: s.hp)


def render(output="battle.mp4", seed=None, mode="klasik", with_audio=True,
           max_seconds=MAX_SECONDS, progress=None):
    """Simulasikan satu pertandingan, render ke MP4, dan kembalikan metadata hasilnya."""
    if mode not in MODES:
        raise ValueError(f"Mode tidak dikenal: {mode} (pilihan: {', '.join(MODES)})")
    if seed is None:
        seed = random.randrange(2 ** 31)
    rng = random.Random(seed)
    squares = [Square(n, c, rng) for n, c in PARTICIPANTS]
    renderer = Renderer()
    with VideoWriter(output, with_audio, progress) as video:
        video.write_intro(renderer, CONCEPT["nama"])
        frame, events, winner, reason, end_frame, eliminations = _simulate(
            squares, renderer, video, rng, mode, max_seconds)
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
        "statistik": {"hp_pemenang": max(winner.hp, 0),
                      "jumlah_tabrakan": sum(1 for k, _ in events if k == "hit")},
    }


def _simulate(squares, renderer, video, rng, mode, max_seconds):
    frame, winner, end_frame, reason = 0, None, None, ""
    arena = ARENA
    events, eliminations = [], []
    while True:
        if winner is None:
            arena = arena_at(frame, mode)
            alive = [s for s in squares if s.alive]
            for s in alive:
                s.move(arena)
            for i in range(len(alive)):
                for j in range(i + 1, len(alive)):
                    if collide(alive[i], alive[j], rng):
                        events.append(("hit", frame))
            for s in alive:
                if not s.alive:
                    s.out_frame = frame
                    events.append(("elim", frame))
                    eliminations.append({"nama": s.name, "detik": round(frame / FPS, 2)})
            remaining = [s for s in squares if s.alive]
            if len(remaining) <= 1 or frame >= max_seconds * FPS:
                winner, end_frame = pick_winner(squares, frame), frame
                reason = "Bertahan sampai akhir!" if len(remaining) <= 1 else "Waktu habis - HP tertinggi"
                events.append(("win", frame))
        elif frame - end_frame >= WINNER_SECONDS * FPS:
            break
        seconds = (frame if end_frame is None else end_frame) // FPS
        renderer.draw(squares, arena, seconds, max_seconds, mode, winner, reason)
        video.write(renderer)
        frame += 1
    return frame, events, winner, reason, end_frame, eliminations


if __name__ == "__main__":
    run_cli(CONCEPT, render)
