# LPDDR4-6400 x64：2-Bank 1KB 交替存取模式分析報告

## 1. 實驗目標與設定

本次實驗主要探討當記憶體為 **LPDDR4-6400 (x64 介面)** 時，若 Master 的存取行為被嚴格限制在 **2 個 Bank 之間交替**（例如 Bank 0 與 Bank 1），且每次讀取的資料大小為 **1KB (Pure Read)**，此時的記憶體頻寬利用率 (Utilization Rate, urate) 能達到多少？排程器策略（FIFO 與 FRFCFS）對此特定情境是否有影響？

### 關鍵硬體規格 (LPDDR4 x64)
- **傳輸速率 (Data Rate)**: 6400 MT/s
- **匯流排寬度 (Bus Width)**: 64-bit (8 Bytes/beat)
- **最小突發長度 (Burst Length)**: BL16
- **單次最小交易大小 (Transaction Size)**: 8 Bytes × 16 = **128 Bytes**
- 因此，每次 **1KB** 的請求實際上在匯流排上會被拆分為 **8 次 128 Bytes** 的連續 Burst。

### 流量模式設計 (Trace Design)
- 確保所有位址完美對齊 `RoBaCoBy` (Row-Bank-Column-Byte) 映射。
- **嚴格交替**：前 1KB 存取 Bank 0，接下來的 1KB 存取 Bank 1，再換回 Bank 0...依此類推。
- **必定發生 Row Conflict**：每次切換回同一個 Bank 時（例如從 Bank 1 切換回 Bank 0），會刻意讓存取落在 Bank 0 的 **「下一個不同 Row」**。這表示每 1KB (8 個 Bursts) 結束後，下一次訪問該 Bank 時必定會遭遇 Row Miss/Conflict 帶來的 AC Timing 懲罰 (如 tRP, tRCD)。

---

## 2. 模擬結果

本次測試動用了兩套業界標準的記憶體系統模擬器進行交叉驗證：**DRAMSys 5.0** 與 **Ramulator 2.0**。

### DRAMSys 模擬結果 (執行 64 次 1KB 請求)
| 排程器 (Scheduler) | 平均頻寬 (AVG BW) | 頻寬利用率 (urate) | 執行總時間 (Total Time) |
| :--- | :--- | :--- | :--- |
| **FIFO** | 31.54 GB/s | **61.70 %** | 2078 ns |
| **FRFCFS** | 31.54 GB/s | **61.70 %** | 2078 ns |

### Ramulator 2.0 模擬結果 (等效 LPDDR5-6400, 執行 512 次 128B 存取)
| 排程器 (Scheduler) | 記憶體系統執行週期 (System Cycles) |
| :--- | :--- |
| **FCFS (FIFO)** | **2417 cycles** |
| **FRFCFS** | **2406 cycles** |

*(註：由於 Ramulator2 計算邏輯稍有不同，且支援的是 LPDDR5 協定，但從極為接近的 Cycle 數可以看出兩種排程器表現依然幾乎一致。)*

---

## 3. 分析與結論

### Q1: 在這種 2-bank 1KB 交替的模式下，urate 會是多少？
實測證明，在極端的 2-bank (1KB) 交替下，LPDDR4-6400 x64 的 **urate 大約落在 61.70% 左右**。

**無法達到 95%~99% 高利用率的原因分析**：
雖然 1KB 的存取很大（連續 8 個 128B Burst 會產生 7 次 Row Hit），能夠極大地攤提 (Amortize) 掉前面 Activate (tRCD) 的時間。但因為 **只有 2 個 Bank 進行交替 (Bank Interleave 數量太少)**，當這兩個 Bank 在交替時，控制器 (Controller) 無法找到足夠多「正在處於 Ready 狀態」的其他 Bank 來填補命令匯流排的空窗期。

詳細來說，當 Bank 0 讀完 1KB 後，下一次輪到 Bank 0 時必須先執行 Precharge (tRP) 和 Activate (tRCD)。而在這段 AC Timing 的空窗期內，系統只有 Bank 1 能夠提供資料。一旦 Bank 1 的資料也發送完畢（1KB 很快就傳完了），而 Bank 0 的 Activate 又還沒準備好時，Data Bus 就只能閒置 (Idle)。這就是為什麼 utilization rate 被死死卡在 ~61% 而無法達到 90% 以上的原因。若要藏住這些 AC Timing 懲罰，通常需要 4 個或 8 個以上的 Bank 進行 Interleave，才能利用多個 Bank 的資料傳輸時間完全覆蓋掉某個 Bank 的 tRP/tRCD。

### Q2: 效能會跟 Policy (FIFO vs FRFCFS) 有關嗎？
**結論：完全無關（或影響微乎其微）。**

- **原因**：FRFCFS (First-Ready First-Come-First-Serve) 的核心優勢在於：它可以從 Request Queue 裡面挑出那些**已經 Open（發生 Row Hit）**的請求優先執行，藉此打破原本 FIFO 的順序來提高頻寬。
- 然而，在這個特定的 Trace 中：
  1. 針對同一個 Bank 的連續 8 次 128B 請求（構成 1KB），它們本來就是在時間上**連續且緊湊**地發送的，就算不用 FRFCFS，單純的 FIFO 也會連續執行它們，自然獲得 7 次 Row Hit。
  2. 當切換到下一個 1KB 時，我們強制它落在**新的 Row**。這表示 Request Queue 裡面**根本沒有任何可以發生 Row Hit 的未來請求**可供 FRFCFS 去「優先挑選」。
- 在「所有排隊中的請求都必定造成 Row Conflict」且「同一個 1KB 的請求本來就已經擠在一起」的情況下，FRFCFS 退化成了與 FCFS (FIFO) 完全相同的行為模式。因此，這兩種 Policy 在這個實驗中的最終頻寬利用率才會一模一樣 (61.70%)。