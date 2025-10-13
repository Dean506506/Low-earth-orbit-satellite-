#!/usr/bin/env python
# coding: utf-8

# In[ ]:





# In[17]:


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

# ==== 基本參數 ====
Re = 6371.0            # 地球半徑 [km]
h = 550.0              # 軌道高度 [km]
r = Re + h
inclination = np.deg2rad(53)  # 傾角
N_planes = 6
Sats_per_plane = 11

# 地球重力常數 (km^3/s^2)
mu = 398600.4418
omega = np.sqrt(mu / r**3)   # 角速度 [rad/s]
T_orbit = 2 * np.pi / omega  # 週期 [s]

# 時間軸 (取一個軌道週期的一部分)
t = np.linspace(0, 0.2*T_orbit, 80)  # 取 20% 軌道週期製作動畫

# ==== 回傳「依平面分組」的下投影座標 ====
def satellite_positions_by_plane(time):
    # 回傳 list，長度 = N_planes；每個元素是 (lats, lons) 的 numpy array
    per_plane = []
    for p in range(N_planes):
        RAAN = 2*np.pi*p / N_planes  # 均勻分布
        lats, lons = [], []
        for s in range(Sats_per_plane):
            M0 = 2*np.pi*s / Sats_per_plane
            theta = M0 + omega*time
            # 軌道平面座標 -> ECI（圓軌道假設）
            x_orb = r * np.cos(theta)
            y_orb = r * np.sin(theta)
            # 依傾角與 RAAN 旋轉到 ECI
            x_eci = (np.cos(RAAN)*x_orb - np.sin(RAAN)*np.cos(inclination)*y_orb)
            y_eci = (np.sin(RAAN)*x_orb + np.cos(RAAN)*np.cos(inclination)*y_orb)
            z_eci = np.sin(inclination)*y_orb
            # 轉成下投影緯經（弧度前先算度）
            lon = np.degrees(np.arctan2(y_eci, x_eci))
            lat = np.degrees(np.arcsin(z_eci / r))
            lats.append(lat)
            lons.append(lon)
        per_plane.append((np.array(lats), np.array(lons)))
    return per_plane

# ==== 動畫繪製 ====
cmap = plt.cm.get_cmap('tab10', N_planes)
fig, ax = plt.subplots(figsize=(10,5), subplot_kw={'projection':'mollweide'})
ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
ax.set_title("Walker-Star Constellation Projection (53°, 550 km)", pad=20)

def update(frame):
    ax.cla()
    ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
    ax.set_title("Walker-Star Constellation Projection (53°, 550 km)", pad=20)

    per_plane = satellite_positions_by_plane(t[frame])
    handles = []
    labels = []
    for p, (lats_deg, lons_deg) in enumerate(per_plane):
        # 轉成弧度給 mollweide
        lats = np.deg2rad(lats_deg)
        lons = np.deg2rad(lons_deg)
        sc = ax.scatter(lons, lats, s=12, color=cmap(p))
        # 只建立一次圖例項目（每平面一個）
        handles.append(sc)
        labels.append(f"Plane {p}")

    ax.legend(handles, labels, loc='lower left', fontsize=8, framealpha=0.8)
    return handles

ani = FuncAnimation(fig, update, frames=len(t), interval=120, blit=False)

# 匯出 GIF
ani.save("walker_star.gif", writer=PillowWriter(fps=10))
plt.close(fig)
print("✅ 已生成 walker_star.gif（各平面不同顏色）")


# In[ ]:




