import os

def write_yaml(filepath, scheduler):
    content = f"""Frontend:
  impl: LoadStoreTrace
  path: hackmd_trace.ldst
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
      channel: 2
      rank: 2
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
    impl: RoBaRaCoCh
"""
    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    write_yaml('ramulator2_hackmd.yaml', 'FCFS')