"""Produksi massal video Square Battle beserta metadata untuk unggahan."""
import argparse
import json
import os
import random

from square_battle import MODES, render


def describe(meta, episode):
    lines = [f"Square Battle #{episode} - mode {meta['mode']}.",
             f"Pemenang: {meta['pemenang']} ({meta['alasan']}).", "",
             "Urutan tereliminasi:"]
    lines += [f"- {e['nama']} ({e['detik']}s)" for e in meta["eliminasi"]] or ["- (tidak ada)"]
    lines += ["", f"Seed: {meta['seed']}"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Render banyak video Square Battle sekaligus.")
    ap.add_argument("-n", "--count", type=int, default=3, help="jumlah video")
    ap.add_argument("--start", type=int, default=1, help="nomor episode pertama")
    ap.add_argument("--mode", choices=MODES + ("acak",), default="acak")
    ap.add_argument("--seed", type=int, help="seed dasar; episode ke-i memakai seed+i")
    ap.add_argument("--out", default="output", help="folder hasil")
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    picker = random.Random(args.seed)
    manifest = os.path.join(args.out, "manifest.jsonl")
    for i in range(args.count):
        episode = args.start + i
        seed = args.seed + i if args.seed is not None else random.randrange(2 ** 31)
        mode = picker.choice(MODES) if args.mode == "acak" else args.mode
        path = os.path.join(args.out, f"battle_{episode:03d}.mp4")
        print(f"[{i + 1}/{args.count}] Render episode #{episode} (mode {mode}, seed {seed})...")
        meta = render(path, seed, mode, not args.no_audio)
        meta.update(episode=episode,
                    judul=f"Siapa yang Menang? Square Battle #{episode}",
                    deskripsi=describe(meta, episode),
                    tag=["square battle", "satisfying", "simulation", "shorts"])
        with open(path[:-4] + ".json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        with open(manifest, "a", encoding="utf-8") as f:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
        print(f"    -> {path} | pemenang {meta['pemenang']} ({meta['durasi_video']}s)")


if __name__ == "__main__":
    main()
