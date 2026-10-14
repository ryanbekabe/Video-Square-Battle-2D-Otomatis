"""Produksi video: penomoran episode, metadata unggahan, daftar hasil, dan klasemen."""
import glob
import json
import os
import random
import time

from concepts import CONCEPTS

OUT_DIR = "output"
TAGS = ["simulation", "satisfying", "who will win", "shorts"]


def load_videos(out_dir=OUT_DIR):
    """Baca semua metadata *.json di folder output, terbaru lebih dulu."""
    videos = []
    for path in glob.glob(os.path.join(out_dir, "*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            continue
        base = os.path.splitext(os.path.basename(path))[0]
        meta.setdefault("konsep", "square_battle")   # metadata lama sebelum ada banyak konsep
        meta.setdefault("dibuat", os.path.getmtime(path))
        meta["file"] = base + ".mp4"
        meta["ada_video"] = os.path.exists(os.path.join(out_dir, meta["file"]))
        videos.append(meta)
    videos.sort(key=lambda v: v["dibuat"], reverse=True)
    return videos


def next_episode(concept_id, out_dir=OUT_DIR):
    """Nomor episode selalu naik, termasuk melewati episode yang sudah dihapus (dicatat di manifest)."""
    eps = [v.get("episode", 0) for v in load_videos(out_dir) if v["konsep"] == concept_id]
    try:
        with open(os.path.join(out_dir, "manifest.jsonl"), encoding="utf-8") as f:
            for line in f:
                try:
                    meta = json.loads(line)
                except ValueError:
                    continue
                if meta.get("konsep", "square_battle") == concept_id:
                    eps.append(meta.get("episode", 0))
    except OSError:
        pass
    episode = max(eps, default=0) + 1
    while os.path.exists(os.path.join(out_dir, f"{concept_id}_{episode:03d}.mp4")):
        episode += 1
    return episode


def describe(meta, concept, episode):
    lines = [f"{concept['nama']} #{episode} - mode {meta['mode']}.",
             concept["deskripsi"], "",
             f"Pemenang: {meta['pemenang']} ({meta['alasan']})."]
    if meta.get("eliminasi"):
        lines += ["", "Urutan tereliminasi:"]
        lines += [f"- {e['nama']} ({e['detik']}s)" for e in meta["eliminasi"]]
    stats = meta.get("statistik") or {}
    if stats:
        lines += ["", "Statistik pertandingan:"]
        lines += [f"- {label}: {value}" for label, value in _stat_lines(stats)]
    lines += ["", "Tebak pemenang berikutnya di kolom komentar!", f"Seed: {meta['seed']}"]
    return "\n".join(lines)


def _stat_lines(stats, prefix=""):
    """Ratakkan statistik untuk deskripsi unggahan yang mudah dibaca manusia."""
    rows = []
    for key, value in stats.items():
        label = f"{prefix} - {key}" if prefix else key.replace("_", " ").capitalize()
        if value is None:
            continue
        if isinstance(value, dict):
            rows.extend(_stat_lines(value, label))
        elif isinstance(value, bool):
            rows.append((label, "Ya" if value else "Tidak"))
        else:
            rows.append((label, value))
    return rows


def produce(concept_id, mode="acak", seed=None, out_dir=OUT_DIR, with_audio=True,
            max_seconds=None, progress=None):
    """Render satu episode, simpan metadata JSON + manifest, dan kembalikan metadatanya."""
    module = CONCEPTS[concept_id]
    concept = module.CONCEPT
    if seed is None:
        seed = random.randrange(2 ** 31)
    if mode in (None, "acak"):
        mode = random.Random(seed).choice(concept["mode"])
    if mode not in concept["mode"]:
        raise ValueError(f"Mode '{mode}' tidak tersedia untuk {concept['nama']}")
    os.makedirs(out_dir, exist_ok=True)
    episode = next_episode(concept_id, out_dir)
    path = os.path.join(out_dir, f"{concept_id}_{episode:03d}.mp4")

    meta = module.render(path, seed, mode, with_audio, max_seconds or concept["durasi_maks"],
                         progress)
    meta.update(episode=episode,
                dibuat=time.time(),
                judul=f"Siapa yang Menang? {concept['nama']} #{episode}",
                deskripsi=describe(meta, concept, episode),
                tag=TAGS + [concept["nama"].lower()])
    with open(path[:-4] + ".json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "manifest.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    return meta


def delete_video(name, out_dir=OUT_DIR):
    """Hapus video beserta metadatanya. `name` adalah nama file .mp4 (tanpa folder)."""
    base = os.path.splitext(os.path.basename(name))[0]
    removed = False
    for ext in (".mp4", ".json"):
        p = os.path.join(out_dir, base + ext)
        if os.path.exists(p):
            os.remove(p)
            removed = True
    return removed


def standings(videos):
    """Klasemen per konsep: jumlah kemenangan setiap peserta."""
    table = {}
    for v in videos:
        rows = table.setdefault(v["konsep"], {})
        row = rows.setdefault(v["pemenang"], {"nama": v["pemenang"], "menang": 0})
        row["menang"] += 1
    result = {}
    for concept_id, rows in table.items():
        total = sum(r["menang"] for r in rows.values())
        ranked = sorted(rows.values(), key=lambda r: (-r["menang"], r["nama"]))
        for r in ranked:
            r["persen"] = round(100 * r["menang"] / total, 1)
        result[concept_id] = {"total": total, "peringkat": ranked}
    return result
