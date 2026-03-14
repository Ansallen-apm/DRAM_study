def analyze():
    # CoL[4:9] -> 6 bits
    # CH[10] -> 1 bit
    # Rank[11] -> 1 bit
    # CoH[12:15] -> 4 bits
    # Bank[16:18] -> 3 bits
    # Row[19:32] -> 14 bits

    def get_bank_rank_row(addr):
        ch = (addr >> 10) & 1
        rank = (addr >> 11) & 1
        bank = (addr >> 16) & 7
        row = (addr >> 19) & 0x3FFF
        return ch, rank, bank, row

    bases = [0x20000, 0x40000, 0x60000, 0x80000]
    for i, base in enumerate(bases):
        print(f"Master {i} Base: {hex(base)}")
        for req in range(2): # Just look at first 2 requests (4KB apart)
            addr = base + req * 0x1000
            print(f"  Req {req} Addr {hex(addr)} -> ", end="")
            for chunk in range(4): # 4 chunks of 1KB
                chunk_addr = addr + chunk * 1024
                ch, rank, bank, row = get_bank_rank_row(chunk_addr)
                print(f"[C{chunk}: CH{ch} R{rank} B{bank} Ro{row}] ", end="")
            print()

analyze()
