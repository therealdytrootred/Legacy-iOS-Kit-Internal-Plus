import argparse
import sys
import os

# The fixed search pattern (37 bytes)
SEARCH_PATTERN = "2D 76 00 69 61 6E 63 65 20 6F 6E 20 74 68 69 73 20 63 65 72 74 69 66 69 63 61 74 65 20 62 79 20 61 6E 79 20 70 61"

def parse_hex_string(hex_str):
    """Parse a hex string in various formats (space-separated, 0x-prefixed, raw) into bytes."""
    # Normalise: strip 0x prefixes and whitespace, then parse
    cleaned = hex_str.replace("0x", "").replace("0X", "").replace(" ", "").replace(",", "")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as e:
        print(f"Error: Invalid hex string: {e}")
        sys.exit(1)

def patch_file(file_path, replacement_hex):
    search_bytes = parse_hex_string(SEARCH_PATTERN)
    replace_bytes = parse_hex_string(replacement_hex)

    search_len = len(search_bytes)   # 37 bytes
    replace_len = len(replace_bytes)

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    try:
        with open(file_path, 'rb') as f:
            data = bytearray(f.read())
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    idx = data.find(search_bytes)
    if idx == -1:
        print("Error: Search pattern not found in the file.")
        sys.exit(1)

    print(f"Pattern found at offset 0x{idx:X} ({idx}).")

    if replace_len <= search_len:
        # --- Shorter or equal ---
        # Overwrite only the first replace_len bytes of the match,
        # then write a 00 terminator immediately after the replacement.
        # Bytes between the terminator and the end of the original match
        # are left intact (we only touch replace_len + 1 bytes).
        end = idx + replace_len + 1          # +1 for the null terminator
        if end > len(data):
            print("Error: Not enough space in file for replacement + null terminator.")
            sys.exit(1)
        data[idx:idx + replace_len] = replace_bytes
        data[idx + replace_len] = 0x00
        print(f"Replacement ({replace_len} bytes) is shorter than / equal to search "
              f"pattern ({search_len} bytes). Overwrote first {replace_len} byte(s) "
              f"and placed a 00 terminator at offset 0x{idx + replace_len:X}.")

    else:
        # --- Longer ---
        # Overwrite the full search pattern AND continue into the bytes that
        # follow it in the file, then place a 00 terminator right after.
        end = idx + replace_len + 1          # +1 for the null terminator
        if end > len(data):
            print("Error: Not enough space in file for replacement + null terminator.")
            sys.exit(1)
        data[idx:idx + replace_len] = replace_bytes
        data[idx + replace_len] = 0x00
        print(f"Replacement ({replace_len} bytes) is longer than search pattern "
              f"({search_len} bytes). Overwrote {replace_len} byte(s) starting at "
              f"offset 0x{idx:X} and placed a 00 terminator at offset "
              f"0x{idx + replace_len:X}.")

    try:
        with open(file_path, 'wb') as f:
            f.write(data)
        print("Successfully patched.")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Patch a binary file by replacing a fixed search pattern with a "
            "user-supplied hex string.\n\n"
            "  If the replacement is SHORTER than the search pattern, only the first "
            "N bytes of the pattern are overwritten, followed by a 00 terminator.\n"
            "  If the replacement is LONGER than the search pattern, the pattern AND "
            "the bytes that follow it are overwritten, followed by a 00 terminator.\n\n"
            "The hex string may be space-separated (e.g. 'DE AD BE EF') or "
            "continuous (e.g. 'DEADBEEF')."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", help="Path to the binary file to patch.")
    parser.add_argument(
        "replacement",
        help="Hex string to write (e.g. '2D 76 20 61 6D' or '2D762061 6D').",
    )

    args = parser.parse_args()
    patch_file(args.file, args.replacement)
