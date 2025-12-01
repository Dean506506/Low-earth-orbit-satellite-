
# core_part3.py
# ------------------------------------------------------------
# core.py 第 3 段：Scheduling（依衛星各自預測分配轉碼任務）
# ------------------------------------------------------------
# 根據你的描述，這一段的規則是：
#
#   ✔ 一個 cluster 內可能有多顆 idle 衛星（最多 5 顆）
#   ✔ 當前要處理的地區 region_r，有一組「需要被處理的 bitrate 任務」
#   ✔ cluster 內每一顆衛星，都有「自己所在地區」的預測需求：
#
#        pred_demand[t][ sat.region_id ][ bitrate ]
#
#   ✔ Scheduling 規則（逐個 bitrate 分配）：
#
#        對於每一個需要被分配的 bitrate b：
#           1. 在 cluster 的 idle 衛星中，找出
#                  pred_demand[t][ sat.region_id ][ b ]
#              最大的那一顆衛星 sat*
#           2. 將「碼率 b 的轉碼任務」分配給 sat*
#           3. sat* 變成 busy，不再參與後續 bitrate 的分配
#           4. 用 sat* 的預測 vs sat* 所在地區的實際需求
#              來更新該衛星的 LSTM：
#
#                 error = pred_demand[t][ sat.region_id ][ b ]
#                         - real_demand[t][ sat.region_id ][ b ]
#
#                 lstm.record_error(sat_id, error)
#                 new_pred = lstm.adjust_prediction(sat_id, old_pred)
#                 pred_demand[t][ sat.region_id ][ b ] = new_pred
#
#   ✔ 不考慮 activation_sat 的優先排序，
#      分配完全由「各自的預測」決定。
#
#   ✔ 回傳：
#        assignments = { bitrate: sat_id }
#
# ------------------------------------------------------------

from typing import Dict, List
from satellites import SatelliteNetwork
from lstm_model import LSTMManager
from configs import BITRATES


class CorePart3:
    """core.py 的第 3 段：Scheduling。"""

    def __init__(self,
                 sat_network: SatelliteNetwork,
                 lstm_manager: LSTMManager,
                 real_demand: Dict,
                 pred_demand: Dict):
        # sat_network : 衛星網路（可查詢 sat.region_id / busy 狀態）
        # lstm_manager: 管理每顆衛星 LSTM 的物件
        # real_demand : real[t][region][bitrate] = 人數
        # pred_demand : pred[t][region][bitrate] = 人數（會被本模組更新）
        self.net = sat_network
        self.lstm = lstm_manager
        self.real_all = real_demand
        self.pred_all = pred_demand

    # --------------------------------------------------------
    # 主函式：對一個地區，在已選好的 activation_sat 所在的 cluster 內做排程
    # --------------------------------------------------------
    def scheduling_step(self,
                        t: int,
                        region_r: int,
                        activation_sat: int,
                        real_req_region: Dict[float, int]) -> Dict[float, int]:
        """對 region_r 的 bitrate 任務做排程，回傳 assignments。"""

        # 先找出 cluster（包含 activation_sat 自己）
        cluster = self.net.cluster_of(activation_sat)

        # 可用的 idle 衛星
        idle_sats = [sid for sid in cluster if not self.net.get_sat_by_id(sid).busy]

        if not idle_sats:
            raise RuntimeError("Scheduling 失敗：cluster 內沒有 idle 衛星")

        # 需要被分配的 bitrate（實際需求 > 0）
        required_bitrates = [b for b, n in real_req_region.items() if n > 0]

        assignments: Dict[float, int] = {}

        # 逐個 bitrate 分配
        for b in required_bitrates:

            if not idle_sats:
                # 理論上不應該發生，因為 activation 時已保證 idle 數量足夠
                raise RuntimeError("Scheduling 失敗：idle 衛星數不足以處理所有 bitrate")

            # 在目前 idle 的衛星中，找預測值最大的那一顆
            best_sat = None
            best_pred = -1.0

            for sat_id in idle_sats:
                sat = self.net.get_sat_by_id(sat_id)
                sat_region = sat.region_id

                # 該衛星對「自己所在地區」的預測
                sat_pred_dict = self.pred_all.get(t, {}).get(sat_region, {})
                pred_val = float(sat_pred_dict.get(b, 0.0))

                if pred_val > best_pred:
                    best_pred = pred_val
                    best_sat = sat_id

            if best_sat is None:
                # 所有預測都是 0，也要選一顆（例如第一顆）
                best_sat = idle_sats[0]

            # ---- 確定分配 ----
            assignments[b] = best_sat

            # 該衛星變成 busy，並標記正在處理 bitrate b
            sat_best = self.net.get_sat_by_id(best_sat)
            sat_best.busy = True
            sat_best.processing[b] = True

            # 從 idle_list 中移除，避免再被分配其他 bitrate
            idle_sats = [sid for sid in idle_sats if sid != best_sat]

            # ---- LSTM 更新該衛星對「自己地區 + 此 bitrate」的預測 ----
            sat_region = sat_best.region_id

            # 目前的預測值
            old_pred = float(self.pred_all.get(t, {}).get(sat_region, {}).get(b, 0.0))
            # 真實需求（以該衛星自己所在的地區為準）
            real_val = float(self.real_all.get(t, {}).get(sat_region, {}).get(b, 0.0))

            diff = old_pred - real_val

            # 記錄誤差並修正
            self.lstm.record_error(best_sat, diff)
            new_pred = self.lstm.adjust_prediction(best_sat, old_pred)

            # 寫回 pred_all
            if t not in self.pred_all:
                self.pred_all[t] = {}
            if sat_region not in self.pred_all[t]:
                self.pred_all[t][sat_region] = {}
            self.pred_all[t][sat_region][b] = new_pred

        return assignments
