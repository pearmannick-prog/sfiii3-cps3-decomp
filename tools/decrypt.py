#!/usr/bin/env python3
"""Combine and decrypt CPS-3 program SIMMs (1 and 2) into a flat big-endian image.

usage: decrypt.py <rom_dir> <out.bin> [--key1 HEX --key2 HEX]
Output is mapped at 0x06000000 (SIMM1 = first 8 MB, SIMM2 = next 8 MB).
Defaults are the Street Fighter III 3rd Strike keys (as documented in MAME).
"""
import argparse, glob, os, sys
import numpy as np

BASE = 0x06000000

def rotl(v, n):
    v &= 0xFFFF
    return ((v << n) | (v >> (16 - n))) & 0xFFFF

def rotxor(val, x):
    val &= 0xFFFF; x &= 0xFFFF
    res = (val + rotl(val, 2)) & 0xFFFF
    return (rotl(res, 4) ^ (res & (val ^ x))) & 0xFFFF

def mask(addr, k1, k2):
    addr ^= k1
    val = (addr & 0xFFFF) ^ 0xFFFF
    val = rotxor(val, k2 & 0xFFFF)
    val ^= (addr >> 16) ^ 0xFFFF
    val = rotxor(val, k2 >> 16)
    val ^= (addr & 0xFFFF) ^ (k2 & 0xFFFF)
    return (val | (val << 16)) & 0xFFFFFFFF

def mask_vec(addrs, k1, k2):
    a = addrs ^ np.uint32(k1)
    def rl(v, n): return ((v << n) | (v >> (16 - n))) & 0xFFFF
    def rx(v, x):
        r = (v + rl(v, 2)) & 0xFFFF
        return (rl(r, 4) ^ (r & (v ^ x))) & 0xFFFF
    lo = (a & 0xFFFF).astype(np.uint32); hi = (a >> 16).astype(np.uint32)
    v = lo ^ 0xFFFF
    v = rx(v, k2 & 0xFFFF)
    v ^= hi ^ 0xFFFF
    v = rx(v, k2 >> 16)
    v ^= lo ^ (k2 & 0xFFFF)
    return (v | (v << 16)).astype(np.uint32)

def load_simm(rom_dir, n):
    parts = []
    for i in range(4):
        m = sorted(glob.glob(os.path.join(glob.escape(rom_dir), f"*simm{n}.{i}")))
        if len(m) != 1:
            sys.exit(f"expected exactly one *simm{n}.{i} in {rom_dir}, found {len(m)}")
        parts.append(np.fromfile(m[0], dtype=np.uint8).astype(np.uint32))
    return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom_dir"); ap.add_argument("out")
    ap.add_argument("--key1", type=lambda s: int(s, 16), default=0xA55432B4)
    ap.add_argument("--key2", type=lambda s: int(s, 16), default=0x0C129981)
    a = ap.parse_args()
    words = np.concatenate([load_simm(a.rom_dir, 1), load_simm(a.rom_dir, 2)])
    addrs = (BASE + 4 * np.arange(len(words), dtype=np.uint64)).astype(np.uint32)
    assert int(mask_vec(addrs[:64], a.key1, a.key2)[5]) == mask(int(addrs[5]), a.key1, a.key2)
    dec = words ^ mask_vec(addrs, a.key1, a.key2)
    dec.astype(">u4").tofile(a.out)
    print(f"wrote {a.out}: {len(dec)*4:#x} bytes at {BASE:#010x}")

if __name__ == "__main__":
    main()
