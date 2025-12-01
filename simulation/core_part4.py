
# core_part4.py
# ------------------------------------------------------------
# core.py 第 4 段：Delay 模型（完整正式版）
# ------------------------------------------------------------

from typing import Dict, List
from satellites import SatelliteNetwork
from routing import routing_path
from configs import (
    ACTIVATION_DELAY, SCHEDULING_DELAY,
    TRANSCODING_DELAY, ISL_PROPAGATION_DELAY,
    TX_DELAY_PER_HOP, BITRATES
)

class CorePart4:
    """core.py 的第 4 段：Delay 計算"""

    def __init__(self, sat_network: SatelliteNetwork):
        self.net = sat_network

    # --------------------------------------------------------
    # 判斷是否為 Case1（需要新轉碼）
    # --------------------------------------------------------
    def is_case1(self, cluster: List[int], bitrate: float) -> bool:
        for sid in cluster:
            sat = self.net.get_sat_by_id(sid)
            if bitrate in sat.processing:  
                return False
        return True

    # --------------------------------------------------------
    # 計算單一 bitrate 的 delay
    # --------------------------------------------------------
    def compute_delay_for_bitrate(self, region_r: int, bitrate: float, sat_proc: int) -> float:

        sat_user = self.net.get_sat_at_region(region_r)
        if sat_user is None:
            raise RuntimeError(f"region {region_r} 找不到 viewer 衛星")

        path = routing_path(self.net, sat_proc, sat_user.sat_id)
        H = max(0, len(path) - 1)

        prop_delay = H * ISL_PROPAGATION_DELAY
        tx_delay = H * TX_DELAY_PER_HOP.get(bitrate, 0.02)

        cluster = self.net.cluster_of(sat_proc)

        if self.is_case1(cluster, bitrate):
            return (
                ACTIVATION_DELAY +
                SCHEDULING_DELAY +
                TRANSCODING_DELAY.get(bitrate, 0.15) +
                prop_delay +
                tx_delay
            )
        else:
            return prop_delay + tx_delay

    # --------------------------------------------------------
    # 計算一個 region 的平均 delay
    # --------------------------------------------------------
    def compute_region_delay(self, region_r: int, real_req_region: Dict[float, int], assignments: Dict[float, int]) -> float:

        total_people = sum(real_req_region.values())
        if total_people == 0:
            return 0.0

        sum_delay = 0.0

        for b, num_people in real_req_region.items():
            if num_people <= 0:
                continue

            sat_proc = assignments.get(b)
            if sat_proc is None:
                raise RuntimeError(f"Delay 計算錯誤：bitrate {b} 沒有分配衛星")

            delay_b = self.compute_delay_for_bitrate(region_r, b, sat_proc)
            sum_delay += delay_b * num_people

        return sum_delay / total_people


if __name__ == "__main__":
    from satellites import SatelliteNetwork
    net = SatelliteNetwork()
    net.init_from_regions()
    core4 = CorePart4(net)
    real_req = {0.75: 10, 1.2: 5}
    assignments = {0.75: 8, 1.2: 13}
    d = core4.compute_region_delay(10, real_req, assignments)
    print("測試 region 10 平均 delay =", d)
