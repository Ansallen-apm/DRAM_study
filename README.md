# DRAMSys LPDDR4 Scheduling Analysis (FIFO vs FR-FCFS)

本專案使用 DRAMSys 模擬器分析了 **LPDDR4-6400** 記憶體在不同排程演算法 (**FIFO** vs **FR-FCFS**) 下的效能差異。重點在於探討多個 Master 在高頻寬需求與位址交錯 (Address Interleaving) 情況下的頻寬利用率 (Utilization)，以及 Buffer Size 和 Burst Size 對效能的影響。

## 模擬環境設定 (Simulation Setup)

*   **DRAM 規格**: LPDDR4-6400 x64 (1 Channel, 1 Rank, 8 Banks)
    *   `tCK`: 0.3125 ns (3200 MHz Clock)
    *   `Burst Length`: 16
*   **流量模式 (Traffic Pattern)**:
    *   **Masters**: 4 個 Master
    *   **存取模式**: Sequential Read (循序讀取)
    *   **位址偏移 (Address Offset)**: 每個 Master 的起始位址相差 128KB (0, 128KB, 256KB, 384KB)。
    *   **Bank Contention**: 由於位址映射 (`BANK_BIT`: 13, 14, 15)，所有 Master 的起始位址都映射到 **Bank 0** 但不同的 Row。這創造了一個極端的 Bank Conflict 與 Row Thrashing 場景。
    *   **產生方式**: 使用 Python 腳本 (`generate_trace.py`) 產生嚴格交錯 (Interleaved) 的 STL Trace 檔案，確保測試條件的一致性。

## 實驗摘要 (Experiments Summary)

我們進行了多組實驗，變數包括：
1.  **Burst Size**: 1KB (長突發) vs 256B (短突發)。
2.  **Request Buffer Size**: 32, 64, 128, 256, 512。
3.  **Refresh Policy**: Rankwise (AllBank), PerBank, NoRefresh。

### 關鍵實驗結果 (Key Results)

#### 1. Burst Size 的影響 (1KB vs 256B)

在高 Bank Contention (多個 Master 搶同一個 Bank 的不同 Row) 的情況下，Burst Size 對 FIFO 的效能有決定性的影響。

*   **1KB Bursts**:
    *   **FIFO**: ~86% Utilization (Buffer 256)。
    *   **FR-FCFS**: ~91% Utilization。
    *   **分析**: 1KB 的資料傳輸時間 (約 64 cycles) 足夠長，能夠有效分攤 Row Activate/Precharge (tRC) 的開銷。因此即使 FIFO 發生 Row Thrashing，效能損失也相對較小。

*   **256B Bursts**:
    *   **FIFO**: **~10-15%** Utilization (Buffer 64/128)。
    *   **FR-FCFS**: **~70-80%** Utilization。
    *   **分析**: 當資料量變小 (256B 僅需 16 cycles)，Row Activate/Precharge 的時間成為主要瓶頸。FIFO 導致的頻繁 Row 切換造成災難性的效能下降。FR-FCFS 透過重排序 (Reordering) 將同一 Row 的請求分組處理，維持了高效率。

#### 2. Buffer Size 的影響

Request Buffer Size 決定了記憶體控制器的「視野」(Scheduling Window) 以及是否對 Master 產生 Backpressure。

*   **Buffer < Total Pending Requests (e.g., 64/128)**:
    *   控制器產生 Backpressure，強制 Master 依序送出請求 (Interleaved)。
    *   **FIFO**: 效能最差，完全受限於 Row Thrashing。
    *   **FR-FCFS**: 隨著 Buffer 增大 (64 -> 128)，效能顯著提升 (69% -> 82%)，因為調度器能看到更多請求並進行更佳的優化。

*   **Buffer > Total Pending Requests (e.g., 256/512)**:
    *   無 Backpressure，Master 可以一次性送出所有請求。這可能導致模擬中的請求「自然分組」(Natural Batching)。
    *   在此情況下，FIFO 的效能會異常提升 (在模擬中達到 ~50-90% 取決於 Burst Size)，因為請求以批次形式到達，減少了交錯。
    *   FR-FCFS 在此條件下達到接近理論極限的效能 (**~99%** with NoRefresh)。

#### 3. Refresh Policy 的影響 (Baseline: Buffer 256, 256B Burst)

| Metric | PerBank Refresh | No Refresh | 差異 (Refresh Overhead) |
| :--- | :--- | :--- | :--- |
| **FR-FCFS Utilization** | 90.84% | 99.16% | ~8.3% |
| **FIFO Utilization** | 45.25% | 49.71% | ~4.5% |

*   **Per-Bank Refresh** 允許在 Refresh 期間存取其他 Bank，但在本實驗中所有 Master 集中攻擊 Bank 0，因此 Per-Bank Refresh 的優勢不明顯，主要是扣除了 Refresh 佔用的時間。
*   **No Refresh** 測試顯示 FR-FCFS 在理想狀況下能達到 **99%** 的匯流排利用率，證明其排程演算法極為高效。

## 結論 (Conclusion)

1.  **FR-FCFS 優勢巨大**: 對於短突發 (Small Burst) 或隨機存取 (Random Access) 的應用，FR-FCFS 是絕對必要的。它能將 FIFO 下僅 10-15% 的效能提升至 80% 以上。
2.  **FIFO 僅適用於特定場景**: 只有在 Burst Size 非常大 (如 1KB+) 且足以掩蓋 Row Cycle Latency 時，FIFO 才具有可接受的效能。
3.  **Buffer Size 至關重要**: 加大 Request Buffer 可以顯著提升 FR-FCFS 的效能，使其有更大的機會找到 Row Hit。

## 如何執行模擬 (How to Run)

### 1. 產生 Trace
使用 `generate_trace.py` 產生交錯的流量檔案 (STL format)。
```bash
python3 generate_trace.py
```
這會產生 `configs/interleaved.stl`。你可以在腳本中修改 `burst_size` (例如 256 或 1024)。

### 2. 執行 DRAMSys
使用提供的設定檔執行模擬：

**FIFO Scheduler:**
```bash
DRAMSys/build/bin/DRAMSys configs/sim_fifo_interleaved.json
```

**FR-FCFS Scheduler:**
```bash
DRAMSys/build/bin/DRAMSys configs/sim_frfcfs_interleaved.json
```

### 3. 修改設定
*   **Buffer Size**: 修改 `.json` 檔案中的 `RequestBufferSize` (例如 64, 128, 256)。
*   **Refresh Policy**: 修改 `.json` 檔案中的 `RefreshPolicy` (例如 "PerBank", "NoRefresh")。
*   **Data Length**: 需同時修改 `generate_trace.py` 中的 `burst_size` 以及 `.json` 檔案中的 `dataLength` 以保持一致。

## AXI Trace Benchmark Results

使用 `run_all_traces.py` 腳本自動執行多組 AXI Trace 的模擬結果。這些 Trace 涵蓋了從 128B 到 512B 的不同存取大小，以及隨機 (Random) 與循序 (Sequential) 存取模式。所有測試均使用 **FR-FCFS** 排程演算法與 **1GB** (Mask: 0x3FFFFFFF) 記憶體空間。

| Trace Name                     | Bandwidth       | Utilization (%) |
| :---                           | :---            | :---            |
| rand_read_128B.trace           | 11.48  GB/s     | 22.47           |
| rand_read_256B.trace           | 18.95  GB/s     | 37.06           |
| rand_read_512B.trace           | 42.92  GB/s     | 83.97           |
| rand_write_128B.trace          | 10.45  GB/s     | 20.45           |
| rand_write_256B.trace          | 16.97  GB/s     | 33.20           |
| rand_write_512B.trace          | 35.47  GB/s     | 69.38           |
| sample.trace                   | 5.91   GB/s     | 11.55           |
| seq_read_128B.trace            | 44.26  GB/s     | 86.58           |
| seq_read_256B.trace            | 47.41  GB/s     | 92.75           |
| seq_read_512B.trace            | 48.96  GB/s     | 95.78           |
| seq_write_128B.trace           | 45.79  GB/s     | 89.59           |
| seq_write_256B.trace           | 48.28  GB/s     | 94.45           |
| seq_write_512B.trace           | 49.42  GB/s     | 96.68           |

**分析**:
*   **Sequential Access**: FR-FCFS 在循序存取下表現極佳 (86% - 96%)，因為能夠最大化 Row Hit 並有效利用 Bank Parallelism。
*   **Random Access**:
    *   在小封包 (128B) 下，由於頻繁的 Row Miss 和有限的 Row Hit 機會，頻寬利用率顯著下降至 ~22%。
    *   隨著封包大小增加 (512B)，即使是隨機存取，利用率也能提升至 ~84%，這顯示了大封包能有效攤提 Row Cycle 的開銷。

## 檔案列表
*   `run_all_traces.py`: 自動化執行 `traces/` 目錄下所有 AXI Trace 的腳本。
*   `axi_to_stl.py`: AXI 格式轉 DRAMSys STL 格式的轉換工具。
*   `generate_trace.py`: 產生 STL Trace 的 Python 腳本。
*   `configs/`: 包含模擬設定檔 (`.json`) 與 Trace 檔 (`.stl`)。
*   `result/`: 存放模擬結果 Log (`.txt`)。
*   `analysis_fifo_vs_frfcfs.txt`: 詳細的英文分析報告。
