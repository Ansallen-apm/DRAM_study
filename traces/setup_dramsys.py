import json

def setup_dramsys():
    with open('sim_DRAMsys/configs/sim_fifo.json', 'r') as f:
        config = json.load(f)

    config['simulation']['simulationid'] = "hackmd_lp4_2ch_x128_fifo"
    config['simulation']['simconfig']['SimulationName'] = "hackmd_lp4_2ch_x128"

    # 2 Channels, each x64 width
    config['simulation']['memspec']['memarchitecturespec']['nbrOfChannels'] = 2
    config['simulation']['memspec']['memarchitecturespec']['width'] = 64
    config['simulation']['memspec']['memarchitecturespec']['nbrOfRanks'] = 2

    config['simulation']['mcconfig']['RefreshPolicy'] = "NoRefresh"
    config['simulation']['mcconfig']['Scheduler'] = "Fifo"

    # User's mapping translated to DRAMSys (LPDDR4 has 10 Column bits, 14 Row bits, 8 Banks)
    # The user wanted RoBaCoHChCoLBy where CH is at bit 10.
    # CoL = 4:9 (6 bits). This means BYTE_BIT = 0,1,2,3 (16 Bytes).
    # But LPDDR4 x64 is 8 Bytes per transfer.
    # If width=64 (8 Bytes), DRAMSys expects exactly 3 BYTE_BITs [0,1,2].
    # If we map BYTE_BIT=[0,1,2,3], DRAMSys might complain if width isn't 128.
    # Wait, earlier we used BYTE_BIT=[0,1,2,3] and it worked? Let's check how DRAMSys responded.
    # Actually, LPDDR4 has burst length 16 (16 * 8 = 128 Bytes).
    config['simulation']['addressmapping'] = {
        "BYTE_BIT": [0, 1, 2, 3], # 16 Bytes
        "COLUMN_BIT": [4, 5, 6, 7, 8, 9, 12, 13, 14, 15],
        "CHANNEL_BIT": [10],
        "RANK_BIT": [11],
        "BANK_BIT": [16, 17, 18],
        "ROW_BIT": [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
    }

    traces = []
    traces.append({
        "name": "hackmd_trace.stl",
        "type": "player",
        "clkMhz": 1000,
        "TraceFile": "../traces/hackmd_trace.stl",
        "dataLength": 1024
    })
    config['simulation']['tracesetup'] = traces

    with open('traces/dramsys_hackmd.json', 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == "__main__":
    setup_dramsys()