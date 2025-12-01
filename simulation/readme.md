
diff --git a/SIMULATION_LOGIC.md b/SIMULATION_LOGIC.md
new file mode 100644
index 0000000000000000000000000000000000000000..bcbfae95c2e2f061c5a4016cac9fb7a809fadecb
--- /dev/null
+++ b/SIMULATION_LOGIC.md
@@ -0,0 +1,32 @@
+# 模擬邏輯總覽
+
+本文說明目前版本程式在「不依賴外部雲端套件即可運作」的前提下，如何完成五個時間槽的衛星直播模擬。內容依照初始化 → 每個時間槽的處理 → 結果輸出三個階段整理，對照程式主流程與各核心模組。
+
+## 初始化階段
+1. **需求生成 (`demand.py`)**：`DemandGenerator` 先以 pandas 讀取 `.xlsx` 或 `.csv`，若環境沒有 pandas 則改用標準 `csv` 解析器，並自動補齊所有地區與碼率的缺漏值，形成 `real` 與 `pred` 的 t=1 基底資料。【F:demand.py†L17-L161】
+2. **衛星網路 (`satellites.py`)**：`SatelliteNetwork` 產生 30 顆衛星，建立 region 對應與 cluster 分組，供後續排程查詢（程式流程在 `main_sim.py` 先建構網路物件）。【F:main_sim.py†L12-L35】
+3. **學習模型**：
+   - `RLModel` 提供 `select_best`，用特徵表挑選適合的 activation 衛星，若缺少 NumPy 會改用 `np_compat` 的最小 API 仍可運行。【F:core_part2.py†L1-L37】【F:np_compat.py†L1-L54】
+   - `LSTMManager` 管理每顆衛星的預測誤差累積與校正，配合排程時更新各自的預測值。
+4. **核心模組**：`CorePart1~6` 分別處理需求解析、activation、scheduling、delay 計算、能源更新與紀錄/繪圖，並在 `main_sim.py` 中被初始化。
+
+## 每個時間槽的處理流程
+`main_sim.py` 以 `T=5` 迭代時間槽，每回合依下列步驟執行，確保論文邏輯的模擬順序一致。【F:main_sim.py†L19-L41】
+
+1. **時間進位與衛星重置**：t>1 時呼叫 `SatelliteNetwork.advance_one_timeslot()` 更新軌道，接著將所有衛星的 `busy` 與 `processing` 清空，確保當前時間槽的排程不受上一輪干擾。【F:main_sim.py†L19-L32】
+2. **逐區域處理 (region 1→30)**：
+   1. `CorePart1.process_region_stage1` 取得該區的 viewer/source 衛星、實際與預測需求，以及對應的 Walker-star 路由路徑，形成後續步驟的上下文。【F:core_part1.py†L17-L71】
+   2. `CorePart2.activation_step` 基於 stage1 的路徑，計算各候選衛星的可行度（idle 數是否足以覆蓋所需碼率）與特徵表，交由強化學習模型挑選 activation 衛星。【F:core_part2.py†L7-L37】
+   3. `CorePart3.scheduling_step` 在 activation 衛星所在 cluster 的 idle 衛星之間，逐個碼率挑選「該衛星所在地區預測需求最高」者進行轉碼，並同步更新對應衛星的 LSTM 預測，產生 `bitrate → sat_id` 的分派表。【F:core_part3.py†L29-L99】
+   4. `CorePart4.compute_region_delay` 根據分派表與路由，計算每個碼率的傳輸/轉碼延遲並加權平均成區域平均 delay；若同一 cluster 先前已有相同碼率的轉碼成果，會跳過 activation/scheduling 延遲以符合 Case 2 邏輯。【F:core_part4.py†L15-L63】
+   5. `CorePart5.update_region_energy` 以分派結果更新負責衛星的電池與頻寬，並記錄 hop 數與剩餘電量，低於門檻的衛星會被標記為忙碌以避免過度使用。【F:core_part5.py†L15-L72】
+   6. `CorePart6.log_all` 將 activation、排程與平均 delay 依時間/地區寫入對應 log 結構，為後續輸出做準備。【F:core_part6.py†L22-L55】
+
+## 結果輸出與論文圖
+迴圈結束後，`CorePart6.export_all` 會整合能源紀錄、序列化 JSON 結果，並嘗試產生 delay、activation、energy、scheduling 及 hop 分布圖表；若環境缺少 matplotlib，程式會安全地跳過繪圖步驟並提示，確保模擬不會因依賴缺失而中斷。【F:core_part6.py†L12-L105】【F:core_part6.py†L106-L152】
+
+## 可靠性與可重現性補充
+- **離線相容**：`np_compat.py` 提供 `zeros`、`dot`、`mean`、`random`、`poisson` 等最小介面，讓強化學習模型在無法安裝 NumPy 的環境仍可正常運作。【F:np_compat.py†L1-L54】
+- **輸入健全性**：需求載入時會把缺漏的地區或碼率以 0 填補，並在 CSV 模式下累計重複列的需求，避免因輸入不完整或檔案格式受限產生 KeyError 或錯誤排程。【F:demand.py†L67-L161】
+- **日誌完整性**：所有時間槽與地區的 activation、排程、delay、能源資訊都被保存在 `CorePart6` 的 log 中，可直接用於後續統計或繪圖，符合論文中需展示的性能指標。【F:core_part6.py†L22-L152】
+
