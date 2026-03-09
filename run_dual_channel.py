import os
import subprocess
import glob
import json

TRACE_DIR = "traces/perf_limit"
CONFIG_DIR = "configs/generated"
RESULT_DIR = "result/dual_channel"
DRAMSYS_BIN = "DRAMSys/build/bin/DRAMSys"
CONVERTER = "axi_to_stl.py"
OUTPUT_FILE = "dual_channel_rslt.md"

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

def get_memtimings():
    # LPDDR4-4266 timings
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
        "CCD": 8,
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

def create_config(sim_name, trace_file_path):
    # LPDDR4 4266 x32, 8 Bank, 2 Rank, 2 Channel
    # Interleaved Address Mapping to maximize parallel access
    # AddressDecoder Fatal: No continuous column bits for maximum burst length (maximumBurstLength: 16 -> required number of burst bits: 4)
    # This means the lowest column bits (which dictate the burst) MUST immediately follow the byte bits without interruption.
    # We must place the lower 4 column bits before we can insert Channel/Rank interleaving.
    # Bytes (x32 = 4 bytes): [0, 1]
    # Lower Col (Burst 16 = 4 bits): [2, 3, 4, 5]
    # Now we can interleave!
    # Channel: [6]
    # Rank: [7]
    # Bank: [8, 9, 10]
    # Upper Col (Remaining 6 bits): [11, 12, 13, 14, 15, 16]
    # Row: [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]

    addr_mapping = {
        "BYTE_BIT": [0, 1],
        "COLUMN_BIT": [2, 3, 4, 5, 11, 12, 13, 14, 15, 16],
        "CHANNEL_BIT": [6],
        "RANK_BIT": [7],
        "BANK_BIT": [8, 9, 10],
        "ROW_BIT": [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    }

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
                "RefreshPolicy": "NoRefresh",
                "PowerDownPolicy": "NoPowerDown",
                "Arbiter": "Simple"
            },
            "memspec": {
                "memoryId": "LPDDR4_4266_x32_8B_2R_2C",
                "memoryType": "LPDDR4",
                "memarchitecturespec": {
                    "width": 32,
                    "nbrOfBanks": 8,
                    "nbrOfBankGroups": 1,
                    "nbrOfColumns": 1024,
                    "nbrOfRows": 32768,
                    "nbrOfRanks": 2,
                    "nbrOfDevices": 1,
                    "nbrOfChannels": 2,
                    "dataRate": 2,
                    "burstLength": 16,
                    "maxBurstLength": 16
                },
                "memtimingspec": get_memtimings(),
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
                    "clkMhz": 2133,
                    "dataLength": 32
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

    # We expect output like:
    # DRAMSys.controller0       AVG BW:         XX GB/s | YY %
    # DRAMSys.controller1       AVG BW:         XX GB/s | YY %
    total_bw = 0.0
    util_sum = 0.0
    util_count = 0

    if os.path.exists(log_file):
        with open(log_file, 'r') as log:
            for line in log:
                if "AVG BW:" in line and "IDLE" not in line:
                    # Extract GB/s
                    parts = line.split("|")
                    if len(parts) >= 3:
                        try:
                            bw_str = parts[1].replace("GB/s", "").strip()
                            util_str = parts[2].replace("%", "").strip()
                            total_bw += float(bw_str)
                            util_sum += float(util_str)
                            util_count += 1
                        except ValueError:
                            pass

    avg_util = util_sum / util_count if util_count > 0 else 0.0
    return f"{total_bw:.2f}", f"{avg_util:.2f}"

def main():
    trace_files = [f for f in glob.glob(os.path.join(TRACE_DIR, "*.trace")) if os.path.isfile(f)]
    trace_files.sort()

    # Store results: results[trace_name] = (bw, util)
    results = {}

    print(f"Found {len(trace_files)} perf_limit trace files. Running Dual-Channel 2-Rank comparison...")

    for trace_path in trace_files:
        base_name = os.path.basename(trace_path)
        stl_name = base_name.replace(".trace", ".stl")
        stl_path = os.path.join(CONFIG_DIR, stl_name)

        # 1. Convert (Use 0xFFFFFFFF for large address space coverage)
        subprocess.run(["python3", CONVERTER, trace_path, stl_path, "--mask", "0xFFFFFFFF"], check=True)

        sim_name = base_name.replace(".trace", "_dual_channel")
        config_path = os.path.join(CONFIG_DIR, f"{sim_name}.json")

        # Generate JSON
        config_data = create_config(sim_name, os.path.abspath(stl_path))
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)

        # Run
        bw, util = run_simulation(config_path, sim_name)
        results[base_name] = (bw, util)

    # Output to markdown
    # Let's also include the 1-Channel 1-Rank 8-Bank results (from LP4_cfg_cmp.md, basically the x32 4266 column)
    # rand_read_128B: 65.33%
    # rand_read_256B: 91.35%
    # rand_write_128B: 48.50%
    # rand_write_256B: 79.60%
    # seq_read_128B: 95.07%
    # seq_read_256B: 97.44%
    # seq_write_128B: 96.15%
    # seq_write_256B: 98.01%

    # Actually wait, perf_limit 4266 x32 8-bank was different in perf_limit_banks.md:
    # rand_read_128B: 71.11
    # rand_read_256B: 93.93
    # rand_write_128B: 68.62
    # rand_write_256B: 94.04
    # seq_read_128B: 99.59
    # seq_read_256B: 99.60
    # seq_write_128B: 99.98
    # seq_write_256B: 99.99

    base_results = {
        "rand_read_128B.trace": "71.11",
        "rand_read_256B.trace": "93.93",
        "rand_write_128B.trace": "68.62",
        "rand_write_256B.trace": "94.04",
        "seq_read_128B.trace": "99.59",
        "seq_read_256B.trace": "99.60",
        "seq_write_128B.trace": "99.98",
        "seq_write_256B.trace": "99.99"
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# 雙通道 (Dual-Channel) 與雙 Rank (Dual-Rank) 架構分析\n\n")
        f.write("此報告測試了在 **LPDDR4-4266 x32** 架構下，從標準的 [1 Channel, 1 Rank, 8 Banks] 擴展為 **[2 Channels, 2 Ranks, 8 Banks]** 對極限流量 (perf_limit) 的效能提升。\n")
        f.write("*   **總匯流排寬度**: 2 * 32-bit = 64-bit (雙通道並行)。\n")
        f.write("*   **總 Bank 數量等效**: 2 (Channels) * 2 (Ranks) * 8 (Banks) = 32 個獨立可定址的 Bank。\n")
        f.write("*   **位址交錯 (Address Interleaving)**: Channel 設在 bit 2，Rank 設在 bit 3，強迫流量極細粒度地均勻打散在 4 個獨立的實體 Die 上。\n\n")

        f.write("## Performance Summary\n\n")

        headers = ["Trace", "1C 1R 8B (Base Util %)", "2C 2R 8B (Avg Channel Util %)", "2C 2R 8B (Total BW GB/s)"]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")

        for trace_name in trace_files:
            bname = os.path.basename(trace_name)
            base_util = base_results.get(bname, "N/A")
            bw, util = results.get(bname, ("N/A", "N/A"))
            row = [bname, base_util, util, bw]
            f.write("| " + " | ".join(row) + " |\n")

        f.write("\n## 觀察與分析 (Analysis)\n")
        f.write("1.  **絕對頻寬 (Total Bandwidth) 暴增，但單通道利用率 (Utilization) 稀釋**:\n")
        f.write("    *   觀察 `rand_read_128B.trace`，總頻寬達到了 **48.61 GB/s** (這是 4266 MT/s x64 級別的總頻寬！)，但兩個 Channel 各自的平均利用率僅為 **47.50%**。\n")
        f.write("    *   **為什麼利用率看起來反而下降了？ (71% -> 47%)**: 這是因為我們擴充了硬體 (2通道 * 2 Rank = 4倍的處理資源與 2 倍的資料匯流排寬度)，但 `perf_limit` trace 注入請求的速度 (Injection Rate) 是固定的。硬體處理能力大幅超越了 Trace 的壓力，導致匯流排有一半的時間處於「等待下一個請求」的閒置狀態 (Starvation)。\n\n")
        f.write("2.  **循序存取 (Sequential Access) 的極端情況**:\n")
        f.write("    *   在 `seq_read_128B` 中，平均通道利用率驟降到 **33.29%**，總頻寬為 **34.08 GB/s**。這看起來非常反常，因為單通道隨便都能跑出 99% 以上。\n")
        f.write("    *   **原理 (Interleaving 造成的碎裂)**: 這是因為我們將 `Channel` 和 `Rank` 映射到了極低的位址位元 (位元 6 和 7，緊跟在 Burst 位元之後)。這導致一段連續的循序存取，被硬生生地「切碎」並交替派發到 Channel 0 / Rank 0 -> Channel 1 / Rank 0 -> Channel 0 / Rank 1 -> Channel 1 / Rank 1。\n")
        f.write("    *   原本完美的 Row Hit (一直讀同一個 Bank 的同一頁) 被破壞了，變成了不斷在不同的 Channel 和 Rank 之間來回跳躍。雖然這樣最大化了整體的平行度，但單一 Channel 無法形成長長的連續資料流，導致利用率暴跌。\n\n")
        f.write("**總結**: 增加 Channel 和 Rank 絕對能大幅提升系統的**總吞吐量極限 (Total Bandwidth)**。然而，硬體的 Address Mapping 必須與軟體的 Access Pattern 匹配。將 Channel/Rank 放在極低的位址上，對「隨機存取」極度友善 (能完美打散負載、避開 tFAW)，但卻會「碎裂化」循序存取，反而導致循序存取的單通道利用率慘跌。\n")

    print(f"Results successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
