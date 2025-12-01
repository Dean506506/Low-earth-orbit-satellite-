
# satellites.py
# 衛星與軌道相關的資料結構與函式
# ---------------------------------------------------------------
# 設計假設：
#   1. 地球被切成 5x6 共 30 個區域，編號方式如下（column-major）：
#        1   6  11  16  21  26
#        2   7  12  17  22  27
#        3   8  13  18  23  28
#        4   9  14  19  24  29
#        5  10  15  20  25  30
#
#      也就是「先列後行」，同一欄就是同一條軌道。
#
#   2. 一開始 t = 1 時，我們假設「每個區域上空剛好一顆衛星」，
#      衛星編號可以與起始區域相同（sat_id = region_id）。
#
#   3. 每一個時間槽 t → t+1 時，所有衛星「往上移動一格」（同一欄內循環）：
#        row_new = (row - 1) mod 5         （row 從 0 開始算）
#      例如：
#        t=1: sat 在 region 1 (row=0,col=0)
#        t=2: 會移到 region 5 (row=4,col=0)
#        t=3: 再移到 region 4 (row=3,col=0)
#      如此在同一欄內做循環，符合「同一 column 代表同軌道」的假設。
#
#   4. cluster(i) 的定義：
#        cluster(i) = {i 自己} ∪ {上、下、左、右 的鄰接衛星}
#      其中左/右不做 cross-seam，不會從第 1 欄連到第 6 欄。
#      最多可有 5 顆衛星（自己 + 四個方向）。
#
#   5. 本檔案只負責「衛星位置與 cluster 計算」，不碰 RL 或 LSTM。
#

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from configs import SATELLITE_BATTERY_MAX
# ---------------------------------------------------------------
# 一些基本常數（預設可從 configs 覆蓋）
# ---------------------------------------------------------------
N_ROWS = 5   # 區域列數
N_COLS = 6   # 區域欄數
N_REGIONS = N_ROWS * N_COLS


# ---------------------------------------------------------------
# 小工具：region <-> (row, col) 轉換
# ---------------------------------------------------------------
def region_to_rc(region_id: int) -> Tuple[int, int]:
    """將 region 編號轉成 (row, col)，皆為 0-based。

    region_id: 1 ~ 30
    回傳: (row, col) 其中 row: 0~4, col: 0~5
    """
    if region_id < 1 or region_id > N_REGIONS:
        raise ValueError(f"region_id 超出範圍: {region_id}")
    region0 = region_id - 1
    col = region0 // N_ROWS
    row = region0 % N_ROWS
    return row, col


def rc_to_region(row: int, col: int) -> int:
    """將 (row, col) 轉回 region 編號 (1~30)。

    row: 0~4
    col: 0~5
    """
    if not (0 <= row < N_ROWS and 0 <= col < N_COLS):
        raise ValueError(f"(row,col) 超出範圍: ({row},{col})")
    region0 = row + col * N_ROWS
    return region0 + 1


# ---------------------------------------------------------------
# 衛星物件
# ---------------------------------------------------------------
@dataclass
class Satellite:
    """單一顆衛星的狀態描述。

    重點欄位：
        sat_id       : 衛星編號（1~30），可與起始 region 相同
        region_id    : 目前所在的地區編號（1~30）
        busy         : 當前時間槽內是否已被指派轉碼任務
        processing   : 紀錄目前正在處理的 bitrate（例如 {1.85: True}）
        battery      : 剩餘電量（任意單位，實際耗電模型由上層決定）
        bw_in_use    : 目前已使用的 ISL 頻寬比例 (0~1)
    """
    sat_id: int
    region_id: int
    busy: bool = False
    processing: Dict[float, bool] = field(default_factory=dict)
    battery: float = SATELLITE_BATTERY_MAX
    bw_in_use: float = 0.0

    def row_col(self) -> Tuple[int, int]:
        """回傳目前所在的 (row, col) 0-based。"""
        return region_to_rc(self.region_id)

    def move_up_one_step(self) -> None:
        """往「上方」區域移動一格（同欄循環）。"""
        row, col = self.row_col()
        # row-1，若 <0 則從最底一列回來
        new_row = (row - 1) % N_ROWS
        self.region_id = rc_to_region(new_row, col)

    def reset_state_for_new_timeslot(self) -> None:
        """每個時間槽開始時，重置轉碼相關狀態。"""
        self.busy = False
        self.processing.clear()
        self.bw_in_use = 0.0
        # 電量是否在每個時間槽回復，交由上層決定，這裡不自動修改。


# ---------------------------------------------------------------
# 衛星網路：管理全部衛星、位置與 cluster
# ---------------------------------------------------------------
class SatelliteNetwork:
    """用來管理整個衛星群（位置更新、查詢 cluster 等）。"""

    def __init__(self, n_rows: int = N_ROWS, n_cols: int = N_COLS):
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.satellites: Dict[int, Satellite] = {}
        self.region_to_sat: Dict[int, int] = {}

    # ----------------------- 初始化 ----------------------------
    def init_from_regions(self) -> None:
        """假設一開始 t=1，每個區域上空有一顆衛星，sat_id = region_id。"""
        self.satellites.clear()
        self.region_to_sat.clear()
        for region_id in range(1, self.n_rows * self.n_cols + 1):
            sat = Satellite(sat_id=region_id, region_id=region_id)
            self.satellites[sat.sat_id] = sat
            self.region_to_sat[region_id] = sat.sat_id

    # ----------------------- 查詢函式 --------------------------
    def get_sat_by_id(self, sat_id: int) -> Satellite:
        return self.satellites[sat_id]

    def get_sat_at_region(self, region_id: int) -> Optional[Satellite]:
        sat_id = self.region_to_sat.get(region_id)
        if sat_id is None:
            return None
        return self.satellites[sat_id]

    # ----------------------- 位置更新 --------------------------
    def advance_one_timeslot(self) -> None:
        """所有衛星依照軌道模型往上移動一格。"""
        # 先更新 region_id
        for sat in self.satellites.values():
            sat.move_up_one_step()

        # 重新建立 region_to_sat 對應
        self.region_to_sat.clear()
        for sat_id, sat in self.satellites.items():
            if sat.region_id in self.region_to_sat:
                # 正常不應該發生（一區多星），發生代表模型設定有問題
                raise RuntimeError(f"區域 {sat.region_id} 出現多顆衛星: {sat_id} 與 {self.region_to_sat[sat.region_id]}")
            self.region_to_sat[sat.region_id] = sat_id

    # ----------------------- cluster 計算 ----------------------
    def cluster_of(self, sat_id: int) -> List[int]:
        """給定一顆衛星，回傳其 cluster 內所有衛星 ID。

        cluster 定義：自己 + 上下左右，最多 5 顆。
        左右不做 cross-seam（不會從第 1 欄連到第 6 欄）。
        """
        sat = self.get_sat_by_id(sat_id)
        row, col = sat.row_col()

        # 先把自己放進 cluster
        clusters: List[int] = [sat_id]

        # 上
        if row - 1 >= 0:
            up_region = rc_to_region(row - 1, col)
            up_sat = self.get_sat_at_region(up_region)
            if up_sat is not None:
                clusters.append(up_sat.sat_id)

        # 下
        if row + 1 < self.n_rows:
            down_region = rc_to_region(row + 1, col)
            down_sat = self.get_sat_at_region(down_region)
            if down_sat is not None:
                clusters.append(down_sat.sat_id)

        # 左（不 cross-seam）
        if col - 1 >= 0:
            left_region = rc_to_region(row, col - 1)
            left_sat = self.get_sat_at_region(left_region)
            if left_sat is not None:
                clusters.append(left_sat.sat_id)

        # 右（不 cross-seam）
        if col + 1 < self.n_cols:
            right_region = rc_to_region(row, col + 1)
            right_sat = self.get_sat_at_region(right_region)
            if right_sat is not None:
                clusters.append(right_sat.sat_id)

        return clusters

    # ----------------------- 狀態重置 --------------------------
    def reset_all_for_new_timeslot(self) -> None:
        """讓所有衛星在新時間槽開始時重置 busy / processing / 頻寬。"""
        for sat in self.satellites.values():
            sat.reset_state_for_new_timeslot()


# 若直接執行本檔案，做一個簡單測試
if __name__ == "__main__":
    net = SatelliteNetwork()
    net.init_from_regions()
    print("t=1: region_to_sat =", net.region_to_sat)
    net.advance_one_timeslot()
    print("t=2: region_to_sat =", net.region_to_sat)
    # 測試某顆衛星的 cluster
    sat_id = 7
    print(f"sat {sat_id} 在 t=2 的 region =", net.get_sat_by_id(sat_id).region_id)
    print(f"sat {sat_id} 的 cluster =", net.cluster_of(sat_id))
