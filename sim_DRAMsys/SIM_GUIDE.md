# 模擬操作指南 (Simulation Guide)

這份指南將告訴您如何執行 `sim_DRAMsys` 資料夾下的所有自動化測試與手動模擬。

所有的操作皆預期在 `sim_DRAMsys` 資料夾內執行。

## 如何執行模擬 (How to Run)

### 1. 執行外部 AXI Trace 自動化測試 (Benchmark)
專案內含多個由 `DRAM_bench` 擷取的 AXI 流量檔，可透過 Python 腳本自動轉換為 STL 格式並執行模擬：

**執行全部 Trace (LPDDR4-6400 x64, 1GB):**
```bash
python3 run_all_traces.py
```
這會處理 `traces/` 目錄下的所有 `.trace` 檔案，並在終端機印出所有結果的總表。

**執行 x32 介面寬度測試 (128B Seq/Rand Read):**
```bash
python3 run_x32_benchmark.py
```
這會專門測試 x32 架構下的 128B 讀取效能，並將結果輸出至 `LP4_x32_128B_read_rslt.txt`。

### 2. 執行合成流量分析 (Synthetic Traffic - Interleaved)
如果您想自訂流量並測試 FIFO vs FR-FCFS：

1. **產生 Trace**:
   修改並執行 `generate_trace.py` 產生交錯的流量檔案 `configs/interleaved.stl`。
   ```bash
   python3 generate_trace.py
   ```

2. **執行 DRAMSys**:
   使用提供的設定檔執行模擬：
   ```bash
   # FIFO Scheduler
   DRAMSys/build/bin/DRAMSys configs/sim_fifo_interleaved.json

   # FR-FCFS Scheduler
   DRAMSys/build/bin/DRAMSys configs/sim_frfcfs_interleaved.json
   ```

## 檔案列表 (File List)
*   `run_all_traces.py`: 自動化執行 `traces/` 目錄下所有 AXI Trace 的腳本 (x64)。
*   `run_x32_benchmark.py`: 專門針對 x32 介面執行 128B Trace 的腳本。
*   `axi_to_stl.py`: AXI 格式轉 DRAMSys STL 格式的轉換工具 (支援 `--mask` 位址過濾)。
*   `generate_trace.py`: 產生自訂交錯 STL Trace 的 Python 腳本。
*   `configs/`: 包含模擬設定檔 (`.json`) 與 Trace 檔 (`.stl`)。
*   `result/`: 存放模擬結果 Log (`.txt`)。
*   `analysis_seq_vs_rand_128B.txt`: 128B 循序與隨機讀取的詳細英文分析。
