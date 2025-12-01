
# configs.py
# ------------------------------------------------------------
# 系統所有參數設定（延遲 / 能量 / 頻寬 / 碼率）
# ------------------------------------------------------------
# 本檔案提供：
#   1. 所有可調整常數與模型參數
#   2. 延遲模型中會使用的各種 delay（activation、scheduling、transcoding、傳輸、傳播）
#   3. 能量消耗模型（轉碼能耗、ISL 傳輸能耗）
#   4. bitrate 相關參數（吞吐量、chunk size）
#   5. RL 可能會用到的 reward 權重
#
# 便於 core.py、satellites.py、routing.py 等模組 import。
#
# ------------------------------------------------------------

# -----------------------------
# Bitrate 版本（單位：Mbps）
# -----------------------------
BITRATES = [0.75, 1.20, 1.85, 2.85]

# 轉碼時間（單位：秒）
# 參照你的學長論文：TR = 0.19 / 0.16 / 0.13 s
TRANSCODE_TIME = {
    0.75: 0.19,
    1.20: 0.16,
    1.85: 0.13,
    2.85: 0.13,   # 若未提供 → default 用最高碼率同級
}

# 轉碼能量（單位：J）
# 來自論文：IP = 14.2 / 8.2 / 5.1 J
TRANSCODE_ENERGY = {
    0.75: 14.2,
    1.20: 8.2,
    1.85: 5.1,
    2.85: 5.1,   # 若未提供 → default 用最高碼率同級
}

# 轉碼 power（相對比例，若要）
TRANSCODE_POWER_RATIO = {
    0.75: 1.0,
    1.20: 0.82,
    1.85: 0.51,
    2.85: 0.51,
}

# -----------------------------
# ISL 與傳輸相關
# -----------------------------
ISL_BANDWIDTH = 10e9  # 10 GHz
INBOUND_MAX = 20e6     # 20 Mbps
OUTBOUND_MAX = 40e6    # 40 Mbps

# 傳輸吞吐量（bps）
# 假設 bitrate 本身就是可用吞吐（簡化處理）
BITRATE_TO_THROUGHPUT = {
    b: b * 1_000_000 for b in BITRATES
}

# 每段影片 chunk（單位：bits）
CHUNK_SIZE = 2_000_000  # 2 Mbits（可調整）

# -----------------------------
# 延遲模型
# -----------------------------
# Activation delay（秒）
ACTIVATION_DELAY = 0.01

# Scheduling delay（秒）
SCHEDULING_DELAY = 0.01

# ISL 傳播延遲（每 hop 秒）
# 假設 LEO 衛星間距 1,000 km → 1000km / 光速 ≈ 3.3 ms → 再加處理延遲取 5ms
ISL_PROPAGATION_DELAY = 0.005

# 傳輸 delay = CHUNK_SIZE / THROUGHPUT（自動計算）

# -----------------------------
# 衛星能量模型
# -----------------------------
SATELLITE_BATTERY_MAX = 5000.0  # J
BATTERY_MIN_THRESHOLD = 100.0   # 避免完全耗盡

# 每 hop 傳輸能耗
ISL_TX_ENERGY_PER_HOP = 0.5  # J

# -----------------------------
# RL reward 權重（可自行調整）
# -----------------------------
RL_REWARD_WEIGHT = {
    "delay": -1.0,     # 越小越好
    "energy": -0.02,   # 少能量消耗為佳
}

# -----------------------------
# LSTM 預測模型參數（placeholder）
# -----------------------------
LSTM_LEARNING_RATE = 0.1

# -----------------------------
# Demand 模型參數
# -----------------------------
POISSON_LAMBDA = 2.0  # 中度變動


# 在 configs.py 最後面加上這些別名映射
TRANSCODING_DELAY = TRANSCODE_TIME
TRANSCODING_ENERGY = TRANSCODE_ENERGY
ENERGY_PER_HOP = ISL_TX_ENERGY_PER_HOP
BATTERY_MIN = BATTERY_MIN_THRESHOLD

# 補上缺漏的參數
TX_DELAY_PER_HOP = { b: (CHUNK_SIZE / BITRATE_TO_THROUGHPUT[b]) for b in BITRATES } 
# 或者簡單定義一個固定值，例如 TX_DELAY_PER_HOP = { b: 0.02 for b in BITRATES }
