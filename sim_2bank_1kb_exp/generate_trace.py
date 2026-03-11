import os
import argparse

def generate_2bank_1kb_trace(output_file, num_1kb_requests=64):
    with open(output_file, 'w') as f:
        row_0 = 0
        row_1 = 0
        for i in range(num_1kb_requests):
            bank = i % 2
            if bank == 0:
                current_row = row_0
                row_0 += 1
            else:
                current_row = row_1
                row_1 += 1

            base_addr = (current_row << 16) | (bank << 13)

            for j in range(8):
                col_offset = j * 128
                addr = base_addr + col_offset
                f.write(f"ARx {addr:016X} 6 01\n")

if __name__ == "__main__":
    generate_2bank_1kb_trace("trace_2bank_1kb.axi", 64)
