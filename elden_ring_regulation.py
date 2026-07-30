#!/usr/bin/env python3
"""Open and repack Elden Ring's regulation.bin.

Layout, outermost first:
  AES-256-CBC  - 16-byte IV prefix, then ciphertext. Key is the well-known public
                 one shipped in every ER modding tool.
  DCX          - FromSoftware container. Elden Ring uses zstd ("ZSTD" magic in the
                 format block); older games used DEFLATE or Oodle.
  BND4         - archive holding one file per param table (GameAreaParam.param,
                 SpEffectParam.param, ...).

Everything here is byte-exact on the way back out: unpack() -> pack() with no
edits must reproduce the original file, and that round-trip is the gate before
any modified regulation is written anywhere near the game.

Needs pycryptodome and zstandard, neither of which the other scripts here use:
    pip install --target <dir> pycryptodome zstandard   # then PYTHONPATH=<dir>

WARNING - a modified regulation.bin is NOT loadable under CrossOver. Any change
to param content, down to a single float, makes the game abort when a character
loads, while the unmodified file loads fine. Measured both ways with the same
profile and save. This module is kept because the format work is reusable (on
Windows, or if CrossOver changes), not because the result works here. See
plans/reports/regulation-modding-260730-1215-*.md."""
import io
import struct

from Crypto.Cipher import AES
import zstandard

# erRegulationKey, verbatim from SoulsFormats/Util/SFUtil.cs
CHUNK = 65536   # FromSoft flushes a zstd block every 64 KiB of input
REGULATION_KEY = bytes.fromhex(
    "99BFFC366A6BC8C6F5827D093602D676C42892A01C207FB024D3AF4E493FEF99")


def decrypt(raw):
    iv, body = raw[:16], raw[16:]
    body = body[:len(body) // 16 * 16]
    return AES.new(REGULATION_KEY, AES.MODE_CBC, iv).decrypt(body), iv


def encrypt(plain, iv):
    pad = (-len(plain)) % 16
    return iv + AES.new(REGULATION_KEY, AES.MODE_CBC, iv).encrypt(plain + b"\0" * pad)


def dcx_unpack(data):
    """Split a DCX into (compressed payload, header info needed to rebuild it).

    Header as it appears in this file, all big-endian:
        0x00 'DCX\\0'   0x18 'DCS\\0'   0x1C uncompressed size
        0x20 compressed size            0x24 'DCP\\0'   0x28 'ZSTD'
        0x44 'DCA\\0'   0x48 DCA size   payload follows immediately
    Only the two sizes ever change, so the rest of the header is kept verbatim."""
    assert data[:4] == b"DCX\0", f"not a DCX container: {data[:4]!r}"
    assert data[0x18:0x1C] == b"DCS\0", data[0x18:0x1C]
    assert data[0x24:0x28] == b"DCP\0", data[0x24:0x28]
    raw_size, comp_size = struct.unpack_from(">II", data, 0x1C)
    fmt = data[0x28:0x2C]
    dca_off = 0x44
    assert data[dca_off:dca_off + 4] == b"DCA\0", data[dca_off:dca_off + 4]
    (dca_size,) = struct.unpack_from(">I", data, dca_off + 4)
    start = dca_off + dca_size
    comp = data[start:start + comp_size]
    return comp, dict(head=data[:start], fmt=fmt, raw_size=raw_size)


def dcx_pack(header, payload):
    head = bytearray(header["head"])
    struct.pack_into(">II", head, 0x1C, header["raw_size"], len(payload))
    return bytes(head) + payload


def unpack(path):
    raw = open(path, "rb").read()
    plain, iv = decrypt(raw)
    comp, hdr = dcx_unpack(plain)
    assert hdr["fmt"] == b"ZSTD", f"unexpected DCX format {hdr['fmt']!r}"
    bnd = zstandard.ZstdDecompressor().decompress(comp, max_output_size=hdr["raw_size"] * 2)
    return bnd, dict(iv=iv, dcx=hdr, plain_len=len(plain))


def pack(bnd, meta, level=21):
    """Recompress and re-encrypt.

    The zstd frame must look exactly like FromSoftware's or the game rejects the
    file and deliberately aborts - it writes 0xDEADBA to address 0, which shows up
    as `movl $0xdeadba, 0` in a Wine crash dump rather than as a normal error.
    Their frames carry a 0x00 header descriptor: no content size, no checksum, no
    dictionary id. python-zstandard writes the content size by default, giving
    0x80 instead, so all three have to be switched off explicitly. The uncompressed
    length is not lost by this - it already lives in the DCX header at 0x1C.

    FromSoftware also compresses as a STREAM, flushing a block every 64 KiB of
    input, so their frame holds one zstd block per 64 KiB: 53,879,376 bytes of
    BND4 becomes 825 blocks with none larger than 54,874. A one-shot compress()
    lets zstd pick its own 128 KiB boundaries, which produced 462-632 much larger
    blocks at every level from 3 to 18 - no level reproduces 825. So the chunking
    is the parameter, not the level, and it has to be reproduced explicitly."""
    meta["dcx"]["raw_size"] = len(bnd)
    cctx = zstandard.ZstdCompressor(level=level, write_content_size=False,
                                    write_checksum=False, write_dict_id=False)
    co = cctx.compressobj()
    out = []
    for off in range(0, len(bnd), CHUNK):
        out.append(co.compress(bytes(bnd[off:off + CHUNK])))
        out.append(co.flush(zstandard.COMPRESSOBJ_FLUSH_BLOCK))
    out.append(co.flush(zstandard.COMPRESSOBJ_FLUSH_FINISH))
    comp = b"".join(out)
    assert comp[4] == 0x00, f"frame descriptor {comp[4]:#02x}, FromSoft uses 0x00"
    plain = dcx_pack(meta["dcx"], comp)
    return encrypt(plain, meta["iv"])


# --- BND4 -------------------------------------------------------------------
def bnd4_entries(bnd):
    """Parse the file table. Entry layout for this BND4 (fileHeaderSize = 36):
        0x00 format byte + 3 pad     0x04 -1
        0x08 compressed size (q)     0x10 uncompressed size (q)
        0x18 data offset (I)         0x1C id (I)          0x20 name offset (i)
    Names are UTF-16LE, NUL-terminated."""
    assert bnd[:4] == b"BND4", bnd[:4]
    count, = struct.unpack_from("<i", bnd, 0x0C)
    entry_size, = struct.unpack_from("<q", bnd, 0x20)
    out = []
    off = 0x40
    for i in range(count):
        size, = struct.unpack_from("<q", bnd, off + 0x08)
        data_off, = struct.unpack_from("<I", bnd, off + 0x18)
        ident, = struct.unpack_from("<I", bnd, off + 0x1C)
        name_off, = struct.unpack_from("<i", bnd, off + 0x20)
        end = name_off
        while bnd[end:end + 2] != b"\0\0":
            end += 2
        out.append(dict(index=i, hdr=off, size=size, data_off=data_off, id=ident,
                        name=bnd[name_off:end].decode("utf-16-le")))
        off += entry_size
    return out


if __name__ == "__main__":
    import sys
    bnd, meta = unpack(sys.argv[1])
    print(f"BND4 {len(bnd):,} bytes")
    ents = bnd4_entries(bnd)
    print(f"{len(ents)} entries")
    for e in ents[:5]:
        print(f"  {e['name']}  {e['size']:,}B @ {e['data_off']:#x}")
    print("  ...")
    hits = [e for e in ents if "SpEffectParam" in e["name"] or "CalcCorrect" in e["name"]]
    for e in hits:
        print(f"  MATCH {e['name']}  {e['size']:,}B")
