def get_bank_rank_row(addr):
    ch = (addr >> 10) & 1
    rank = (addr >> 11) & 1
    bank = (addr >> 16) & 7
    row = (addr >> 19) & 0x3FFF
    return ch, rank, bank, row

bases = [0x20000, 0x40000, 0x60000, 0x80000]
for i, base in enumerate(bases):
    print(f"\nMaster {i} Base: {hex(base)}")
    for req in range(30):
        addr = base + req * 0x1000
        ch, rank, bank, row = get_bank_rank_row(addr)
        print(f"Req {req}: R{rank} B{bank} Ro{row}")
