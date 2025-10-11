#!/usr/bin/env python
# coding: utf-8

# In[2]:


pip install cartopy


# In[ ]:


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# --- 1. 常數與物理參數設定 ---
EARTH_RADIUS = 6371  # 地球半徑 (km)
ALTITUDE = 550       # 衛星軌道高度 (km)
SEMI_MAJOR_AXIS = EARTH_RADIUS + ALTITUDE # 軌道半長軸
GRAVITATIONAL_PARAM = 3.986004418e5  # 地球引力常數 (km^3/s^2)
EARTH_ROTATION_RATE_DEG_S = 360 / 86164.1 # 地球自轉角速度 (度/秒)，基於恆星日

# 根據物理定律計算軌道週期
ORBITAL_PERIOD_S = 2 * np.pi * np.sqrt(SEMI_MAJOR_AXIS**3 / GRAVITATIONAL_PARAM)

# --- 2. 星座設定函數 ---
def setup_walker_constellation_star(T, P, F, inclination_deg):
    """
    設定 Walker-Star 星座的初始軌道參數。
    此模型符合文獻定義：RAAN 在 0..180° 內均勻分佈。
    """
    assert T % P == 0, "衛星總數 T 必須能被軌道平面數 P 整除"
    sats_per_plane = T // P
    inclination_rad = np.deg2rad(inclination_deg)

    satellites = []
    for p in range(P):
        # Walker-Star 的核心：RAAN 在 180 度範圍內分佈
        raan_deg = p * (180.0 / P)
        raan_rad = np.deg2rad(raan_deg)
        
        for s in range(sats_per_plane):
            # 相位計算也基於 180 度
            mean_anomaly_deg = (s * (180.0 / sats_per_plane)
                              + p * F * (180.0 / T)) % 360.0
            mean_anomaly_rad = np.deg2rad(mean_anomaly_deg)
            
            satellites.append({
                "plane": p,
                "id_in_plane": s,
                "inclination": inclination_rad,
                "raan": raan_rad,
                "mean_anomaly_0": mean_anomaly_rad,
            })
    return satellites

# --- 3. 軌道傳播與計算函數 ---
def propagate_orbit(satellites, duration_s, time_steps):
    """
    計算一段時間內所有衛星的地面軌跡。
    (已修正 append 迴圈錯誤)
    """
    time_array = np.linspace(0, duration_s, time_steps)
    all_sats_ground_tracks = []

    for sat in satellites:
        longitudes = []
        latitudes = []
        
        for t in time_array:
            # 1. 計算當前平近點角
            mean_motion = 2 * np.pi / ORBITAL_PERIOD_S
            current_mean_anomaly = (sat['mean_anomaly_0'] + mean_motion * t) % (2 * np.pi)
            
            # 2. 計算在軌道平面上的位置
            u = current_mean_anomaly 
            x_orb = SEMI_MAJOR_AXIS * np.cos(u)
            y_orb = SEMI_MAJOR_AXIS * np.sin(u)

            # 3. 轉換到地心慣性坐標系 (ECI)
            i = sat['inclination']
            O = sat['raan']
            
            x_eci = x_orb * np.cos(O) - y_orb * np.cos(i) * np.sin(O)
            y_eci = x_orb * np.sin(O) + y_orb * np.cos(i) * np.cos(O)
            z_eci = y_orb * np.sin(i)

            # 4. 轉換為經緯度 (考慮地球自轉)
            earth_rotation_angle_rad = np.deg2rad(t * EARTH_ROTATION_RATE_DEG_S)
            lon_rad = np.arctan2(y_eci, x_eci) - earth_rotation_angle_rad
            lat_rad = np.arcsin(z_eci / SEMI_MAJOR_AXIS)
            
            lon_deg = np.rad2deg(lon_rad)
            lon_deg = (lon_deg + 180) % 360 - 180 # 確保經度在 [-180, 180]

            longitudes.append(lon_deg)
            latitudes.append(np.rad2deg(lat_rad))
            
        # ★ 修正點：在計算完一顆衛星的完整軌跡後，再添加到列表中
        all_sats_ground_tracks.append({'lon': np.array(longitudes), 'lat': np.array(latitudes)})
        
    return all_sats_ground_tracks

def get_3d_orbit_path(inclination_rad, raan_rad, num_points=100):
    """計算單一軌道平面在 3D ECI 空間中的坐標"""
    path_x, path_y, path_z = [], [], []
    for u in np.linspace(0, 2 * np.pi, num_points):
        x_orb = SEMI_MAJOR_AXIS * np.cos(u)
        y_orb = SEMI_MAJOR_AXIS * np.sin(u)
        x_eci = x_orb * np.cos(raan_rad) - y_orb * np.cos(inclination_rad) * np.sin(raan_rad)
        y_eci = x_orb * np.sin(raan_rad) + y_orb * np.cos(inclination_rad) * np.cos(raan_rad)
        z_eci = y_orb * np.sin(inclination_rad)
        path_x.append(x_eci); path_y.append(y_eci); path_z.append(z_eci)
    return np.array(path_x), np.array(path_y), np.array(path_z)

# --- 4. 繪圖與動畫函數 ---
def plot_static_ground_track(ground_tracks, T, P, F, inclination_deg):
    """繪製靜態的 2D 地面軌跡圖"""
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 8))
    
    try:
        import cartopy.crs as ccrs
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.stock_img(); ax.coastlines(color='cyan')
    except ImportError:
        print("提示: Cartopy 未安裝，將使用簡易背景。建議安裝以獲得地圖效果：pip install cartopy")
        ax = fig.add_subplot(111)
        ax.set_facecolor('black'); ax.grid(True, linestyle='--', alpha=0.5, color='gray')

    colors = plt.cm.turbo(np.linspace(0, 1, P))
    sats_per_plane = T // P

    for i, track in enumerate(ground_tracks):
        plane_index = i // sats_per_plane
        ax.plot(track['lon'], track['lat'], color=colors[plane_index], alpha=0.7, linewidth=1)

    ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    ax.set_title(f"Walker-Star Ground Track | {T}/{P}/{F} | Inclination: {inclination_deg}°", color='white')
    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
    plt.tight_layout(); plt.show()

def plot_3d_constellation(satellites_config, T, P, F, inclination_deg):
    """繪製清晰的 3D 星座軌道平面圖"""
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection='3d')

    u, v = np.linspace(0, 2*np.pi, 100), np.linspace(0, np.pi, 100)
    earth_x = EARTH_RADIUS * np.outer(np.cos(u), np.sin(v))
    earth_y = EARTH_RADIUS * np.outer(np.sin(u), np.sin(v))
    earth_z = EARTH_RADIUS * np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(earth_x, earth_y, earth_z, color='mediumblue', alpha=0.7, linewidth=0, antialiased=False)

    colors = plt.cm.turbo(np.linspace(0, 1, P))
    drawn_raans = set()
    for sat_config in satellites_config:
        raan = sat_config['raan']
        if raan not in drawn_raans:
            orbit_x, orbit_y, orbit_z = get_3d_orbit_path(sat_config['inclination'], raan)
            ax.plot(orbit_x, orbit_y, orbit_z, color=colors[sat_config['plane']], linewidth=2.0)
            drawn_raans.add(raan)

    for sat_config in satellites_config:
        u_current = sat_config['mean_anomaly_0']
        x_orb_curr = SEMI_MAJOR_AXIS * np.cos(u_current)
        y_orb_curr = SEMI_MAJOR_AXIS * np.sin(u_current)
        x_eci_curr = x_orb_curr * np.cos(sat_config['raan']) - y_orb_curr * np.cos(sat_config['inclination']) * np.sin(sat_config['raan'])
        y_eci_curr = x_orb_curr * np.sin(sat_config['raan']) + y_orb_curr * np.cos(sat_config['inclination']) * np.cos(sat_config['raan'])
        z_eci_curr = y_orb_curr * np.sin(sat_config['inclination'])
        ax.plot([x_eci_curr], [y_eci_curr], [z_eci_curr], 'o', color='gold', markersize=6, markeredgecolor='black')

    max_range = SEMI_MAJOR_AXIS * 1.1
    ax.set_box_aspect([1,1,1]); ax.set_xlim(-max_range, max_range); ax.set_ylim(-max_range, max_range); ax.set_zlim(-max_range, max_range)
    ax.set_title(f"3D Walker-Star Constellation | {T}/{P}/{F} | Inclination: {inclination_deg}°", color='white', fontsize=16)
    ax.set_xlabel("X (km)"); ax.set_ylabel("Y (km)"); ax.set_zlabel("Z (km)")
    ax.view_init(elev=35, azim=55); plt.tight_layout(); plt.show()

def animate_ground_track(ground_tracks, T, P, F, inclination_deg, filename="walker_star_animation.gif"):
    """生成地面軌跡的 GIF 動畫"""
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 8))
    
    use_cartopy = False
    try:
        import cartopy.crs as ccrs
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.stock_img(); ax.coastlines(color='cyan'); use_cartopy = True
    except ImportError:
        ax = fig.add_subplot(111)
        ax.set_facecolor('black'); ax.grid(True, linestyle='--', alpha=0.5, color='gray')

    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
    ax.set_title(f"Walker-Star Animation | {T}/{P}/{F} | Inclination: {inclination_deg}°", color='white')

    colors = plt.cm.turbo(np.linspace(0, 1, P))
    sats_per_plane = T // P
    points = [ax.plot([], [], 'o', color=colors[i // sats_per_plane], markersize=5)[0] for i in range(T)]

    num_frames = len(ground_tracks[0]['lon'])

    def init():
        for pt in points: pt.set_data([], [])
        return points

    def update(frame):
        for i, pt in enumerate(points):
            pt.set_data([ground_tracks[i]['lon'][frame]], [ground_tracks[i]['lat'][frame]])
        return points

    ani = FuncAnimation(fig, update, frames=num_frames, init_func=init, blit=not use_cartopy, interval=50)
    print(f"正在儲存 GIF 動畫到 {filename}，這可能需要一點時間...")
    ani.save(filename, writer='pillow', dpi=100); plt.close(fig)
    print("動畫儲存完成！")

# --- 5. 主程式執行區塊 ---
if __name__ == "__main__":
    # --- 星座參數設定 ---
    T = 24           # 衛星總數 (例如 GPS)
    P = 6            # 軌道平面數
    F = 1            # 相位參數
    INCLINATION = 55.0 # 軌道傾角

    # --- 模擬參數設定 ---
    TIME_STEPS = 500  # 模擬的總步數 (影響軌跡平滑度和 GIF 幀數)
    SIM_DURATION_S = ORBITAL_PERIOD_S * 2  # 模擬總時長 (建議至少2個週期以觀察完整圖案)

    # 1. 設定星座初始條件
    print("1. 正在設定 Walker-Star 星座...")
    sats_initial_conditions = setup_walker_constellation_star(T, P, F, INCLINATION)

    # 2. 繪製 3D 軌道平面圖
    print("2. 正在繪製 3D 星座軌道平面圖...")
    plot_3d_constellation(sats_initial_conditions, T, P, F, INCLINATION)
    
    # 3. 進行軌道傳播計算，以供 2D 繪圖和動畫使用
    print("3. 正在計算所有衛星的地面軌跡...")
    tracks = propagate_orbit(sats_initial_conditions, SIM_DURATION_S, TIME_STEPS)
    print("   軌跡計算完成！")

    # 4. 繪製靜態 2D 地面軌跡圖
    print("4. 正在繪製靜態 2D 地面軌跡圖...")
    plot_static_ground_track(tracks, T, P, F, INCLINATION)

    # 5. 生成並儲存 GIF 動畫
    print("5. 正在生成 GIF 動畫...")
    animate_ground_track(tracks, T, P, F, INCLINATION, filename="walker_star_final_animation.gif")
    
    print("\n所有任務已完成！")


# In[ ]:




