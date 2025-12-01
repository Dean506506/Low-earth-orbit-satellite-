
# core_part5.py
# ------------------------------------------------------------
# core.py 第 5 段：Energy / Bandwidth 更新（完整正式版）
# ------------------------------------------------------------

from typing import Dict, List
from satellites import SatelliteNetwork
from routing import routing_path
from configs import (
    TRANSCODING_ENERGY,
    ENERGY_PER_HOP,
    BATTERY_MIN,
)


class CorePart5:
    """core.py 第 5 段：能源與頻寬更新"""

    def __init__(self, sat_network: SatelliteNetwork):
        self.net = sat_network
        self.energy_log = {}   # (t, region, bitrate) → dict

    # --------------------------------------------------------
    # 更新負責此 bitrate 的衛星的 energy 與 bandwidth
    # --------------------------------------------------------
    def update_energy_bw(
        self,
        t: int,
        region_r: int,
        bitrate: float,
        sat_proc: int,
        sat_user: int
    ):
        """更新 sat_proc 的能量消耗、頻寬使用，並紀錄 log"""

        sat = self.net.get_sat_by_id(sat_proc)

        # ---------------------------
        # 1. 計算 hop 數 (sat_proc → sat_user)
        # ---------------------------
        path = routing_path(self.net, sat_proc, sat_user)
        hop_count = max(0, len(path) - 1)

        # ---------------------------
        # 2. 轉碼能量
        # ---------------------------
        energy_transcoding = TRANSCODING_ENERGY.get(bitrate, 0.05)

        # ---------------------------
        # 3. ISL energy
        # ---------------------------
        energy_isl = hop_count * ENERGY_PER_HOP

        # ---------------------------
        # 4. 電池扣除
        # ---------------------------
        sat.battery -= (energy_transcoding + energy_isl)

        # ---------------------------
        # 5. 頻寬增加
        # ---------------------------
        sat.bw_in_use += bitrate

        # ---------------------------
        # 6. 若電量低於門檻 → sat 不可 idle
        # ---------------------------
        if sat.battery < BATTERY_MIN:
            sat.busy = True

        # ---------------------------
        # 7. energy log
        # ---------------------------
        self.energy_log[(t, region_r, bitrate)] = {
            "sat_proc": sat_proc,
            "hop_count": hop_count,
            "energy_transcoding": energy_transcoding,
            "energy_isl": energy_isl,
            "battery_after": sat.battery,
        }

    # --------------------------------------------------------
    # 批次對一個 region 所有 bitrate 做 energy 更新
    # --------------------------------------------------------
    def update_region_energy(
        self,
        t: int,
        region_r: int,
        assignments: Dict[float, int]
    ):
        """對該 region 的所有 bitrate 任務更新 energy/bw"""

        sat_user = self.net.get_sat_at_region(region_r)
        if sat_user is None:
            raise RuntimeError(f"region {region_r} 沒有 user 衛星")

        user_id = sat_user.sat_id

        for b, sat_proc in assignments.items():
            self.update_energy_bw(
                t=t,
                region_r=region_r,
                bitrate=b,
                sat_proc=sat_proc,
                sat_user=user_id
            )


if __name__ == "__main__":
    from satellites import SatelliteNetwork

    net = SatelliteNetwork()
    net.init_from_regions()

    core5 = CorePart5(net)

    assignments = {0.75: 8, 1.20: 13}
    core5.update_region_energy(t=1, region_r=10, assignments=assignments)
    print("energy log =", core5.energy_log)
