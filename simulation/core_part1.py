
# core_part1.py
# ------------------------------------------------------------
# core.py 第 1 段：區域需求解析 + 初始化（可運行骨架）
# ------------------------------------------------------------
# 內容：
#   ✔ process_region() 前置邏輯
#   ✔ 取得 real/pred 需求
#   ✔ 找 viewer 衛星、source 衛星
#   ✔ routing path 整合
#   ✔ 完整中文註解
#
# 這是完整 core.py 的第一段，可直接被 import。
# ------------------------------------------------------------

from typing import Dict, List
from satellites import SatelliteNetwork
from routing import routing_path


class CorePart1:
    """core.py 的第 1 段（區域解析與初始化）。"""

    def __init__(self,
                 sat_network: SatelliteNetwork,
                 real_demand: Dict,
                 pred_demand: Dict,
                 T: int):
        self.net = sat_network
        self.real = real_demand
        self.pred = pred_demand
        self.T = T

    # --------------------------------------------------------
    # 處理單一 region（第 1 段：做前置，後續段落會 override）
    # --------------------------------------------------------
    def process_region_stage1(self, t: int, region: int):
        """回傳所有後續階段需要的基本資料：
        - viewer_satid
        - source_satid
        - real requests
        - pred requests
        - routing path
        """

        # 使用者所在區域的衛星
        sat_user = self.net.get_sat_at_region(region)
        if sat_user is None:
            raise RuntimeError(f"region {region} 上沒有衛星（不應該發生）")

        # 假設直播主永遠在 region 1
        sat_src = self.net.get_sat_at_region(1)
        if sat_src is None:
            raise RuntimeError("region 1 沒有 source 衛星（不應該發生）")

        # Real / Pred 的需求字典
        # real[t][region] = {bitrate: num}
        real_req = self.real[t][region]
        pred_req = self.pred[t][region]

        # 路徑：vertical-first Walker-star routing
        path = routing_path(self.net, sat_user.sat_id, sat_src.sat_id)

        return {
            "sat_user": sat_user.sat_id,
            "sat_src": sat_src.sat_id,
            "real_req": real_req,
            "pred_req": pred_req,
            "path": path
        }


# ------------------------------------------------------------
# 測試（用非常簡易的資料）
# ------------------------------------------------------------
if __name__ == "__main__":
    # 建立假衛星網路
    from satellites import SatelliteNetwork
    net = SatelliteNetwork()
    net.init_from_regions()

    # 假需求：t=1, region=1 real=pred={0.75: 10}
    real = {1: {1: {0.75: 10}}}
    pred = {1: {1: {0.75: 12}}}

    core = CorePart1(net, real, pred, T=1)
    out = core.process_region_stage1(1, 1)
    print("測試結果：", out)
