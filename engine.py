"""Komponen bersama semua konsep video: kanvas, teks, encoder FFmpeg, dan penggabungan audio."""
import argparse
import os
import shutil
import subprocess

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")   # jalan tanpa membuka jendela
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

import audio

W, H, FPS = 1080, 1920, 60
WINNER_SECONDS = 3

BG = (18, 18, 28)
WHITE = (255, 255, 255)
GRAY = (110, 110, 120)

PARTICIPANTS = [("Merah", (235, 64, 52)), ("Biru", (52, 120, 235)),
                ("Hijau", (46, 204, 113)), ("Kuning", (241, 196, 15)),
                ("Ungu", (155, 89, 182)), ("Oranye", (230, 126, 34))]


class Cancelled(Exception):
    """Dilempar oleh callback progress untuk menghentikan render di tengah jalan."""


class Canvas:
    def __init__(self):
        pygame.init()
        self.screen = pygame.Surface((W, H))
        self.font_big = pygame.font.SysFont("arial", 84, bold=True)
        self.font_mid = pygame.font.SysFont("arial", 48, bold=True)
        self.font_small = pygame.font.SysFont("arial", 34, bold=True)
        self.overlay = pygame.Surface((900, 260), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 190))

    def text(self, font, msg, color, center):
        img = font.render(msg, True, color)
        self.screen.blit(img, img.get_rect(center=center))

    def header(self, title, mode, seconds, max_seconds):
        self.screen.fill(BG)
        img = self.font_big.render(title, True, WHITE)
        if img.get_width() > W - 120:   # judul panjang diperkecil agar muat
            scale = (W - 120) / img.get_width()
            img = pygame.transform.smoothscale(img, (W - 120, int(img.get_height() * scale)))
        self.screen.blit(img, img.get_rect(center=(W // 2, 220)))
        self.text(self.font_small, f"Mode: {mode.upper()}", GRAY, (W // 2, 300))
        self.text(self.font_mid, f"{seconds}s / {max_seconds}s", (200, 200, 210), (W // 2, 390))

    def banner(self, title, color, reason, center):
        box = self.overlay.get_rect(center=center)
        self.screen.blit(self.overlay, box)
        self.text(self.font_big, title, color, (box.centerx, box.centery - 40))
        self.text(self.font_small, reason, WHITE, (box.centerx, box.centery + 50))

    def frame_bytes(self):
        return pygame.image.tobytes(self.screen, "RGB")


class VideoWriter:
    """Kirim frame ke FFmpeg; jika audio aktif, soundtrack digabungkan saat finish()."""

    def __init__(self, output, with_audio=True, progress=None):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg tidak ditemukan. Pasang FFmpeg dan pastikan ada di PATH.")
        self.output, self.with_audio, self.progress = output, with_audio, progress
        self.video_path = output + ".video.mp4" if with_audio else output
        self.wav_path = output + ".audio.wav"
        self.frames = 0
        self.proc = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
             self.video_path],
            stdin=subprocess.PIPE)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.abort()

    def write(self, canvas):
        self.proc.stdin.write(canvas.frame_bytes())
        self.frames += 1
        if self.progress and self.frames % 30 == 0:
            self.progress(self.frames)

    def finish(self, events, seed):
        self.proc.stdin.close()
        if self.proc.wait() != 0:
            raise RuntimeError(f"FFmpeg gagal menulis {self.video_path}")
        if not self.with_audio:
            return
        audio.build_soundtrack(self.wav_path, events, FPS, self.frames, seed=seed)
        result = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", self.video_path, "-i", self.wav_path,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", self.output])
        self._remove(self.video_path, self.wav_path)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg gagal menggabungkan audio ke {self.output}")

    def abort(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        self.proc.kill()
        self.proc.wait()
        self._remove(self.video_path, self.wav_path, self.output)

    @staticmethod
    def _remove(*paths):
        for p in paths:
            if os.path.exists(p):
                os.remove(p)


def run_cli(concept, render):
    """CLI standar untuk setiap konsep: python <konsep>.py [--seed] [--mode] ..."""
    ap = argparse.ArgumentParser(description=f"Render satu video {concept['nama']}.")
    ap.add_argument("-o", "--output", default=f"{concept['id']}.mp4")
    ap.add_argument("--seed", type=int, help="seed acak (untuk membuat ulang video yang sama)")
    ap.add_argument("--mode", choices=concept["mode"], default=concept["mode"][0])
    ap.add_argument("--no-audio", action="store_true", help="render tanpa efek suara/musik")
    ap.add_argument("--max-seconds", type=int, default=concept["durasi_maks"],
                    help="batas durasi pertandingan (detik)")
    args = ap.parse_args()
    meta = render(args.output, args.seed, args.mode, not args.no_audio, args.max_seconds)
    print(f"Selesai: {meta['output']} | seed {meta['seed']} | pemenang {meta['pemenang']} "
          f"({meta['alasan']}, {meta['durasi_video']}s)")
