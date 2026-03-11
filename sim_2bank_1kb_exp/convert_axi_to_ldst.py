import sys
def convert_trace(infile, outfile):
    with open(infile, 'r') as fin, open(outfile, 'w') as fout:
        for line in fin:
            parts = line.strip().split()
            if not parts: continue
            if parts[0] == 'ARx': cmd = 'LD'
            elif parts[0] == 'AWx': cmd = 'ST'
            else: continue
            addr = parts[1]
            fout.write(f"{cmd} 0x{addr}\n")

if __name__ == "__main__":
    convert_trace(sys.argv[1], sys.argv[2])
