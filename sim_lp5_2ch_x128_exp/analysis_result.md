# LPDDR5 x128 2-Channel 交替存取模式分析報告

## 1. 實驗目標與設定

本次實驗主要探討當記憶體為 **LPDDR5-6400**，採用 **2-Channel x64 (總頻寬 x128)** 架構時，4 個 Master 同時進行大範圍循序讀取 (Sequential Read) 的頻寬利用率 (Utilization Rate, urate)。

### 關鍵硬體與位址映射 (Address Mapping)
- **傳輸速率 (Data Rate)**: 6400 MT/s
- **架構**: 2 個邏輯 Channel，每個 Channel 寬度為 x64，總共 128 bit (16 Bytes/beat)。
- **排程器 (Scheduler)**: FIFO
- **自定義 Address Mapping (`RoBaCoHChCoLBy`)**:
  - `Byte`: `[0:3]` (16 Bytes 傳輸單位)
  - `Column Low`: `[4:9]` (對應 1024 Bytes = 1KB 空間)
  - `Channel`: `[10]` (設計為每跨越 1KB 邊界，請求就會切換至另一個 Channel 進行 Interleaving)
  - `Rank`: `[11]`
  - `Column High`: `[12:15]`
  - `Bank`: `[16:18]`
  - `Row`: `[19:32]`

### 流量模式設計 (Trace Design)
- **4 個 Master**：每個 Master 循序存取 30 次 **4KB** 的資料。
- 各 Master 的起始位址 (Base Address) 互相拉開 **512KB** 的距離 (`0x20000`, `0xA0000`, `0x120000`, `0x1A0000`)。
- **切分機制**：為了忠實模擬底層 AXI Interconnect 在遇到跨越 `1KB` Channel 邊界的行為，我們將原本每個 Master 發出的 1 個連續 4KB 請求，在輸入模擬器前切分成 **4 個連續的 1KB 請求**。這確保了位址遞增時，能正確且平均地觸發 Bit 10 的翻轉，實現精準的 2-Channel 交替餵單 (Interleaving)。

---

## 2. DRAMSys 模擬結果

經過 DRAMSys 5.0 模擬 (FIFO 排程)，記憶體控制器在雙通道上輸出的結果如下：

| 元件 (Component) | 平均頻寬 (AVG BW) | 頻寬利用率 (urate) |
| :--- | :--- | :--- |
| **System Total** | **779.26 Gb/s** (97.40 GB/s) | N/A |
| **Channel 0 (Controller 0)** | 389.63 Gb/s (48.70 GB/s) | **95.28 %** (最高 100%) |
| **Channel 1 (Controller 1)** | 389.63 Gb/s (48.70 GB/s) | **95.28 %** (最高 100%) |
*(註：單一 Channel 最大理論極限為 51.12 GB/s)*

**(勘誤說明)**：初次實驗中觀察到的 `71.80%` 是因為在某些配置下 4 個 Master 爭搶資源導致的 Bank 衝突。在精確對齊 Address Mapping 與 1KB Request Size 切割後，系統達到了 **95.28%** 的極高利用率。

---

## 3. 分析與結論

### 1. 2-Channel Interleaving 的強大效益
在此實驗中，我們將 Channel 選擇位元 (Bit 10) 放置在剛好 1KB 邊界的位置 (`RoBaCoHChCoLBy`)。這是一個極為優秀的硬體級打散策略。當任何一個 Master 發出 4KB 的大筆資料讀取時，這筆資料會被硬體自動切成「1KB 進 CH0 -> 1KB 進 CH1 -> 1KB 進 CH0 -> 1KB 進 CH1」。
這使得兩個 Channel 的資料匯流排可以 **近乎平行地同時吐出資料**，完全避免了單一 Channel 匯流排的擁塞，達到雙通道 **95.28%** 的超高頻寬利用率。

### 2. 循序流量 (Sequential) 的本質
因為每個 Master 都是進行連續位址 (Sequential) 的 4KB 讀取，這帶來了極高的 **Row Hit Rate (Page Hit)**。由於連續的存取大多落在同一個已開啟的 Row 內，因此可以避開絕大多數的 tRP (Precharge) 和 tRCD (Activate) 延遲懲罰。這也是為何我們只使用最簡單的 **FIFO 排程器** 就能獲得 95%+ 如此高效率的原因。在此情境下，換用 FRFCFS 排程器也不會有進一步的顯著提升，因為瓶頸已經轉移到了純粹的實體資料匯流排極限 (Data Bus Saturation)。

### 3. 多 Master 同時打的影響
儘管有 4 個 Master 同時發送請求，且它們的起始位址相隔 512KB (這通常意味著它們會打到不同的 Bank 甚至不同的 Row)，但因為每個 Master 的存取塊非常大 (4KB)，而且透過 Channel Interleaving 均勻分攤了壓力，DRAM 控制器的 Buffer 能夠很好地吸收這些請求並流水線化 (Pipelined) 處理，從而維持了兩邊 Channel 都接近滿載的優異表現。

### 總結
當 LPDDR5 x128 (雙通道) 遇到連續 4KB 大小的讀取流量時，只要 **Address Mapping 將 Channel 選擇位元放在適當的交錯點 (如 1KB 邊界)**，系統的記憶體頻寬利用率能輕易達到 **95% 以上**，且單靠 **FIFO** 排程器即可勝任。