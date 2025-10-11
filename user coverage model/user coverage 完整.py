#!/usr/bin/env python
# coding: utf-8

# In[5]:


pip install pandas


# In[7]:


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Coverage Blocks Visualization (Walker-Star, i=53°, |lat|<=50°)
-------------------------------------------------------------------
This script shows how we divide the Earth's surface into user blocks within
a latitude band (±LAT_LIMIT). The block size is derived from Walker-Star
grid spacings:
    ΔΩ = 360/P (longitude spacing per plane)
    Δu = 360/S (latitude spacing per along-track slot)
We also overlay satellite footprints (based on altitude H and minimum
elevation E_MIN) to see how blocks relate to single-satellite coverage.
We print a handover check (cell diagonal <= service diameter).

Run:
    python user_coverage_blocks.py

Adjustable parameters are near the top of the file.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ===================== Parameters (edit here) =====================
# User belt
LAT_LIMIT   = 50.0     # users live within ±LAT_LIMIT [deg]

# Walker-Star (i=53°); choose P,S then block sizes follow from ΔΩ, Δu
P = 72                 # number of planes  -> ΔΩ = 360/P = 5.0°
S = 23                 # sats/plane        -> Δu = 360/S ≈ 15.652°

# Satellite footprint overlay
SHOW_FOOTPRINTS = True
H       = 550.0        # satellite altitude [km]
E_MIN   = 25.0         # minimum elevation angle [deg] for service
# Example sub-satellite points (lat, lon) [deg]; feel free to add more
SUBPOINTS = [
    (0.0,   0.0),
    (0.0,  5.0),       # neighbor in RAAN spacing sense (ΔΩ)
]

# Earth model
R_EARTH = 6378.137     # [km] consistent with other scripts

# Output
SAVE_PNG = True
PNG_OUT  = "user_coverage_blocks.png"
CSV_OUT  = "user_coverage_blocks_cells.csv"

# ===================== Derived grid =====================
BLOCK_DLON = 360.0/float(P)   # ΔΩ
BLOCK_DLAT = 360.0/float(S)   # Δu

# ===================== Geometry helpers =====================
def sph_to_xyz(lat_deg, lon_deg, radius=1.0):
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    x = radius * np.cos(lat) * np.cos(lon)
    y = radius * np.cos(lat) * np.sin(lon)
    z = radius * np.sin(lat)
    return np.array([x, y, z])

def xyz_to_sph(v):
    v = np.array(v, dtype=float)
    r = np.linalg.norm(v)
    x, y, z = v
    lat = np.degrees(np.arcsin(z / r))
    lon = np.degrees(np.arctan2(y, x))
    return lat, lon

def local_basis_from_subpoint(lat_deg, lon_deg):
    n0 = sph_to_xyz(lat_deg, lon_deg, 1.0)
    north_approx = sph_to_xyz(lat_deg + 1e-5, lon_deg, 1.0) - n0
    n = north_approx / np.linalg.norm(north_approx)
    e = np.cross(n, n0); e /= np.linalg.norm(e)
    n = np.cross(n0, e); n /= np.linalg.norm(n)
    return n0, e, n

def rotate_from_subpoint(lat0_deg, lon0_deg, psi_deg, az_deg):
    n0, e, n = local_basis_from_subpoint(lat0_deg, lon0_deg)
    az  = np.radians(az_deg)
    psi = np.radians(psi_deg)
    t_hat = np.cos(az)*e + np.sin(az)*n
    p = np.cos(psi)*n0 + np.sin(psi)*t_hat
    return p / np.linalg.norm(p)

def elevation_deg(sat_xyz, gnd_xyz):
    v = sat_xyz - gnd_xyz
    v_norm = np.linalg.norm(v)
    n_hat = gnd_xyz / np.linalg.norm(gnd_xyz)
    sin_el = np.dot(v, n_hat) / v_norm
    sin_el = np.clip(sin_el, -1.0, 1.0)
    return np.degrees(np.arcsin(sin_el))

def footprint_boundary(lat0_deg, lon0_deg, E_min_deg, R, h, az_step=2.0):
    sub_xyz = sph_to_xyz(lat0_deg, lon0_deg, 1.0)
    sat_xyz = sub_xyz * (R + h)

    az_list = np.arange(0.0, 360.0, az_step)
    lat_list, lon_list = [], []

    for az in az_list:
        lo, hi = 0.0, 90.0
        for _ in range(30):
            mid = 0.5*(lo + hi)
            g_hat = rotate_from_subpoint(lat0_deg, lon0_deg, mid, az)
            g_xyz = g_hat * R
            el = elevation_deg(sat_xyz, g_xyz)
            if el > E_min_deg:
                lo = mid
            else:
                hi = mid
        psi_sol = 0.5*(lo + hi)
        g_hat = rotate_from_subpoint(lat0_deg, lon0_deg, psi_sol, az)
        lat_b, lon_b = xyz_to_sph(g_hat)
        lat_list.append(lat_b); lon_list.append(lon_b)

    return np.array(lat_list), np.array(lon_list)

# Service half-angle ψ from geometry (used to check handover criterion)
def service_half_angle_deg(R, h, emin_deg):
    e = np.deg2rad(emin_deg)
    num = R*(np.cos(e)**2) + np.sin(e)*np.sqrt((R*np.sin(e))**2 + 2*R*h + h**2)
    den = R + h
    cpsi = num/den
    cpsi = np.clip(cpsi, -1.0, 1.0)
    return np.degrees(np.arccos(cpsi))

# ===================== Block builder =====================
def build_blocks(lat_limit=55.0, dlat=10.0, dlon=10.0):
    lat_edges = np.arange(-lat_limit, lat_limit + 1e-6, dlat)
    lon_edges = np.arange(-180.0, 180.0 + 1e-6, dlon)

    blocks = []
    bid = 0
    for i in range(len(lat_edges)-1):
        la0, la1 = lat_edges[i], lat_edges[i+1]
        if la1 < -lat_limit or la0 > lat_limit:
            continue
        for j in range(len(lon_edges)-1):
            lo0, lo1 = lon_edges[j], lon_edges[j+1]
            center_lat = 0.5*(la0 + la1)
            center_lon = 0.5*(lo0 + lo1)
            blocks.append(dict(
                id = bid,
                lat0 = la0, lat1 = la1,
                lon0 = lo0, lon1 = lo1,
                center_lat = center_lat,
                center_lon = center_lon
            ))
            bid += 1
    return blocks

# ===================== Visualization =====================
def plot_blocks_and_footprints(lat_limit, dlat, dlon,
                               show_footprints=True, subpoints=None,
                               h=550.0, e_min=25.0, R=6378.137,
                               save_png=False, png_path="user_coverage_blocks.png",
                               csv_out=None):
    fig = plt.figure(figsize=(12, 6.5))
    ax = plt.gca()
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 60)
    ax.set_xlabel("Longitude [deg]")
    ax.set_ylabel("Latitude [deg]")
    ax.set_title("User Coverage Blocks (±{:.0f}°), ΔΩ={:.2f}°, Δu={:.3f}°".format(
        lat_limit, dlon, dlat))
    ax.grid(True, alpha=0.25)

    # Shade forbidden bands (|lat| > lat_limit)
    ax.fill_between([-180, 180],  lat_limit, 90,  alpha=0.10, step='pre')
    ax.fill_between([-180, 180], -90, -lat_limit, alpha=0.10, step='pre')

    # Draw blocks
    blocks = build_blocks(lat_limit, dlat, dlon)
    for b in blocks:
        rect = plt.Rectangle((b['lon0'], b['lat0']), dlon, dlat, fill=False, linewidth=0.5)
        ax.add_patch(rect)

    # Label a subset for readability
    for b in blocks[::max(1, len(blocks)//30)]:
        ax.text(b['center_lon'], b['center_lat'], str(b['id']), ha='center', va='center', fontsize=7)

    # Optional footprints
    if show_footprints and subpoints:
        for (slat, slon) in subpoints:
            lat_fp, lon_fp = footprint_boundary(slat, slon, e_min, R, h, az_step=2.0)
            ax.plot(lon_fp, lat_fp, label="Footprint @ ({:+.0f}°, {:+.0f}°), E_min={}°".format(slat, slon, int(e_min)))
            ax.scatter([slon], [slat], marker='*', s=150, zorder=5)
        ax.legend(loc='lower left', fontsize=8, ncol=2)

    # Print and check handover rule
    psi_deg = service_half_angle_deg(R, h, e_min)
    service_diam_deg = 2.0*psi_deg
    diagonal_deg = np.sqrt(dlat**2 + dlon**2)
    print("Service half-angle ψ = {:.4f}° (diameter = {:.4f}°)".format(psi_deg, service_diam_deg))
    print("Grid diagonal = {:.4f}°   ->   {}".format(diagonal_deg,
          "OK (handover overlap guaranteed)" if diagonal_deg <= service_diam_deg else "NOT OK"))

    # Export CSV of blocks if requested
    if csv_out is not None:
        df = pd.DataFrame(blocks)
        df.to_csv(csv_out, index=False)
        print("Saved cells CSV ->", csv_out)

    plt.tight_layout()
    if save_png:
        plt.savefig(png_path, dpi=150)
        print("Saved plot ->", png_path)
    else:
        plt.show()

# ===================== Main =====================
if __name__ == "__main__":
    plot_blocks_and_footprints(
        lat_limit=LAT_LIMIT,
        dlat=BLOCK_DLAT,
        dlon=BLOCK_DLON,
        show_footprints=SHOW_FOOTPRINTS,
        subpoints=SUBPOINTS,
        h=H,
        e_min=E_MIN,
        R=R_EARTH,
        save_png=True,
        png_path=PNG_OUT,
        csv_out=CSV_OUT
    )


# In[ ]:




