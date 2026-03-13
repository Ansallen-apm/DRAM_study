# HackMD Trace 在 2CH LPDDR4 x64 的分析報告

## 1. 實驗設定

本次實驗讀取了指定的 `hackmd_trace.axi`，並在 **2 個實體 Channel (每個 x64 寬度)** 的 LPDDR4 架構下進行分析。

### 記憶體與排程設定
- **硬體規格**: LPDDR4-6400, 2 Channels x 64 bits (總寬度 x128)
- **排程策略 (Scheduler)**: FIFO
- **自定義 Address Mapping**: `RoBaCoHChCoLBy` (將 Channel 切換位元放在 1KB 邊界，亦即 Bit 10，來促進 4KB 大封包的 Interleave)。

### Trace 分析與處理
原 Trace 包含了一系列 `ARx ... 6 3F` 的讀取請求，這是標準的 **4KB** 大筆資料連續讀取 (64 beats of 64 Bytes = 4096 Bytes)。
為了能在模擬器中觸發跨 Channel 邊界的 Interleave，我們將原本每個 4KB 的請求切割成 4 個 **1KB** 的子請求。

---

## 2. DRAMSys 模擬結果

經過 DRAMSys 的 `Fifo` 排程器執行，記憶體控制器的吞吐表現如下：

| 元件 (Component) | 平均頻寬 (AVG BW) | 頻寬利用率 (urate) |
| :--- | :--- | :--- |
| **System Total** | 817.60 Gb/s (102.20 GB/s) | N/A |
| **Channel 0** | 408.80 Gb/s (51.10 GB/s) | **99.96 %** |
| **Channel 1** | 408.80 Gb/s (51.10 GB/s) | **99.96 %** |

**分析**：
這份 Trace 幾乎是完美的連續讀取 (Sequential Read)，而且跨越了我們設定的 1KB Channel 邊界。因為完全沒有資料相依性阻礙，加上硬體級的 2-Channel 完美交替發送資料 (Interleaving)，這使得 DRAM 的 AC Timing (如 Precharge、Activate) 延遲完全被資料傳輸的時間掩蓋掉。最終在最簡單的 FIFO 排程下，兩個 Channel 雙雙達到了 **99.96%** 的極限利用率。

---

## 3. Ramulator2 模擬結果

我們在 Ramulator2 設定了等效的 `FCFS` 排程器與雙通道配置，執行結果如下：

- **Memory System Cycles**: 223,999 cycles
- **Total Read Requests**: 224,000 (1KB 切成 64B cacheline 帶來的大量請求)
- **分析**：
  Ramulator2 成功排空了所有 22 萬筆讀取指令。由於是純粹且密集的循序存取，我們可以看到它幾乎是以 `1 request / cycle` 的極限吞吐量在消耗這些 Trace，與 DRAMSys 測得的接近 100% 頻寬利用率結論完全一致。
