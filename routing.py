
# routing.py
# Walker-star 路由模型（依照你的規則）
# ------------------------------------------------------------
# 你的需求：
#   ✔ 使用你指定的 5x6 GRID（column-major）
#   ✔ 同一 column = 同一軌道（plane）
#   ✔ routing 採用：
#         1. 先沿 column 垂直移動（vertical-first）
#         2. 若需要跨 column，才水平移動（horizontal）
#   ✔ 不允許 cross-seam（不能 col=0 ↔ col=5）
#
#   本檔案提供：
#       - sat_id → region → (row,col)
#       - routing_path(sat_user, sat_src)
#            → 回傳一串中間經過的衛星 ID（包含起點與終點）
#
#   註：sat_network 必須先提供：
#          - region_to_sat[region] = sat_id
#          - satellites[sat_id].region_id
#       本檔案不修改衛星位置，只做路徑查詢。
#
# ------------------------------------------------------------

from typing import List
from satellites import region_to_rc, rc_to_region, N_ROWS, N_COLS


def routing_path(sat_network, sat_user_id: int, sat_src_id: int) -> List[int]:
    """計算 Walker-star vertical-first path。

    輸入：
        sat_network : SatelliteNetwork 物件
        sat_user_id : viewer 所在區域上的衛星 ID
        sat_src_id  : 直播主所在的衛星 ID

    回傳：
        path : List[int]  依序經過的衛星 ID（含起點與終點）

    規則：
        1. 先 vertical（同 column 內上下移動）
        2. 若 column 不同 → 再 horizontal（左右移動）
        3. 不能跨 seam（不允許 col=0 ↔ col=5）

    """
    # 取得 sat_user 與 sat_src 的 region
    sat_user = sat_network.get_sat_by_id(sat_user_id)
    sat_src = sat_network.get_sat_by_id(sat_src_id)

    region_u = sat_user.region_id
    region_s = sat_src.region_id

    # 轉成 (row,col)
    ru, cu = region_to_rc(region_u)
    rs, cs = region_to_rc(region_s)

    path: List[int] = []

    # --------------------------------------------------------
    # 步驟一：vertical-first（同 column）
    # --------------------------------------------------------
    if cu == cs:
        # 同一條軌道，直接垂直走
        step = 1 if rs > ru else -1
        for r in range(ru, rs + step, step):
            region = rc_to_region(r, cu)
            sat_id = sat_network.region_to_sat[region]
            path.append(sat_id)
        return path

    # --------------------------------------------------------
    # 不同 column → 先垂直對齊 row，再水平移動
    # --------------------------------------------------------

    # 1. 垂直對齊 row：讓 user 先走到與 src 同一 row
    step_v = 1 if rs > ru else -1
    for r in range(ru, rs + step_v, step_v):
        region = rc_to_region(r, cu)
        sat_id = sat_network.region_to_sat[region]
        path.append(sat_id)

    # 現在 viewer 停在 region (rs, cu)
    # 下一步從 col cu → col cs

    # 2. 水平移動（左/右，但不能跨 seam）
    step_h = 1 if cs > cu else -1
    for c in range(cu + step_h, cs + step_h, step_h):
        # seam check
        if c < 0 or c >= N_COLS:
            raise RuntimeError(f"Routing 跨越 seam：col={c}")

        region = rc_to_region(rs, c)
        sat_id = sat_network.region_to_sat[region]
        path.append(sat_id)

    return path


# ------------------------------------------------------------
# 測試
# ------------------------------------------------------------
if __name__ == "__main__":
    from satellites import SatelliteNetwork

    net = SatelliteNetwork()
    net.init_from_regions()

    # sat_user=1, sat_src=30
    print("t=1 region_to_sat:", net.region_to_sat)
    p = routing_path(net, 1, 30)
    print("path 1 → 30:", p)
