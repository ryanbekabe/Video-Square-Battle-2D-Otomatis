"""Perang Suit — Batu, Gunting, Kertas saling mengonversi sampai tersisa satu jenis."""
import math
import random

from engine import FPS, GRAY, WHITE, WINNER_SECONDS, Canvas, VideoWriter, run_cli
import pygame

ARENA = pygame.Rect(90, 460, 900, 900)
MAX_SECONDS = 60
RADIUS = 26
SPEED = 3
FLASH = 10
IMMUNE = 45        # frame kebal setelah berubah jenis, agar konversi tidak berantai instan
MODES = ("seimbang", "underdog")

# Urutan penting: jenis i mengalahkan jenis (i - 1) % 3
KINDS = [("Batu", (150, 140, 128)), ("Kertas", (80, 160, 235)), ("Gunting", (235, 80, 90))]

CONCEPT = {
    "id": "perang_suit",
    "nama": "Perang Suit",
    "deskripsi": "Batu, Gunting, dan Kertas bergerak bebas; yang kalah saat bersentuhan berubah "
                 "menjadi jenis pemenang. Menang jika menguasai seluruh arena.",
    "mode": MODES,
    "durasi_maks": MAX_SECONDS,
}


def beats(a, b):
    return (a - b) % 3 == 1


class Token:
    def __init__(self, kind, rng):
        self.kind, self.flash, self.immune = kind, 0, 0
        self.x = rng.uniform(ARENA.left + RADIUS, ARENA.right - RADIUS)
        self.y = rng.uniform(ARENA.top + RADIUS, ARENA.bottom - RADIUS)
        ang = rng.uniform(0, 2 * math.pi)
        self.vx, self.vy = SPEED * math.cos(ang), SPEED * math.sin(ang)

    def move(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < ARENA.left + RADIUS: self.x, self.vx = ARENA.left + RADIUS, abs(self.vx)
        if self.x > ARENA.right - RADIUS: self.x, self.vx = ARENA.right - RADIUS, -abs(self.vx)
        if self.y < ARENA.top + RADIUS: self.y, self.vy = ARENA.top + RADIUS, abs(self.vy)
        if self.y > ARENA.bottom - RADIUS: self.y, self.vy = ARENA.bottom - RADIUS, -abs(self.vy)
        if self.flash: self.flash -= 1
        if self.immune: self.immune -= 1


def collide(a, b):
    """Tabrakan lingkaran (massa sama). True jika ada konversi jenis."""
    dx, dy = b.x - a.x, b.y - a.y
    if abs(dx) >= 2 * RADIUS or abs(dy) >= 2 * RADIUS:
        return False
    dist = math.hypot(dx, dy)
    if dist >= 2 * RADIUS:
        return False
    nx, ny = (dx / dist, dy / dist) if dist else (1.0, 0.0)
    push = (2 * RADIUS - dist) / 2
    a.x -= nx * push; a.y -= ny * push
    b.x += nx * push; b.y += ny * push
    rv = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
    if rv < 0:   # saling mendekat: tukar komponen kecepatan searah normal
        a.vx += rv * nx; a.vy += rv * ny
        b.vx -= rv * nx; b.vy -= rv * ny
    if a.kind == b.kind or a.immune or b.immune:
        return False
    loser = b if beats(a.kind, b.kind) else a
    loser.kind = a.kind if loser is b else b.kind
    loser.flash, loser.immune = FLASH, IMMUNE
    return True


def make_icon(kind, r):
    size = 2 * r
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = r
    pygame.draw.circle(surf, KINDS[kind][1], (c, c), r)
    k = r / RADIUS
    if kind == 0:     # batu
        pts = [(-11, -4), (-5, -12), (6, -11), (12, -3), (10, 8), (0, 12), (-10, 8)]
        pygame.draw.polygon(surf, (70, 64, 58), [(c + x * k, c + y * k) for x, y in pts])
        pygame.draw.polygon(surf, (210, 205, 195), [(c + x * k, c + y * k) for x, y in pts], 2)
    elif kind == 1:   # kertas
        rect = pygame.Rect(0, 0, 22 * k, 28 * k)
        rect.center = (c, c)
        pygame.draw.rect(surf, WHITE, rect)
        for i in range(3):
            y = rect.top + (8 + i * 6) * k
            pygame.draw.line(surf, (120, 140, 170), (rect.left + 4 * k, y), (rect.right - 4 * k, y), 2)
    else:             # gunting
        w = max(2, round(3 * k))
        pygame.draw.line(surf, WHITE, (c - 7 * k, c + 5 * k), (c + 8 * k, c - 13 * k), w)
        pygame.draw.line(surf, WHITE, (c + 7 * k, c + 5 * k), (c - 8 * k, c - 13 * k), w)
        pygame.draw.circle(surf, WHITE, (c - 8 * k, c + 9 * k), 5 * k, w)
        pygame.draw.circle(surf, WHITE, (c + 8 * k, c + 9 * k), 5 * k, w)
    return surf


class Renderer(Canvas):
    def __init__(self):
        super().__init__()
        self.icons = [make_icon(k, RADIUS) for k in range(3)]
        self.big_icons = [make_icon(k, 26) for k in range(3)]

    def draw(self, tokens, counts, history, seconds, max_seconds, mode, winner, reason):
        s = self.screen
        self.header("PERANG SUIT", mode, seconds, max_seconds)
        pygame.draw.rect(s, WHITE, ARENA, 6)
        for t in tokens:
            pos = (int(t.x) - RADIUS, int(t.y) - RADIUS)
            s.blit(self.icons[t.kind], pos)
            if t.flash:
                pygame.draw.circle(s, WHITE, (int(t.x), int(t.y)), RADIUS + 3, 4)

        total = len(tokens)
        for k, (name, color) in enumerate(KINDS):
            y = 1420 + k * 64
            alive = counts[k] > 0
            s.blit(self.big_icons[k], (120, y))
            label = self.font_small.render(name, True, WHITE if alive else GRAY)
            s.blit(label, (190, y + 8))
            pygame.draw.rect(s, (45, 45, 60), (370, y + 12, 460, 30))
            pygame.draw.rect(s, color, (370, y + 12, int(460 * counts[k] / total), 30))
            num = self.font_small.render(str(counts[k]), True, WHITE if alive else GRAY)
            s.blit(num, (960 - num.get_width(), y + 8))

        # Grafik populasi sepanjang waktu
        graph = pygame.Rect(120, 1630, 840, 170)
        pygame.draw.rect(s, (30, 30, 44), graph)
        if len(history) > 1:
            span = max_seconds * FPS
            for k, (_, color) in enumerate(KINDS):
                pts = [(graph.left + graph.width * f / span,
                        graph.bottom - graph.height * c[k] / total) for f, c in history]
                pygame.draw.lines(s, color, False, pts, 4)

        if winner is not None:
            name, color = KINDS[winner]
            self.banner(f"{name.upper()} MENANG!", color, reason, ARENA.center)


def render(output="perang_suit.mp4", seed=None, mode="seimbang", with_audio=True,
           max_seconds=MAX_SECONDS, progress=None):
    if mode not in MODES:
        raise ValueError(f"Mode tidak dikenal: {mode} (pilihan: {', '.join(MODES)})")
    if seed is None:
        seed = random.randrange(2 ** 31)
    rng = random.Random(seed)
    sizes = [18, 18, 18]
    underdog = None
    if mode == "underdog":
        underdog = rng.randrange(3)
        sizes = [8 if k == underdog else 23 for k in range(3)]
    tokens = [Token(k, rng) for k in range(3) for _ in range(sizes[k])]
    rng.shuffle(tokens)
    renderer = Renderer()

    with VideoWriter(output, with_audio, progress) as video:
        frame, winner, end_frame, reason = 0, None, None, ""
        events, eliminations, history = [], [], []
        conversions = 0
        counts = list(sizes)
        while True:
            if winner is None:
                for t in tokens:
                    t.move()
                for i in range(len(tokens)):
                    for j in range(i + 1, len(tokens)):
                        if collide(tokens[i], tokens[j]):
                            conversions += 1
                            events.append(("hit", frame))
                new_counts = [sum(1 for t in tokens if t.kind == k) for k in range(3)]
                for k in range(3):
                    if counts[k] > 0 and new_counts[k] == 0:
                        events.append(("elim", frame))
                        eliminations.append({"nama": KINDS[k][0], "detik": round(frame / FPS, 2)})
                counts = new_counts
                if frame % 15 == 0:
                    history.append((frame, counts))
                survivors = [k for k in range(3) if counts[k] > 0]
                if len(survivors) == 1 or frame >= max_seconds * FPS:
                    winner = max(range(3), key=lambda k: counts[k])
                    end_frame = frame
                    reason = ("Menguasai seluruh arena!" if len(survivors) == 1
                              else f"Waktu habis - jumlah terbanyak ({counts[winner]})")
                    history.append((frame, counts))
                    events.append(("win", frame))
            elif frame - end_frame >= WINNER_SECONDS * FPS:
                break
            seconds = (frame if end_frame is None else end_frame) // FPS
            renderer.draw(tokens, counts, history, seconds, max_seconds, mode, winner, reason)
            video.write(renderer)
            frame += 1
        video.finish(events, seed)

    return {
        "konsep": CONCEPT["id"],
        "output": output,
        "seed": seed,
        "mode": mode,
        "pemenang": KINDS[winner][0],
        "alasan": reason,
        "durasi_pertandingan": round(end_frame / FPS, 2),
        "durasi_video": round(frame / FPS, 2),
        "eliminasi": eliminations,
        "statistik": {
            "jumlah_konversi": conversions,
            "populasi_awal": {KINDS[k][0]: sizes[k] for k in range(3)},
            "populasi_akhir": {KINDS[k][0]: counts[k] for k in range(3)},
            "underdog": KINDS[underdog][0] if underdog is not None else None,
        },
    }


if __name__ == "__main__":
    run_cli(CONCEPT, render)
