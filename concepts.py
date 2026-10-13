"""Daftar semua konsep video. Tambahkan modul konsep baru di sini agar muncul di batch dan dashboard."""
import rps_war
import square_battle
import sumo
import wilayah

MODULES = [square_battle, rps_war, sumo, wilayah]
CONCEPTS = {m.CONCEPT["id"]: m for m in MODULES}


def info():
    return [dict(m.CONCEPT, mode=list(m.CONCEPT["mode"])) for m in MODULES]
