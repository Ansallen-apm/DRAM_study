
def generate_stl_trace(filename, num_requests_per_master, burst_size, offsets):
    with open(filename, 'w') as f:
        current_time = 0
        cycle_step = 1

        # burst_size = 256

        for i in range(num_requests_per_master):
            for master_idx, offset in enumerate(offsets):
                addr = offset + (i * burst_size)
                # Absolute time
                f.write(f"{current_time} ({burst_size}) read 0x{addr:X}\n")
                current_time += cycle_step

if __name__ == "__main__":
    offsets = [0, 131072, 262144, 393216]
    generate_stl_trace("configs/interleaved.stl", 10000, 256, offsets)
