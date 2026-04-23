#!/usr/bin/env python3
"""
Parse the UDIF XML resource fork to extract volume sector count / capacity.
"""
import struct, sys, zlib, plistlib, math

path = sys.argv[1]
with open(path, 'rb') as f:
    f.seek(0, 2)
    file_size = f.tell()

    # Read KOLY
    f.seek(file_size - 512)
    koly = f.read(512)
    assert koly[0:4] == b'koly', "Not a UDIF DMG"

    rsrc_offset = struct.unpack_from('>Q', koly, 0xd8)[0]
    rsrc_length = struct.unpack_from('>Q', koly, 0xe0)[0]

    f.seek(rsrc_offset)
    xml_data = f.read(rsrc_length)
    plist = plistlib.loads(xml_data)

    blkx = plist.get('resource-fork', {}).get('blkx', [])
    total_sectors = 0
    for entry in blkx:
        data = entry.get('Data', b'')
        if len(data) < 48:
            continue
        sector_start = struct.unpack_from('>Q', data, 8)[0]
        sector_count = struct.unpack_from('>Q', data, 16)[0]
        if sector_count < 0xFFFFFFFF:
            total_sectors = max(total_sectors, sector_start + sector_count)

    print(math.ceil(total_sectors * 512 / 1024**2))
