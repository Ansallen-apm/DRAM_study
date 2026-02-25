import sys

def convert_axi_to_stl(input_file, output_file):
    current_time = 0
    time_step = 10  # Arbitrary time step between requests since input has no timestamp

    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 4:
                print(f"Skipping malformed line: {line}")
                continue

            rw_mode = parts[0]
            addr_hex = parts[1]
            buswidth_idx = int(parts[2])
            beats_hex = parts[3]

            # 1. Parse Command
            if rw_mode.startswith('AR'):
                command = 'read'
            elif rw_mode.startswith('AW'):
                command = 'write'
            else:
                print(f"Unknown command {rw_mode}, defaulting to read")
                command = 'read'

            # 2. Parse Address
            # Ensure it starts with 0x for STL
            if not addr_hex.startswith('0x') and not addr_hex.startswith('0X'):
                addr_str = '0x' + addr_hex
            else:
                addr_str = addr_hex

            # 3. Calculate Data Length
            # Size per beat = 2 ^ buswidth_idx
            bytes_per_beat = 1 << buswidth_idx
            # Total beats = beats_hex (AxLEN) + 1
            num_beats = int(beats_hex, 16) + 1
            total_size = bytes_per_beat * num_beats

            # 4. Write STL Line
            # Format: Timestamp (DataLength) Command Address
            outfile.write(f"{current_time} ({total_size}) {command} {addr_str}\n")

            current_time += time_step

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 axi_to_stl.py <input_axi_file> <output_stl_file>")
        sys.exit(1)

    convert_axi_to_stl(sys.argv[1], sys.argv[2])
    print(f"Converted {sys.argv[1]} to {sys.argv[2]}")
