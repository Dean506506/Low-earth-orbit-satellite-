# demand.py
# ------------------------------------------------------------
# 地區需求模型（Real + Predicted + Poisson 動態）
# ------------------------------------------------------------
# 修改說明：
#   1. 整合 Pandas 讀取 Excel/CSV 功能。
#   2. 自動將 k1~k4 對應到 BITRATES。
#   3. t=1 讀檔，t=2~T 維持 Poisson 動態模擬。
# ------------------------------------------------------------

import random
import pandas as pd
import numpy as np
from typing import Dict, List
from configs import BITRATES, POISSON_LAMBDA

class DemandGenerator:
    """產生 Real 與 Predicted 需求。

    real[t][r][b] = 人數
    pred[t][r][b] = 人數
    """

    def __init__(self, regions: List[int], real_file_path: str,
                 pred_file_path: str, T: int = 5):
        """
        Args:
            regions: 地區編號列表 (e.g., 1~30)
            real_file_path: 真實分佈的檔案路徑 (.csv 或 .xlsx)
            pred_file_path: 預測分佈的檔案路徑 (.csv 或 .xlsx)
            T: 模擬總時間槽長度
        """
        self.regions = regions
        self.T = T

        # 讀取檔案並建立 t=1 的 base data
        self.base_real = self._load_data(real_file_path)
        self.base_pred = self._load_data(pred_file_path)

        self.real = {}
        self.pred = {}

    def _load_data(self, file_path: str) -> Dict[int, Dict[float, int]]:
        """讀取檔案並解析為 [region][bitrate] = count 格式 (僅篩選 t=1)"""
        data = {}
        
        try:
            # 根據副檔名判斷讀取方式
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                # 假設是 xlsx
                df = pd.read_excel(file_path)
        except FileNotFoundError:
            print(f"Error: 找不到檔案 {file_path}")
            return {}
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return {}

        # 確保欄位名稱乾淨 (去除可能的空格)
        df.columns = [c.strip() for c in df.columns]

        # 篩選 t=1 的資料
        if 't' in df.columns:
            df_t1 = df[df['t'] == 1]
        else:
            # 如果沒有 t 欄位，假設整份檔案都是 t=1
            df_t1 = df
            print(f"Warning: {file_path} 中沒有 't' 欄位，預設使用所有資料作為 t=1。")

        # 填補空值為 0
        df_t1 = df_t1.fillna(0)

        # 建立 BITRATES 與 k 欄位的對應 (假設 k1, k2, k3, k4 對應 BITRATES[0]~[3])
        # BITRATES = [0.75, 1.20, 1.85, 2.85]
        k_columns = ['k1', 'k2', 'k3', 'k4']

        for _, row in df_t1.iterrows():
            try:
                r = int(row['region'])
            except KeyError:
                continue # 跳過沒有 region 的列

            if r not in self.regions:
                continue

            data[r] = {}
            for i, k in enumerate(k_columns):
                if k in df.columns and i < len(BITRATES):
                    b = BITRATES[i]
                    count = int(row[k])
                    data[r][b] = count
                else:
                    # 如果檔案缺少某個 k 欄位，預設為 0
                    if i < len(BITRATES):
                        data[r][BITRATES[i]] = 0
        
        return data

    # --------------------------------------------------------
    # Poisson 動態（正負變化）
    # --------------------------------------------------------
    def poisson_delta(self):
        # 產生一個以 0 為中心的變化量，這裡簡單模擬
        # 若要嚴格符合 Poisson，通常是指到達率，但這裡是用作"人數增減"
        # 簡單實作：隨機增加或減少少量人數
        change = np.random.poisson(POISSON_LAMBDA)
        # 讓它有正有負 (e.g., poisson(2) 期望值是 2，減去 2 讓期望值變 0)
        return change - int(POISSON_LAMBDA)

    # --------------------------------------------------------
    # 生成所有時間槽的 real/pred
    # --------------------------------------------------------
    def generate(self):
        # t=1 直接使用讀入的 base data
        self.real[1] = self.base_real
        self.pred[1] = self.base_pred

        # t = 2~T
        for t in range(2, self.T + 1):
            self.real[t] = {}
            self.pred[t] = {}
            for r in self.regions:
                self.real[t][r] = {}
                self.pred[t][r] = {}

                # 從 t-1 延續，並加上隨機波動
                for b in BITRATES:
                    prev_real = self.real[t-1][r].get(b, 0)
                    prev_pred = self.pred[t-1][r].get(b, 0)

                    # 加入隨機波動
                    delta_real = random.randint(-2, 2) # 或者使用 self.poisson_delta()
                    delta_pred = random.randint(-2, 2)

                    self.real[t][r][b] = max(0, prev_real + delta_real)
                    self.pred[t][r][b] = max(0, prev_pred + delta_pred)

        return self.real, self.pred


# ------------------------------------------------------------
# 測試區塊
# ------------------------------------------------------------
if __name__ == "__main__":
    regions = list(range(1, 31))
    
    # 請確保這兩個檔案在同目錄下，或是提供正確路徑
    # 這裡使用您上傳後的 CSV 檔名作為預設測試
    real_file = "user_distribution_real.xlsx - Sheet1.csv"
    pred_file = "predicted_user_distribution.xlsx - Sheet1.csv"

    print(f"Testing loading from: {real_file} and {pred_file}")
    
    gen = DemandGenerator(regions, real_file, pred_file, T=5)
    real, pred = gen.generate()

    # 簡單檢查 Region 1 的數據
    if 1 in real[1]:
        print("t=1, Region 1 (Real):", real[1][1])
    else:
        print("Region 1 data not found or file load failed.")
        
    if 1 in real[5]:
        print("t=5, Region 1 (Real) [Simulated]:", real[5][1])