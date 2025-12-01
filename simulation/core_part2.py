
# core_part2.py (updated feasibility logic)
from regions import region_distance

class CorePart2:
    def __init__(self, sat_network, rl_model):
        self.net = sat_network
        self.rl = rl_model

    def activation_step(self, stage1):
        region_r = stage1["region"]
        real_req = stage1["real_req"]
        path = stage1["path"]

        required_bitrates = [b for b, n in real_req.items() if n > 0]

        feature_table = {}
        feasible = {}

        for sat_id in path:
            cluster = self.net.cluster_of(sat_id)
            idle = [s for s in cluster if not self.net.get_sat_by_id(s).busy]

            existing = set()
            for s in cluster:
                sat = self.net.get_sat_by_id(s)
                existing |= set(sat.processing.keys())

            needed = [b for b in required_bitrates if b not in existing]
            needed_tasks = len(needed)

            feasible[sat_id] = (len(idle) >= needed_tasks)

            sat = self.net.get_sat_by_id(sat_id)
            dist = region_distance(sat.region_id, region_r)
            sim = len(required_bitrates) - len(needed)
            load = len(idle)
            battery = sum(self.net.get_sat_by_id(s).battery for s in idle)/len(idle) if idle else 0
            bw = sum(self.net.get_sat_by_id(s).bw_in_use for s in idle)/len(idle) if idle else 0

            feature_table[sat_id] = [dist, sim, load, battery, bw]

        return self.rl.select_best(feasible, feature_table)
