# Bank Interleaving 與 AC Timings 靜態分析報告

## 1. 您的疑慮：Bank 衝突與 Interleave 不足？

您提到：「雖然 4KB 被切成 1KB 分散到 2CH 上，但 **bank + rank 的部分會使得 4 個 master 同時使用同 bank，導致 bank interleave 不夠**。」
為了驗證這點，我們必須將那份 Trace 的真實位址套入您指定的 `RoBaCoHChCoLBy` (CH=10, Rank=11, CoH=12:15, Bank=16:18) 映射規則中，看看這 4 個 Master 到底打中了哪些 Bank。

### 靜態位址映射解析 (Static Address Mapping Analysis)
這 4 個 Master 的 Base Address 分別相差了 `0x20000` (128KB)。
我們來看看它們的位址轉換成 `Rank (R)`, `Bank (B)`, `Row (Ro)` 的結果：

- **Master 0 (Base `0x20000`)**:
  - `0x20000` 轉換後落在 **Rank 0, Bank 2, Row 0**
  - 當讀取了 16 個 4KB 請求後 (來到 `0x30000`)，會推進到 **Rank 0, Bank 3, Row 0**
- **Master 1 (Base `0x40000`)**:
  - `0x40000` 轉換後落在 **Rank 0, Bank 4, Row 0**
  - 隨後推進到 **Rank 0, Bank 5, Row 0**
- **Master 2 (Base `0x60000`)**:
  - `0x60000` 轉換後落在 **Rank 0, Bank 6, Row 0**
  - 隨後推進到 **Rank 0, Bank 7, Row 0**
- **Master 3 (Base `0x80000`)**:
  - `0x80000` 轉換後落在 **Rank 0, Bank 0, Row 1**
  - 隨後推進到 **Rank 0, Bank 1, Row 1**

### 重大發現：完美的 Bank 交錯 (No Bank Conflicts!)
由於您刻意將 Master 的起始位址彼此拉開了 `0x20000` (128KB)，而在我們的 Mapping 中，Bank Bit 落在 `16:18` (也就是以 64KB 為邊界切換 Bank)。
因此，這 4 個 Master 在同一個時間點，**完全打在不同的 Bank 上！**
- Master 0 在用 Bank 2, 3
- Master 1 在用 Bank 4, 5
- Master 2 在用 Bank 6, 7
- Master 3 在用 Bank 0, 1

**結論 1**：您以為「4 個 Master 會同時使用同一個 Bank」的假設是錯誤的。您的 Base Address 設計加上這個 Address Mapping，巧合（或巧妙）地讓 4 個 Master 完美地把 LPDDR4 的 8 個 Bank 徹底均勻地分攤滿了 (8-Bank Interleaving)。這就是為什麼 DRAMSys 可以輕鬆跑到 **99.96%** 的真正原因。

---

## 2. 靜態分析：如果「真的」只有 2 個 Bank 在 Interleave，理論 urate 是多少？

為了回答您的第二個問題：「如果同時間真的只有 2 個 Bank 在 Interleave，而且 Access Size 是 1KB，理論上的 urate 能達到多少？」
我們用 LPDDR4-6400 x64 的實體參數來計算 AC Timing 開銷。

### 系統參數
- **Data Rate**: 6400 MT/s (每個 Clock 傳輸 2 次)
- **核心頻率 (Clock Frequency)**: 3200 MHz (tCK = 0.3125 ns)
- **匯流排寬度**: 64 bits = 8 Bytes
- **一次 Burst (BL16)**: 傳輸 16 * 8 = 128 Bytes，耗時 **8 個 Clock Cycles (tBURST)**。
- **1KB 的傳輸時間 (Data Time)**: 1024 Bytes 需要 8 次 Burst，因此佔用 **64 個 Clock Cycles**。

### LPDDR4 AC Timings 開銷
假設這是一次會引發 Row Miss/Conflict 的存取，標準開銷大約是：
- **tRP (Precharge)**: ~58 cycles
- **tRCD (Activate)**: ~58 cycles
- 總空窗期 (Row Cycle Overhead) 約為 **116 cycles**。

### 雙 Bank 交替的情境模型 (2-Bank Interleave Ping-Pong)
假設我們只有 Bank A 和 Bank B。
1. Bank A 正在匯流排上傳輸 1KB 的資料 (耗時 **64 cycles**)。
2. 同時間，Bank B 正在背景執行 Precharge + Activate 來準備下一個 1KB。這需要 **116 cycles**。

你可以看到問題了：**Bank A 傳輸資料的速度 (64 cycles) 太快，無法完全掩蓋 Bank B 準備資料的時間 (116 cycles)**！

當 Bank A 傳完 1KB 退場時，Bank B 的 AC Timing 還沒走完，還要再等 `116 - 64 = 52 cycles` 才能開始吐資料。
在這 52 cycles 的等待期間，Data Bus 是完全閒置 (Idle) 的。

### 理論頻寬利用率 (Theoretical urate) 計算
- **有效傳輸時間**: 64 cycles
- **總週期時間 (包含等待)**: 64 (傳輸) + 52 (閒置等待) = 116 cycles
- **理論 Maximum Urate** = `64 / 116` = **55.17 %**

*(註：如果在 DRAMSys 中搭配極大的 Request Queue 和 FRFCFS，它可以稍微提前送出 ACT/PRE 指令，甚至讓部分 Request 形成 Row Hit 來降低攤提，urate 會微幅上升至 60%~65% 左右，但這就是純 2-Bank 遇到嚴格 Conflict 時的物理天花板。)*

---

## 3. 總結

1. **為什麼這個 HackMD Trace 跑出了 99.96%？**
   因為這個 Trace 設定的 Address Mapping 與 4 個 Master 起始位址，剛好讓流量 **完美散佈在 8 個不同的 Bank 上**，形成了完美的 8-Bank + 2-Channel Interleaving，完全沒有發生您擔心的「4 Master 擠在同一個 Bank」的瓶頸。

2. **如果真的強制只有 2 個 Bank 交替打 1KB (每次 Conflict) 會怎樣？**
   經過靜態 AC Timing 分析，因為 1KB 傳輸太快 (64 cycles)，蓋不住 tRP+tRCD (116 cycles)，Data bus 會有大量 Idle，理論的 utilization rate 只能達到 **約 55% ~ 65%** 之間。