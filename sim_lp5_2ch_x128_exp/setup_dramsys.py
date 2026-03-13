import json

def setup_dramsys():
    with open('../sim_DRAMsys/configs/sim_fifo.json', 'r') as f:
        config = json.load(f)

    config['simulation']['simulationid'] = "lp5_2ch_x128_fifo"
    config['simulation']['simconfig']['SimulationName'] = "lp5_2ch_x128"

    # 2 Channels, each x64 width = x128 total
    config['simulation']['memspec']['memarchitecturespec']['nbrOfChannels'] = 2
    config['simulation']['memspec']['memarchitecturespec']['width'] = 64
    config['simulation']['memspec']['memarchitecturespec']['nbrOfRanks'] = 2

    config['simulation']['mcconfig']['RefreshPolicy'] = "NoRefresh"
    config['simulation']['mcconfig']['Scheduler'] = "Fifo"

    config['simulation']['addressmapping'] = {
        "BYTE_BIT": [0, 1, 2, 3], # 16 Bytes
        "COLUMN_BIT": [4, 5, 6, 7, 8, 9, 12, 13, 14, 15], # Added bit 15 to make 10 bits total
        "CHANNEL_BIT": [10],
        "RANK_BIT": [11],
        "BANK_BIT": [16, 17, 18],
        "ROW_BIT": [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32] # 14 bits
    }

    traces = []
    for i in range(4):
        traces.append({
            "name": f"master{i}.stl",
            "type": "player",
            "clkMhz": 1000,
            "TraceFile": f"master{i}.stl"
        })
    config['simulation']['tracesetup'] = traces

    with open('dramsys_fifo.json', 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == "__main__":
    setup_dramsys()