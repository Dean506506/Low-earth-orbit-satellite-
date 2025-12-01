
# core_part6.py
# ------------------------------------------------------------
# Part 6：Logs + Summary + 論文用圖產生
# ------------------------------------------------------------
import json
import csv
import matplotlib.pyplot as plt
import os

class CorePart6:
    def __init__(self):
        self.activation_log = {}
        self.scheduling_log = {}
        self.delay_log = {}
        self.energy_log = {}

    # --------------------------------------------------------
    # 記錄 activation
    # --------------------------------------------------------
    def log_activation(self, t, region, sat_id):
        self.activation_log.setdefault(t, {})[region] = sat_id

    # --------------------------------------------------------
    # 記錄 scheduling
    # --------------------------------------------------------
    def log_scheduling(self, t, region, mapping):
        self.scheduling_log.setdefault(t, {})[region] = mapping

    # --------------------------------------------------------
    # 記錄 delay
    # --------------------------------------------------------
    def log_delay(self, t, region, delay):
        self.delay_log.setdefault(t, {})[region] = delay

    # --------------------------------------------------------
    # energy log（由 core_part5 提供）
    # --------------------------------------------------------
    def integrate_energy_log(self, energy_log):
        self.energy_log = energy_log

    # --------------------------------------------------------
    # 匯出結果
    # --------------------------------------------------------
    def export_results(self, path="results.json"):
        results = {
            "activation_log": self.activation_log,
            "scheduling_log": self.scheduling_log,
            "delay_log": self.delay_log,
            "energy_log": self.energy_log
        }
        with open(path, "w") as f:
            json.dump(results, f, indent=2)

    # --------------------------------------------------------
    # 論文用：平均 Delay per region 圖
    # --------------------------------------------------------
    def plot_delay_per_region(self, outdir="plots"):
        os.makedirs(outdir, exist_ok=True)
        regions = sorted(set(r for t in self.delay_log for r in self.delay_log[t]))
        avg_delay = []
        for r in regions:
            vals = []
            for t in self.delay_log:
                if r in self.delay_log[t]:
                    vals.append(self.delay_log[t][r])
            avg_delay.append(sum(vals)/len(vals))

        plt.figure()
        plt.bar(regions, avg_delay)
        plt.xlabel("Region")
        plt.ylabel("Average Delay (sec)")
        plt.title("Average Delay per Region")
        plt.savefig(os.path.join(outdir, "delay_per_region.png"))
        plt.close()

    # --------------------------------------------------------
    # 論文用：Delay vs Time Slot
    # --------------------------------------------------------
    def plot_delay_over_time(self, outdir="plots"):
        os.makedirs(outdir, exist_ok=True)
        times = sorted(self.delay_log.keys())
        avg_over_time = []
        for t in times:
            vals = list(self.delay_log[t].values())
            avg_over_time.append(sum(vals)/len(vals))

        plt.figure()
        plt.plot(times, avg_over_time, marker='o')
        plt.xlabel("Time Slot")
        plt.ylabel("Average Delay (sec)")
        plt.title("Average Delay Over Time")
        plt.savefig(os.path.join(outdir, "delay_over_time.png"))
        plt.close()

    # --------------------------------------------------------
    # Activation distribution
    # --------------------------------------------------------
    def plot_activation_distribution(self, outdir="plots"):
        os.makedirs(outdir, exist_ok=True)
        counter = {}
        for t in self.activation_log:
            for r, s in self.activation_log[t].items():
                counter[s] = counter.get(s, 0) + 1

        sats = sorted(counter.keys())
        counts = [counter[s] for s in sats]

        plt.figure()
        plt.bar(sats, counts)
        plt.xlabel("Satellite ID")
        plt.ylabel("Activation Count")
        plt.title("Activation Distribution")
        plt.savefig(os.path.join(outdir, "activation_distribution.png"))
        plt.close()

    # --------------------------------------------------------
    # Energy consumption per satellite
    # --------------------------------------------------------
    def plot_energy(self, outdir="plots"):
        os.makedirs(outdir, exist_ok=True)
        battery_after = {}

        for (_, _, bitrate), info in self.energy_log.items():
            sat = info["sat_proc"]
            battery_after[sat] = info["battery_after"]

        sats = sorted(battery_after.keys())
        vals = [battery_after[s] for s in sats]

        plt.figure()
        plt.bar(sats, vals)
        plt.xlabel("Satellite ID")
        plt.ylabel("Battery After Simulation")
        plt.title("Final Battery Level per Satellite")
        plt.savefig(os.path.join(outdir, "energy_per_satellite.png"))
        plt.close()

    # --------------------------------------------------------
    # Scheduling distribution (哪顆衛星處理哪些 bitrate)
    # --------------------------------------------------------
    def plot_scheduling_distribution(self, outdir="plots"):
        os.makedirs(outdir, exist_ok=True)
        counter = {}

        for t in self.scheduling_log:
            for r in self.scheduling_log[t]:
                for b, sat in self.scheduling_log[t][r].items():
                    counter.setdefault(b, {})
                    counter[b][sat] = counter[b].get(sat, 0) + 1

        for b in counter:
            sats = sorted(counter[b].keys())
            counts = [counter[b][sid] for sid in sats]

            plt.figure()
            plt.bar(sats, counts)
            plt.xlabel("Satellite ID")
            plt.ylabel("Count")
            plt.title(f"Scheduling Distribution for Bitrate {b}")
            plt.savefig(os.path.join(outdir, f"scheduling_bitrate_{b}.png"))
            plt.close()

    # --------------------------------------------------------
    # Hop distribution（展示 routing 特性）
    # --------------------------------------------------------
    def plot_hop_distribution(self, outdir="plots"):
        os.makedirs(outdir, exist_ok=True)
        hops = [info["hop_count"] for info in self.energy_log.values()]

        plt.figure()
        plt.hist(hops, bins=10)
        plt.xlabel("Hop Count")
        plt.ylabel("Frequency")
        plt.title("Hop Count Distribution")
        plt.savefig(os.path.join(outdir, "hop_distribution.png"))
        plt.close()

    # --------------------------------------------------------
    # 一鍵產生所有論文圖
    # --------------------------------------------------------
    def generate_paper_plots(self, outdir="plots"):
        self.plot_delay_per_region(outdir)
        self.plot_delay_over_time(outdir)
        self.plot_activation_distribution(outdir)
        self.plot_energy(outdir)
        self.plot_scheduling_distribution(outdir)
        self.plot_hop_distribution(outdir)
        print("All paper plots generated!")

