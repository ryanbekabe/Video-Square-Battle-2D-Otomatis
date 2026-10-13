"""Produksi massal video dari semua konsep, beserta metadata untuk unggahan."""
import argparse
import random

from concepts import CONCEPTS
from production import OUT_DIR, produce


def main():
    ap = argparse.ArgumentParser(description="Render banyak video sekaligus.")
    ap.add_argument("-n", "--count", type=int, default=3, help="jumlah video")
    ap.add_argument("--konsep", choices=list(CONCEPTS) + ["acak"], default="square_battle")
    ap.add_argument("--mode", default="acak", help="mode konsep, atau 'acak'")
    ap.add_argument("--seed", type=int, help="seed dasar; video ke-i memakai seed+i")
    ap.add_argument("--out", default=OUT_DIR, help="folder hasil")
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()

    if args.konsep != "acak" and args.mode != "acak" \
            and args.mode not in CONCEPTS[args.konsep].CONCEPT["mode"]:
        ap.error(f"mode '{args.mode}' tidak tersedia untuk {args.konsep}")
    if args.konsep == "acak" and args.mode != "acak":
        ap.error("--konsep acak hanya bisa dipakai dengan --mode acak")

    picker = random.Random(args.seed)
    for i in range(args.count):
        seed = args.seed + i if args.seed is not None else random.randrange(2 ** 31)
        concept = picker.choice(list(CONCEPTS)) if args.konsep == "acak" else args.konsep
        print(f"[{i + 1}/{args.count}] Render {concept} (mode {args.mode}, seed {seed})...")
        meta = produce(concept, args.mode, seed, args.out, not args.no_audio)
        print(f"    -> {meta['output']} | {meta['judul']} | pemenang {meta['pemenang']} "
              f"({meta['durasi_video']}s)")


if __name__ == "__main__":
    main()
