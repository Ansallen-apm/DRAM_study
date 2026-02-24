
def generate_stl_trace(filename, num_requests_per_master, burst_size, offsets):
    # .stl is not accepted by default Simulator.cpp unless it has a specific header or extension logic.
    # The error " is not a valid trace format" suggests the extension parsing failed or it expects .stl for Absolute?
    # Simulator.cpp:126 check:
    # if (extension == ".stl") traceType = Absolute;
    # else if (extension == ".rstl") traceType = Relative;
    # else FATAL.

    # My previous run failed with " is not a valid trace format." (Empty string?)
    # Maybe because the path was relative?
    # Or maybe the file extension parsing in C++ `std::filesystem::path::extension()` behavior?

    # Let's try .stl again but ensure the file content is correct for Absolute mode.

    with open(filename, 'w') as f:
        current_time = 0
        cycle_step = 1

        for i in range(num_requests_per_master):
            for master_idx, offset in enumerate(offsets):
                addr = offset + (i * burst_size)
                # Absolute time
                f.write(f"{current_time} (1024) read 0x{addr:X}\n")
                current_time += cycle_step

if __name__ == "__main__":
    offsets = [0, 131072, 262144, 393216]
    generate_stl_trace("interleaved.stl", 10000, 1024, offsets)
