
# lstm_model.py
# ------------------------------------------------------------
# 每顆衛星的 LSTM-like 預測修正模型（簡易版，可運行）
# ------------------------------------------------------------
# 你的需求摘要：
#
#   ✔ 每顆衛星都維護自己的「預測 vs. 實際」誤差序列
#   ✔ 不做複雜深度學習（避免依賴 PyTorch/TensorFlow）
#   ✔ 只需支援以下行為：
#        1. 記錄歷史誤差 Δ (prediction - real)
#        2. 依據過去 K 個誤差，更新下一時刻預測值
#        3. 更新方式可簡化為：  new_pred = old_pred - lr * avg(error)
#        4. K = 3（可在 configs 設定）
#
#   ✔ 排程時（scheduling），衛星會根據「自己預測的需求」選擇最適合服務的 region
#   ✔ 若預測與實際不符 → LSTM 更新（online 修正）
#   ✔ 無需真正 LSTM 架構，只需符合你描述的功能
#
# ------------------------------------------------------------

from typing import List, Dict
from configs import LSTM_LEARNING_RATE


class LSTMUnit:
    """簡易版 LSTM-like 線性預測修正器（每顆衛星一個）。

    功能：
        - 保留最近 K 次誤差
        - 使用 avg-error 修正 prediction
    """

    def __init__(self, K: int = 3):
        self.K = K
        self.error_hist: List[float] = []  # 保存 Δ_t = pred - real

    # --------------------------------------------------------
    # 記錄新的誤差（pred - real）
    # --------------------------------------------------------
    def record_error(self, diff: float):
        self.error_hist.append(diff)
        if len(self.error_hist) > self.K:
            self.error_hist.pop(0)

    # --------------------------------------------------------
    # 根據誤差調整預測
    # pred: 原本預測的值
    # 回傳：修正後的新預測
    # --------------------------------------------------------
    def adjust_prediction(self, pred: float) -> float:
        if len(self.error_hist) == 0:
            return pred

        avg_err = sum(self.error_hist) / len(self.error_hist)
        new_pred = pred - LSTM_LEARNING_RATE * avg_err
        if new_pred < 0:
            new_pred = 0
        return new_pred


class LSTMManager:
    """管理所有衛星的 LSTMUnit。"""

    def __init__(self, sat_ids: List[int], K: int = 3):
        self.units: Dict[int, LSTMUnit] = {
            sid: LSTMUnit(K=K) for sid in sat_ids
        }

    def get_unit(self, sat_id: int) -> LSTMUnit:
        return self.units[sat_id]

    # --------------------------------------------------------
    # 記錄某衛星在時間 t 的預測誤差
    # --------------------------------------------------------
    def record_error(self, sat_id: int, diff: float):
        self.units[sat_id].record_error(diff)

    # --------------------------------------------------------
    # 修正某衛星的預測值
    # --------------------------------------------------------
    def adjust_prediction(self, sat_id: int, pred: float) -> float:
        return self.units[sat_id].adjust_prediction(pred)


# ------------------------------------------------------------
# 測試
# ------------------------------------------------------------
if __name__ == "__main__":
    lm = LSTMManager([1,2,3], K=3)
    lm.record_error(1, +10)
    lm.record_error(1, +5)
    print("adjust pred=100 →", lm.adjust_prediction(1, 100))
