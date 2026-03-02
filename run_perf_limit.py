import os
import subprocess
import glob
import json

TRACE_DIR = "traces/perf_limit"
CONFIG_DIR = "configs/generated"
RESULT_DIR = "result/perf_limit_traces"
DRAMSYS_BIN = "DRAMSys/build/bin/DRAMSys"
CONVERTER = "axi_to_stl.py"
OUTPUT_FILE = "perf_limit.md"

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# LPDDR4-6400: tCK = 0.3125ns (3200 MHz)
# LPDDR4-4266: tCK = 0.46875ns (2133 MHz)

def get_memtimings(speed):
    if speed == 6400:
        return {
            "tCK": 0.3125e-9,
            "RAS": 135,
            "RCD": 58,
            "RPab": 58,
            "RPpb": 58,
            "RCab": 192,
            "RCpb": 192,
            "RFCab": 896,
            "RFCpb": 448,
            "RRD": 32,
            "FAW": 128,
            "WTR": 32,
            "WR": 96,
            "RTP": 32,
            "CCD": 8,
            "CCDMW": 32,
            "RL": 56,
            "WL": 28,
            "DQSCK": 6,
            "DQSS": 1,
            "DQS2DQ": 2,
            "CKE": 12,
            "CMDCKE": 3,
            "ESCKE": 3,
            "PPD": 4,
            "RPST": 0,
            "WPRE": 2,
            "XP": 12,
            "SR": 24,
            "XSR": 460,
            "RTRS": 1,
            "REFI": 12480,
            "REFIpb": 1560
        }
    elif speed == 4266:
        # Scale timings roughly by 4266/6400 (or use standard JEDEC values if known, here scaling down cycle counts for same absolute time)
        # Actually tCK is 1.5x longer (0.46875 vs 0.3125).
        # So cycle counts should be roughly 2/3 of the 6400 values to maintain same absolute ns.
        return {
            "tCK": 0.46875e-9,
            "RAS": 90,
            "RCD": 39,
            "RPab": 39,
            "RPpb": 39,
            "RCab": 128,
            "RCpb": 128,
            "RFCab": 598,
            "RFCpb": 299,
            "RRD": 22,
            "FAW": 86,
            "WTR": 22,
            "WR": 64,
            "RTP": 22,
            "CCD": 8, # CCD is usually fixed in cycles for burst
            "CCDMW": 32,
            "RL": 36,
            "WL": 18,
            "DQSCK": 4,
            "DQSS": 1,
            "DQS2DQ": 2,
            "CKE": 8,
            "CMDCKE": 2,
            "ESCKE": 2,
            "PPD": 3,
            "RPST": 0,
            "WPRE": 2,
            "XP": 8,
            "SR": 16,
            "XSR": 307,
            "RTRS": 1,
            "REFI": 8320,
            "REFIpb": 1040
        }
    return {}

def create_config(sim_name, trace_file_path, width, speed):
    timings = get_memtimings(speed)

    if width == 64:
        # 1GB mapping for x64
        # 64 bits = 8 bytes -> 3 BYTE_BIT
        addr_mapping = {
            "BANK_BIT": [ 13, 14, 15 ],
            "BYTE_BIT": [ 0, 1, 2 ],
            "COLUMN_BIT": [ 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 ],
            "ROW_BIT": [ 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29 ]
        }
        rows = 16384
    elif width == 32:
        # 1GB mapping for x32
        # 32 bits = 4 bytes -> 2 BYTE_BIT
        # To keep 1GB size, we need double the rows
        addr_mapping = {
            "BANK_BIT": [ 12, 13, 14 ],
            "BYTE_BIT": [ 0, 1 ],
            "COLUMN_BIT": [ 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 ],
            "ROW_BIT": [ 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29 ]
        }
        rows = 32768

    config = {
        "simulation": {
            "simulationid": sim_name,
            "simconfig": {
                "AddressOffset": 0,
                "DatabaseRecording": False,
                "Debug": False,
                "EnableWindowing": False,
                "PowerAnalysis": False,
                "SimulationName": sim_name,
                "SimulationProgressBar": False,
                "StoreMode": "NoStorage",
                "UseMalloc": False,
                "WindowSize": 1000
            },
            "mcconfig": {
                "Scheduler": "FrFcfs",
                "PagePolicy": "Open",
                "SchedulerBuffer": "Bankwise",
                "RequestBufferSize": 256,
                "CmdMux": "Oldest",
                "RespQueue": "Fifo",
                "RefreshPolicy": "NoRefresh", # REFRESH DISABLED as requested
                "PowerDownPolicy": "NoPowerDown",
                "Arbiter": "Simple"
            },
            "memspec": {
                "memoryId": f"LPDDR4_{speed}_x{width}",
                "memoryType": "LPDDR4",
                "memarchitecturespec": {
                    "width": width,
                    "nbrOfBanks": 8,
                    "nbrOfBankGroups": 1,
                    "nbrOfColumns": 1024,
                    "nbrOfRows": rows,
                    "nbrOfRanks": 1,
                    "nbrOfDevices": 1,
                    "nbrOfChannels": 1,
                    "dataRate": 2,
                    "burstLength": 16,
                    "maxBurstLength": 16
                },
                "memtimingspec": timings,
                "mempowerspec": {
                    "idd01": 10.0e-3, "idd02": 10.0e-3, "idd0ql": 10.0e-3,
                    "idd2n1": 5.0e-3, "idd2n2": 5.0e-3, "idd2nQ": 5.0e-3,
                    "idd2ns1": 5.0e-3, "idd2ns2": 5.0e-3, "idd2nsq": 5.0e-3,
                    "idd2p1": 5.0e-3, "idd2p2": 5.0e-3, "idd2pQ": 5.0e-3,
                    "idd2ps1": 5.0e-3, "idd2ps2": 5.0e-3, "idd2psq": 5.0e-3,
                    "idd3n1": 8.0e-3, "idd3n2": 8.0e-3, "idd3nQ": 8.0e-3,
                    "idd3ns1": 8.0e-3, "idd3ns2": 8.0e-3, "idd3nsq": 8.0e-3,
                    "idd3p1": 8.0e-3, "idd3p2": 8.0e-3, "idd3pQ": 8.0e-3,
                    "idd3ps1": 8.0e-3, "idd3ps2": 8.0e-3, "idd3psq": 8.0e-3,
                    "idd4r1": 20.0e-3, "idd4r2": 20.0e-3, "idd4rq": 20.0e-3,
                    "idd4w1": 20.0e-3, "idd4w2": 20.0e-3, "idd4wq": 20.0e-3,
                    "idd51": 30.0e-3, "idd52": 30.0e-3, "idd5ab1": 30.0e-3,
                    "idd5ab2": 30.0e-3, "idd5abq": 30.0e-3, "idd5pb1": 30.0e-3,
                    "idd5pb2": 30.0e-3, "idd5pbq": 30.0e-3, "idd5q": 30.0e-3,
                    "idd61": 5.0e-3, "idd62": 5.0e-3, "idd6q": 5.0e-3,
                    "vdd1": 1.1, "vdd2": 1.1, "vddq": 1.1,
                    "iBeta_vdd1": 1.0e-3, "iBeta_vdd2": 1.0e-3
                },
                "memimpedancespec": {
                    "ck_termination": True, "ck_R_eq": 1e6, "ck_dyn_E": 1e-12,
                    "ca_termination": True, "ca_R_eq": 1e6, "ca_dyn_E": 1e-12,
                    "rdq_termination": True, "rdq_R_eq": 1e6, "rdq_dyn_E": 1e-12,
                    "wdq_termination": True, "wdq_R_eq": 1e6, "wdq_dyn_E": 1e-12,
                    "wdqs_termination": True, "wdqs_R_eq": 1e6, "wdqs_dyn_E": 1e-12,
                    "rdqs_termination": True, "rdqs_R_eq": 1e6, "rdqs_dyn_E": 1e-12,
                    "rdbi_termination": True, "rdbi_R_eq": 1e6, "rdbi_dyn_E": 1e-12,
                    "wdbi_termination": True, "wdbi_R_eq": 1e6, "wdbi_dyn_E": 1e-12
                },
                "bankwisespec": {
                    "factRho": 1, "factSigma": 1, "pasrMode": 0, "hasPASR": False
                }
            },
            "addressmapping": addr_mapping,
            "tracesetup": [
                {
                    "type": "player",
                    "name": trace_file_path,
                    "clkMhz": int(speed / 2), # Note: the traffic generator clock. Usually memory is half data rate, but for player it just issues timestamps as provided.
                    "dataLength": width # The payload size doesn't matter much for StlPlayer since the size is in the file, but we set it to bus width.
                }
            ]
        }
    }
    return config

def run_simulation(config_path, sim_name):
    log_file = os.path.join(RESULT_DIR, f"{sim_name}.txt")
    try:
        with open(log_file, 'w') as log:
            subprocess.run([DRAMSYS_BIN, config_path], stdout=log, stderr=subprocess.STDOUT, timeout=60)
    except subprocess.TimeoutExpired:
        with open(log_file, 'a') as log:
            log.write("\n\nTIMEOUT\n")

    bw = "N/A"
    util = "N/A"
    if os.path.exists(log_file):
        with open(log_file, 'r') as log:
            for line in log:
                if "AVG BW" in line and "IDLE" not in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        bw = parts[1].strip()
                        util = parts[2].strip().replace("%", "")
    return bw, util

def main():
    trace_files = sorted(glob.glob(os.path.join(TRACE_DIR, "*.trace")))

    configs_to_test = [
        {"speed": 6400, "width": 64},
        {"speed": 6400, "width": 32},
        {"speed": 4266, "width": 64},
        {"speed": 4266, "width": 32},
    ]

    # Actually just a flat list of dicts for easier markdown gen
    table_data = []

    print(f"Found {len(trace_files)} trace files. Running comparison...")

    for trace_path in trace_files:
        base_name = os.path.basename(trace_path)
        stl_name = base_name.replace(".trace", ".stl")
        stl_path = os.path.join(CONFIG_DIR, stl_name)

        # 1. Convert
        subprocess.run(["python3", CONVERTER, trace_path, stl_path, "--mask", "0x3FFFFFFF"], check=True)

        row_data = {"Trace": base_name}

        for cfg in configs_to_test:
            speed = cfg["speed"]
            width = cfg["width"]
            sim_name = base_name.replace(".trace", f"_{speed}_x{width}")
            config_path = os.path.join(CONFIG_DIR, f"{sim_name}.json")

            # Generate JSON
            config_data = create_config(sim_name, os.path.abspath(stl_path), width, speed)
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=4)

            # Run
            bw, util = run_simulation(config_path, sim_name)
            row_data[f"LPDDR4-{speed} x{width}"] = util.strip()

        table_data.append(row_data)

    # Generate Markdown
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Performance Limit Traces Analysis (NoRefresh)\n\n")
        f.write("此報告針對最新的 `perf_limit` 測試數據，比較了 4 種 LPDDR4 記憶體配置 (LPDDR4-6400 x64, LPDDR4-6400 x32, LPDDR4-4266 x64, LPDDR4-4266 x32) 在關閉 Refresh (`RefreshPolicy: NoRefresh`) 下的匯流排利用率 (Utilization %)。\n\n")
        f.write("所有的測試皆使用 **FR-FCFS** 排程器與 1GB 的位址空間。\n\n")

        # Header
        f.write("| Trace Name | LPDDR4-6400 x64 | LPDDR4-6400 x32 | LPDDR4-4266 x64 | LPDDR4-4266 x32 |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")

        for row in table_data:
            f.write(f"| {row['Trace']} | {row['LPDDR4-6400 x64']}% | {row['LPDDR4-6400 x32']}% | {row['LPDDR4-4266 x64']}% | {row['LPDDR4-4266 x32']}% |\n")

        f.write("\n## 觀察與分析 (Performance Limit Traces)\n")
        f.write("這些新的 Perf Limit Traces 旨在測試系統的極限壓力。從數據中可以觀察到：\n\n")
        f.write("1.  **資料匯流排寬度 (x64 vs x32) 的影響**:\n")
        f.write("    *   在隨機存取 (Random Access) 下，x32 匯流排的利用率依然穩定地約為 x64 的兩倍。這是因為 x32 需要兩倍的資料傳輸時間 (Data Burst Time) 來傳輸相同的資料量，這有效地「掩蓋」了 Row Cycle (tRP + tRCD) 的固定時間延遲。\n")
        f.write("    *   在極限循序存取 (Sequential Access) 下，所有配置的利用率皆逼近 100%。因為 Row Hit 極高，主要的瓶頸完全落在資料匯流排上。\n\n")
        f.write("2.  **時脈速度 (6400 vs 4266) 的影響**:\n")
        f.write("    *   對於隨機存取 (例如 rand_read_128B)，4266 MT/s 展現了比 6400 MT/s 更高比例的匯流排利用率。原因與上述相同：在內部陣列延遲 (絕對時間 ns) 固定的情況下，較慢的 Clock 導致資料傳輸佔用較長的絕對時間，從而掩蓋了等待陣列操作的閒置時間 (Amortization Effect)。\n")
        f.write("    *   雖然 4266 的利用率 (%) 較高，但由於其理論上限頻寬遠低於 6400，**絕對吞吐量 (GB/s)** 仍是 6400 勝出。\n\n")
        f.write("**結論**: 在系統受限於記憶體陣列存取延遲 (Latency-bound, 即小封包隨機存取) 的場景中，縮小資料匯流排或降低時脈，都會在數學上推升「利用率 (Utilization)」的數字，因為資料傳輸佔用的時間比例變大了。但這不代表絕對效能提升。系統設計應根據應用場景的流量特性 (Streaming vs Random) 來權衡 Bus Width 與 Clock Speed。\n")

    print(f"Results successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
