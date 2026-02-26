import sys
import argparse

def convert_axi_to_stl(input_file, output_file, addr_mask=None):
    current_time = 0
    time_step = 1  # 1ns for 1000MHz

    mask_int = None
    if addr_mask:
        try:
            mask_int = int(addr_mask, 0)
        except ValueError:
            print(f"Invalid mask: {addr_mask}")
            sys.exit(1)

    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 4:
                    continue

                rw_mode = parts[0]
                addr_hex = parts[1]

                # Command
                if rw_mode.startswith('AR'):
                    command = 'read'
                elif rw_mode.startswith('AW'):
                    command = 'write'
                else:
                    # Skip non-read/write lines
                    continue

                # Address Masking
                try:
                    addr_val = int(addr_hex, 16)
                    if mask_int is not None:
                        addr_val = addr_val & mask_int
                    addr_str = hex(addr_val)
                except ValueError:
                    continue

                # Size Calculation
                try:
                    buswidth_idx = int(parts[2])
                    beats_hex = parts[3]
                    bytes_per_beat = 1 << buswidth_idx
                    num_beats = int(beats_hex, 16) + 1
                    total_size = bytes_per_beat * num_beats
                except ValueError:
                    continue

                # STL: timestamp (size) command address
                # Using 1ns steps to avoid overlapping transactions at same timestamp causing issues
                outfile.write(f"{current_time} ({total_size}) {command} {addr_str}\n")

                current_time += time_step
    except FileNotFoundError:
        print(f"File not found: {input_file}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert AXI trace to DRAMSys STL format.")
    parser.add_argument("input_file", help="Input AXI trace file")
    parser.add_argument("output_file", help="Output STL trace file")
    parser.add_argument("--mask", help="Address mask (hex or int) to apply", default=None)

    args = parser.parse_args()

    convert_axi_to_stl(args.input_file, args.output_file, args.mask)
