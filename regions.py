# regions.py
# 區域（Region）相關資訊管理
# ---------------------------------------------------------------
# 依照使用者指定的地區切割方式：
#
#   1    6   11   16   21   26
#   2    7   12   17   22   27
#   3    8   13   18   23   28
#   4    9   14   19   24   29
#   5   10   15   20   25   30
#
# 此檔案提供下列功能：
#   1. region_id → (row, col)
#   2. (row, col) → region_id
#   3. 計算區域之間的 Manhattan 距離（用於 Activation 5 大特徵）
#   4. 建立 region adjacency（上下左右，不跨 seam）
#   5. 提供 sat_network 使用的 region→neighbor 查詢
#
# 所有函式皆為純數學，不依賴衛星狀態。

from typing import Tuple, Dict, List

N_ROWS = 5
N_COLS = 6
N_REGIONS = N_ROWS * N_COLS


# ---------------------------------------------------------------
# region_id → (row, col)
# ---------------------------------------------------------------
def region_to_rc(region_id: int) -> Tuple[int, int]:
    if region_id < 1 or region_id > N_REGIONS:
        raise ValueError(f"region_id 超出範圍: {region_id}")
    region0 = region_id - 1
    col = region0 // N_ROWS
    row = region0 % N_ROWS
    return row, col


# ---------------------------------------------------------------
# (row, col) → region_id
# ---------------------------------------------------------------
def rc_to_region(row: int, col: int) -> int:
    if not (0 <= row < N_ROWS and 0 <= col < N_COLS):
        raise ValueError(f"(row,col) 超出範圍: ({row},{col})")
    region0 = row + col * N_ROWS
    return region0 + 1


# ---------------------------------------------------------------
# 區域的上下左右鄰居（不跨 seam）
# ---------------------------------------------------------------
def region_neighbors(region_id: int) -> List[int]:
    row, col = region_to_rc(region_id)
    neighbors = []

    # 上
    if row - 1 >= 0:
        neighbors.append(rc_to_region(row - 1, col))

    # 下
    if row + 1 < N_ROWS:
        neighbors.append(rc_to_region(row + 1, col))

    # 左（不跨 seam）
    if col - 1 >= 0:
        neighbors.append(rc_to_region(row, col - 1))

    # 右（不跨 seam）
    if col + 1 < N_COLS:
        neighbors.append(rc_to_region(row, col + 1))

    return neighbors


# ---------------------------------------------------------------
# region 之間的 Manhattan 距離（Activation 特徵：距離）
# ---------------------------------------------------------------
def region_distance(region_a: int, region_b: int) -> int:
    ra, ca = region_to_rc(region_a)
    rb, cb = region_to_rc(region_b)
    # 使用 Manhattan Distance 或是您原本的邏輯
    return abs(ra - rb) + abs(ca - cb)


# ---------------------------------------------------------------
# 建立所有 region → neighbors 的 dict
# ---------------------------------------------------------------
def build_region_graph() -> Dict[int, List[int]]:
    graph = {}
    for r in range(1, N_REGIONS + 1):
        graph[r] = region_neighbors(r)
    return graph


# ---------------------------------------------------------------
# [NEW] 取得直播主所在的 Region
# ---------------------------------------------------------------
def get_broadcaster_region(t: int) -> int:
    """
    回傳直播主 (Source) 所在的地區 ID。
    依據需求，固定回傳 Region 1。
    """
    return 1


# ---------------------------------------------------------------
# 測試
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("Region 1 → rc =", region_to_rc(1))
    print("rc (2,3) → region =", rc_to_region(2,3))
    print("region 7 neighbors =", region_neighbors(7))
    print("distance between 1 and 30 =", region_distance(1,30))
    print("Source region =", get_broadcaster_region(1))
    print("region graph snippet =", {k: build_region_graph()[k] for k in range(1,7)})