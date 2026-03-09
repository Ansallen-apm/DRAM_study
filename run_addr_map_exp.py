import os
import subprocess
import glob
import json

TRACE_DIR = "traces/perf_limit"
CONFIG_DIR = "configs/generated"
RESULT_DIR = "result/addr_map_exp"
DRAMSYS_BIN = "DRAMSys/build/bin/DRAMSys"
CONVERTER = "axi_to_stl.py"
OUTPUT_FILE = "addr_map_exp.log"

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
    # Requested Address Mapping:
    # BYTE_BIT: [0, 1]
    # COLUMN_BIT: [2, 3, 4, 5, 6, 7, 8, 9, 12, 13] (Total 10 bits for 1024 cols)
    # CHANNEL_BIT: [10]
    # RANK_BIT: [11]
    # BANK_BIT: [14, 15, 16]
    # ROW_BIT: [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]

    addr_mapping = {
        "BYTE_BIT": [0, 1],
        "COLUMN_BIT": [2, 3, 4, 5, 6, 7, 8, 9, 12, 13],
        "CHANNEL_BIT": [10],
        "RANK_BIT": [11],
        "BANK_BIT": [14, 15, 16],
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
                "memoryId": "LPDDR4_4266_x32_8B_2R_2C_Exp",
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
            subprocess.run([DRAMSYS_BIN, config_path], stdout=log, stderr=subprocess.STDOUT, timeout=120)
    except subprocess.TimeoutExpired:
        with open(log_file, 'a') as log:
            log.write("\n\nTIMEOUT\n")

    total_bw = 0.0
    util_sum = 0.0
    util_count = 0

    if os.path.exists(log_file):
        with open(log_file, 'r') as log:
            for line in log:
                # Only match "DRAMSys.controllerX       AVG BW:" (ignore .raX or system total if any)
                if "AVG BW:" in line and "IDLE" not in line and "ra" not in line:
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

    results = []

    print(f"Found {len(trace_files)} perf_limit trace files. Running modified Address Mapping experiment...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"{'Trace Name':<30} | {'Total Bandwidth (GB/s)':<25} | {'Avg Channel Utilization (%)':<30}\n")
        f.write("-" * 90 + "\n")

        for trace_path in trace_files:
            base_name = os.path.basename(trace_path)
            stl_name = base_name.replace(".trace", ".stl")
            stl_path = os.path.join(CONFIG_DIR, stl_name)

            print(f"Processing {base_name}...")
            # Convert
            subprocess.run(["python3", CONVERTER, trace_path, stl_path, "--mask", "0xFFFFFFFF"], check=True)

            sim_name = base_name.replace(".trace", "_addr_exp")
            config_path = os.path.join(CONFIG_DIR, f"{sim_name}.json")

            # Generate JSON
            config_data = create_config(sim_name, os.path.abspath(stl_path))
            with open(config_path, 'w') as json_f:
                json.dump(config_data, json_f, indent=4)

            # Run
            bw, util = run_simulation(config_path, sim_name)

            # Write to log immediately
            f.write(f"{base_name:<30} | {bw:<25} | {util:<30}\n")
            f.flush()
            print(f"Finished {base_name}: BW={bw} GB/s, Util={util}%")

    print(f"Results successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
