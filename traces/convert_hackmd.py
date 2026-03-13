import sys
import os

def convert_trace(input_file, stl_file, ldst_file):
    with open(input_file, 'r') as fin, open(stl_file, 'w') as f_stl, open(ldst_file, 'w') as f_ldst:
        current_time = 0
        for line in fin:
            parts = line.strip().split()
            if len(parts) < 4:
                continue

            cmd_type = parts[0]
            addr_hex = parts[1]
            size_pow = int(parts[2])
            burst_hex = parts[3]

            # Usually AXI format: [R/W] [Addr] [Size_Pow_2] [Burst_Len_Minus_1] [ThreadID...]
            addr = int(addr_hex, 16)
            bytes_per_beat = 1 << size_pow
            beats = int(burst_hex, 16) + 1
            total_bytes = bytes_per_beat * beats

            is_read = cmd_type.startswith('AR')
            cmd_str = 'read' if is_read else 'write'
            ldst_str = 'LD' if is_read else 'ST'

            # For DRAMSys, we want to split large requests (like 4KB) into 1KB chunks
            # to trigger the Channel Interleaving properly (because CH bit is at bit 10 = 1024).
            CHUNK_SIZE = 1024

            num_chunks = total_bytes // CHUNK_SIZE
            if num_chunks == 0: num_chunks = 1

            for c in range(num_chunks):
                chunk_addr = addr + c * CHUNK_SIZE
                f_stl.write(f"{current_time} ({CHUNK_SIZE}) {cmd_str} 0x{chunk_addr:X}\n")
                current_time += 1

                # For Ramulator2, break the 1KB chunk into 64B cache lines
                num_cachelines = CHUNK_SIZE // 64
                for cl in range(num_cachelines):
                    cl_addr = chunk_addr + cl * 64
                    f_ldst.write(f"{ldst_str} 0x{cl_addr:X}\n")

if __name__ == "__main__":
    convert_trace("traces/hackmd_trace.axi", "traces/hackmd_trace.stl", "traces/hackmd_trace.ldst")
    print("Trace successfully parsed and converted to .stl and .ldst formats (split into 1KB chunks).")
