import os

def write_yaml(filepath, scheduler):
    content = f"""Frontend:
  impl: LoadStoreTrace
  path: trace_2bank_1kb.ldst
  clock_ratio: 1

  Translation:
    impl: NoTranslation
    max_addr: 2147483648

MemorySystem:
  impl: GenericDRAM
  clock_ratio: 1

  DRAM:
    impl: LPDDR5
    org:
      preset: LPDDR5_8Gb_x16
      channel: 1
      rank: 1
    timing:
      preset: LPDDR5_6400

  Controller:
    impl: Generic
    Scheduler:
      impl: {scheduler}
    RefreshManager:
      impl: AllBank
    RowPolicy:
      impl: OpenRowPolicy
    plugins:

  AddrMapper:
    impl: RoBaCoBy
"""
    with open(filepath, 'w') as f:
        f.write(content)

write_yaml('ramulator2_fifo.yaml', 'FCFS')
write_yaml('ramulator2_frfcfs.yaml', 'FRFCFS')