import os

def generate_multi_master_trace(output_dir):
    num_masters = 4
    requests_per_master = 30
    base_addr_start = 0x20000
    offset_between_masters = 512 * 1024 # 512KB
    incr_per_request = 0x1000 # 4KB

    for m in range(num_masters):
        base_addr = base_addr_start + (m * offset_between_masters)
        stl_filename = os.path.join(output_dir, f"master{m}.stl")
        ldst_filename = os.path.join(output_dir, f"master{m}.ldst")

        with open(stl_filename, 'w') as f_stl, open(ldst_filename, 'w') as f_ldst:
            current_time = 0
            for i in range(requests_per_master):
                addr_4k = base_addr + (i * incr_per_request)

                # Split the 4KB request into four 1KB requests to trigger CH interleaving explicitly
                for chunk in range(4):
                    addr_1k = addr_4k + (chunk * 1024)

                    # STL format for DRAMSys: timestamp (size) cmd addr
                    # Send 1KB requests. Time spacing can be nominal (e.g. 1ns apart) to simulate back-to-back injection.
                    f_stl.write(f"{current_time} (1024) read 0x{addr_1k:X}\n")
                    current_time += 1

                    # For Ramulator2 (LDST format), we break the 1KB into 64B cachelines.
                    # 1024 / 64 = 16 cachelines per chunk.
                    for beat in range(16):
                        beat_addr = addr_1k + (beat * 64)
                        f_ldst.write(f"LD 0x{beat_addr:X}\n")

if __name__ == "__main__":
    generate_multi_master_trace(".")
    print("Traces generated successfully, split into 1KB chunks.")
