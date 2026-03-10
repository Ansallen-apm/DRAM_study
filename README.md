# DRAMSys LPDDR4 Scheduling Analysis (FIFO vs FR-FCFS)

本專案使用 DRAMSys 模擬器分析了 **LPDDR4-6400** 記憶體在不同排程演算法 (**FIFO** vs **FR-FCFS**) 下的效能差異。重點在於探討多個 Master 在高頻寬需求與位址交錯 (Address Interleaving) 情況下的頻寬利用率 (Utilization)，以及 Buffer Size 和 Burst Size 對效能的影響。

所有模擬相關的檔案、設定與測試腳本均存放在 `sim_DRAMsys/` 目錄下。

如果您想了解如何執行模擬、測試與分析流量資料，請參閱：
👉 **[模擬操作指南 (SIM_GUIDE.md)](sim_DRAMsys/SIM_GUIDE.md)**

---

## 模擬環境設定 (Simulation Setup)

*   **DRAM 規格**: LPDDR4-6400 x64 (1 Channel, 1 Rank, 8 Banks)
    *   `tCK`: 0.3125 ns (3200 MHz Clock)
    *   `Burst Length`: 16
*   **流量模式 (Traffic Pattern)**:
    *   **Masters**: 4 個 Master
    *   **存取模式**: Sequential Read (循序讀取)
    *   **位址偏移 (Address Offset)**: 每個 Master 的起始位址相差 128KB (0, 128KB, 256KB, 384KB)。
    *   **Bank Contention**: 由於位址映射 (`BANK_BIT`: 13, 14, 15)，所有 Master 的起始位址都映射到 **Bank 0** 但不同的 Row。這創造了一個極端的 Bank Conflict 與 Row Thrashing 場景。
    *   **產生方式**: 使用 Python 腳本產生嚴格交錯 (Interleaved) 的 STL Trace 檔案，確保測試條件的一致性。

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

## AXI Trace Benchmark Results

使用腳本自動執行多組 AXI Trace 的模擬結果。這些 Trace 涵蓋了從 128B 到 512B 的不同存取大小，以及隨機 (Random) 與循序 (Sequential) 存取模式。所有測試均使用 **FR-FCFS** 排程演算法與 **1GB** (Mask: 0x3FFFFFFF) 記憶體空間。

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

### 深度分析：128B Sequential vs Random Read

從上述數據可以看出，**128B** 的存取在 Sequential 與 Random 之間存在著高達 **4倍** 的效能落差 (86.58% vs 22.47%)。

1.  **Sequential Read (高效能 - 86.58%)**:
    *   **原理 (Row Hits)**: 循序存取會不斷讀取相鄰的位址。在 Open Page Policy 下，同一個 Bank 的 Row (Page) 會保持開啟。記憶體控制器只需要發出 `Read (CAS)` 指令即可連續提取資料。
    *   **結果**: 匯流排利用率極高，僅有跨越 Row (Row Crossing) 或 Refresh 時會產生些微延遲。

2.  **Random Read (低效能 - 22.47%)**:
    *   **原理 (Row Thrashing)**: 隨機位址跳躍導致極高的 Row Miss 機率。記憶體控制器必須不斷關閉當前的 Row (`Precharge`, ~18ns) 並打開新的 Row (`Activate`, ~18ns) 才能讀取資料 (`CAS`, ~17ns)。
    *   **結果**: 大量的時間被浪費在內部陣列操作 (tRP + tRCD)，導致資料匯流排處於閒置狀態。儘管有 8 個 Banks 可以進行交錯操作 (Bank Parallelism) 來隱藏部分延遲，但由於 128B 的封包太小 (在 x64 下僅需傳輸 2.5ns)，資料傳輸時間無法有效掩蓋動輒數十奈秒的命令開銷。

### 深度分析：LPDDR4 x64 vs x32 (128B Reads)

為了進一步驗證「資料傳輸時間如何影響整體效率」，我們進行了 **x32 架構** 的測試。在 x32 架構下，最大理論頻寬減半 (25.6 GB/s)，且傳輸 128B 的資料需要 **32 beats (2 個 Bursts)**，而非 x64 的 16 beats (1 個 Burst)。

**x32 測試結果:**
| Trace Name | Bandwidth | Utilization (%) |
| :--- | :--- | :--- |
| seq_read_128B | 23.71 GB/s | **92.75%** |
| rand_read_128B | 11.15 GB/s | **43.61%** |

**分析**:
*   **Random Read 利用率翻倍 (22% -> 43%)**: 因為在 x32 介面下，128B 的資料傳輸時間拉長了一倍 (從 2.5ns 變為 5ns)。這更長的資料傳輸時間幫助記憶體控制器更好地「掩蓋」(Amortize) 了 Bank 執行 Precharge/Activate 的時間開銷 (Overhead)。因此，儘管絕對頻寬較低，但匯流排的*利用率*顯著提升了。
*   **結論**: 當系統受限於隨機存取的 Latency (Row Miss) 時，增加單次存取所佔用的匯流排時間 (透過較小的 Bus Width 或較大的 Request Payload 如 512B) 可以有效提升整體的利用率 (Utilization %)。
