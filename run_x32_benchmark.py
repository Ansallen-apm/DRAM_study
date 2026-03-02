import os
import subprocess
import glob
import json

TRACE_DIR = "traces"
CONFIG_DIR = "configs/generated"
RESULT_DIR = "result/x32_traces"
DRAMSYS_BIN = "DRAMSys/build/bin/DRAMSys"
CONVERTER = "axi_to_stl.py"
OUTPUT_FILE = "LP4_x32_128B_read_rslt.txt"

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

def create_config(sim_name, trace_file_path):
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
                "RefreshPolicy": "PerBank",
                "PowerDownPolicy": "NoPowerDown",
                "Arbiter": "Simple"
            },
            "memspec": {
                "memoryId": "LPDDR4_6400_x32",
                "memoryType": "LPDDR4",
                "memarchitecturespec": {
                    "width": 32,
                    "nbrOfBanks": 8,
                    "nbrOfBankGroups": 1,
                    "nbrOfColumns": 1024,
                    "nbrOfRows": 32768,
                    "nbrOfRanks": 1,
                    "nbrOfDevices": 1,
                    "nbrOfChannels": 1,
                    "dataRate": 2,
                    "burstLength": 16,
                    "maxBurstLength": 16
                },
                "memtimingspec": {
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
                },
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
            "addressmapping": {
                "BANK_BIT": [ 12, 13, 14 ],
                "BYTE_BIT": [ 0, 1 ],
                "COLUMN_BIT": [ 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 ],
                "ROW_BIT": [ 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29 ]
            },
            "tracesetup": [
                {
                    "type": "player",
                    "name": trace_file_path,
                    "clkMhz": 1000,
                    "dataLength": 64
                }
            ]
        }
    }
    return config

def main():
    target_traces = ["seq_read_128B.trace", "rand_read_128B.trace"]
    results = []

    print(f"Running simulation for {len(target_traces)} traces on LPDDR4-6400 x32 (1GB)...")

    for trace_name in target_traces:
        trace_path = os.path.join(TRACE_DIR, trace_name)
        if not os.path.exists(trace_path):
            print(f"Warning: Trace {trace_name} not found, skipping.")
            continue

        base_name = trace_name
        stl_name = base_name.replace(".trace", ".stl")
        stl_path = os.path.join(CONFIG_DIR, stl_name)

        # 1. Convert (reuse existing conversion if available, or just re-run to be safe)
        print(f"Converting {base_name} to {stl_name}...")
        # Use 1GB mask (0x3FFFFFFF)
        subprocess.run(["python3", CONVERTER, trace_path, stl_path, "--mask", "0x3FFFFFFF"], check=True)

        # 2. Config
        sim_name = base_name.replace(".trace", "_x32")
        config_path = os.path.join(CONFIG_DIR, f"{sim_name}.json")

        config_data = create_config(sim_name, os.path.abspath(stl_path))

        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)

        # 3. Run
        print(f"Running simulation for {sim_name}...")
        log_file = os.path.join(RESULT_DIR, f"{sim_name}.txt")
        try:
            with open(log_file, 'w') as log:
                # Run DRAMSys
                subprocess.run([DRAMSYS_BIN, config_path], stdout=log, stderr=subprocess.STDOUT, timeout=60)
        except subprocess.TimeoutExpired:
            print(f"Simulation {sim_name} timed out.")
            with open(log_file, 'a') as log:
                log.write("\n\nTIMEOUT\n")

        # 4. Parse Result
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

        results.append({
            "Trace": base_name,
            "Bandwidth": bw,
            "Utilization": util
        })

    # Write Results to File
    with open(OUTPUT_FILE, 'w') as f:
        f.write("======================================================================\n")
        f.write(f"{'Trace Name':<30} | {'Bandwidth':<15} | {'Utilization (%)'}\n")
        f.write("-" * 70 + "\n")
        for res in results:
            f.write(f"{res['Trace']:<30} | {res['Bandwidth']:<15} | {res['Utilization']}\n")
        f.write("======================================================================\n")

    print(f"Results saved to {OUTPUT_FILE}")
    print(open(OUTPUT_FILE).read())

if __name__ == "__main__":
    main()
