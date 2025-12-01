
# main_sim.py
from core_part1 import CorePart1
from core_part2 import CorePart2
from core_part3 import CorePart3
from core_part4 import CorePart4
from core_part5 import CorePart5
from core_part6 import CorePart6
from demand import DemandGenerator
from satellites import SatelliteNetwork
from rl_model import RLModel
from lstm_model import LSTMManager


def reset_satellites(net):
    for sat in net.satellites.values():
        sat.busy = False
        sat.processing = {}

def main():
    T = 5
    dg = DemandGenerator()
    real, pred = dg.real, dg.pred

    net = SatelliteNetwork()
    rl = RLModel()
    lstm_mgr = LSTMManager(sat_ids=list(range(1, 31)))
    p1 = CorePart1(net, real, pred, T)
    p2 = CorePart2(net, rl)
    p3 = CorePart3(net, lstm_mgr, real, pred)
    p4 = CorePart4(net)
    p5 = CorePart5(net)
    p6 = CorePart6()

    for t in range(1, T+1):
        if t > 1:
            net.advance_one_timeslot()
        reset_satellites(net)
        for r in range(1, 31):
            s1 = p1.process_region_stage1(t, r)
            act = p2.activation_step(s1)
            sched = p3.scheduling_step(t, r, act, s1["real_req"])
            delay = p4.compute_region_delay(t, r, sched, s1["real_req"])
            p5.update_region_energy(t, r, sched)
            p6.log_all(t, r, act, sched, delay)

    p6.export_all()

if __name__ == "__main__":
    main()
