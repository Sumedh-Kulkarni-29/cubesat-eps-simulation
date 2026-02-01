import numpy as np
import matplotlib.pyplot as plt
import math

# =========================================================
# Time parameters
# =========================================================
dt = 100.0                              # seconds
orbit_period = 95 * 60                 # seconds
num_orbits = 100
t_end = num_orbits * orbit_period
time = np.arange(0, t_end, dt)

# =========================================================
# Solar & panel parameters
# =========================================================
G_sun = 1361                            # W/m^2
A_panel = 0.1 * 0.1                    # m^2
packing_eff = 0.5

num_panels = np.array([1, 2, 3, 4, 5, 6])
A_total = num_panels * A_panel * packing_eff

# Efficiencies
eta_cell = 0.30
eta_mppt = 0.95
eta_wiring = 0.97

P_max = G_sun * A_total                # raw solar power per config

# =========================================================
# Subsystem loads
# =========================================================
P_OBC = 0.5
P_ADCS = 0.8
P_COMMS = 0.7
P_PAYLOAD = 0.5
P_load_nominal = P_OBC + P_ADCS + P_COMMS + P_PAYLOAD

# =========================================================
# TX parameters
# =========================================================
P_TX = 15.0                            # W
TX_duration = 15 * 60                 # seconds
TX_theta_width = 360 * TX_duration / orbit_period

# =========================================================
# Battery parameters
# =========================================================
E_battery = 10.0                       # Wh
SOC_min = 0.2
SOC_max = 0.99
SOC_init = 0.6

fade_rate = 0.20                      # 20% per year
self_discharge_per_day = 0.02 / 30    # 2% per month

# =========================================================
# Orbital angle
# =========================================================
theta = 360.0 * (time % orbit_period) / orbit_period

# =========================================================
# State variables (2D: time × panel-config)
# =========================================================
N_t = len(time)
N_p = len(num_panels)

SOC = np.zeros((N_t, N_p))
SOC[0, :] = SOC_init

P_solar_hist = np.zeros((N_t, N_p))
P_load_hist = np.zeros(N_t)

# =========================================================
# Main simulation loop
# =========================================================
for t in range(1, N_t):

    theta_i = theta[t]
    theta_eff = math.radians(theta_i - 45)

    # Eclipse model
    eclipse = 0 if (120 < theta_i < 270) else 1

    # Panel projection factor
    f_theta = 0.6 + 0.4 * math.cos(theta_eff)
    f_theta = max(f_theta, 0.0)

    # Mission time
    mission_days = time[t] / (3600 * 24)
    mission_years = mission_days / 365.0

    # Battery fade
    E_batt_eff = E_battery * (1 - fade_rate * mission_years)
    E_batt_eff = max(E_batt_eff, 0.3 * E_battery)

    for p in range(N_p):

        # Solar power
        P_solar = (
            P_max[p]
            * eta_cell
            * eta_mppt
            * eta_wiring
            * f_theta
            * eclipse
        )

        # Base load (safe vs nominal)
        if SOC[t - 1, p] < 0.30:
            P_load = P_OBC
        else:
            P_load = P_load_nominal

        # TX feasibility
        E_batt_available = SOC[t - 1, p] * E_batt_eff
        E_TX = P_TX * TX_duration / 3600.0
        E_load_TX = P_load_nominal * TX_duration / 3600.0
        E_reserve = 0.30 * E_batt_eff

        TX_on = (
            eclipse == 1
            and 0 <= theta_i <= TX_theta_width
            and (E_batt_available - E_load_TX > E_reserve + E_TX)
        )

        if TX_on:
            P_load += P_TX

        # Energy balance
        dE = (P_solar - P_load) * dt / 3600.0
        if dE > 0:
            dE *= 0.95  # charge efficiency

        SOC[t, p] = SOC[t - 1, p] + dE / E_batt_eff

        # Self discharge
        SOC[t, p] *= (1 - self_discharge_per_day * dt / (3600 * 24))

        SOC[t, p] = np.clip(SOC[t, p], SOC_min, SOC_max)

        P_solar_hist[t, p] = P_solar

    P_load_hist[t] = P_load

# =========================================================
# Plots
# =========================================================
plt.figure(figsize=(10, 5))
for p in range(N_p):
    plt.plot(time / 3600, SOC[:, p], label=f"{num_panels[p]} panels")
plt.xlabel("Time [hours]")
plt.ylabel("SOC")
plt.title("Battery SOC for Different Panel Counts")
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 5))
for p in range(N_p):
    plt.plot(time / 3600, P_solar_hist[:, p], label=f"{num_panels[p]} panels")
plt.plot(time / 3600, P_load_hist, 'k--', label="Load")
plt.xlabel("Time [hours]")
plt.ylabel("Power [W]")
plt.title("Solar Power vs Load")
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()

# =========================================================
# Sanity checks
# =========================================================
print("Peak solar power per config [W]:", np.max(P_solar_hist, axis=0))
print("Average sunlit power [W]:",
      [np.mean(P_solar_hist[P_solar_hist[:, p] > 0, p]) for p in range(N_p)])


# =========================================================
# Results Analysis
# =========================================================
print("\n" + "="*60)
print("EPS OPTIMIZATION RESULTS")
print("="*60)

for p in range(N_p):
    min_soc = np.min(SOC[:, p])
    avg_soc = np.mean(SOC[:, p])
    final_soc = SOC[-1, p]
    
    # Check if mission fails (SOC hits minimum)
    mission_viable = "✓ VIABLE" if min_soc > 0.25 else "✗ FAILS"
    
    print(f"\n{num_panels[p]} Panels:")
    print(f"  Min SOC: {min_soc:.1%}")
    print(f"  Avg SOC: {avg_soc:.1%}")
    print(f"  Final SOC (100 orbits): {final_soc:.1%}")
    print(f"  Mass: {num_panels[p] * 0.05:.2f} kg")  # assume 50g per panel
    print(f"  Status: {mission_viable}")

print("\n" + "="*60)
print("RECOMMENDATION: X panels provide optimal balance")
print("="*60)
# Summary metrics
min_socs = [np.min(SOC[:, p]) for p in range(N_p)]
avg_socs = [np.mean(SOC[:, p]) for p in range(N_p)]
masses = num_panels * 0.05  # kg

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: SOC vs Panel Count
ax1.plot(num_panels, min_socs, 'ro-', label='Minimum SOC', linewidth=2)
ax1.plot(num_panels, avg_socs, 'bo-', label='Average SOC', linewidth=2)
ax1.axhline(y=0.3, color='r', linestyle='--', label='Safe Mode Threshold')
ax1.axhline(y=0.2, color='k', linestyle='--', label='Critical Minimum')
ax1.set_xlabel('Number of Solar Panels')
ax1.set_ylabel('State of Charge')
ax1.set_title('SOC Performance vs Panel Configuration')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Trade-off (SOC vs Mass)
ax2.plot(masses, min_socs, 'go-', linewidth=2, markersize=8)
for i, n in enumerate(num_panels):
    ax2.annotate(f'{n}p', (masses[i], min_socs[i]), 
                 textcoords="offset points", xytext=(0,10))
ax2.axhline(y=0.3, color='r', linestyle='--', alpha=0.5)
ax2.set_xlabel('Total Solar Panel Mass (kg)')
ax2.set_ylabel('Minimum SOC')
ax2.set_title('Reliability vs Mass Trade-off')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('eps_optimization_summary.png', dpi=300)
plt.show()
# Plot single orbit detail (last orbit, with 4 panels for example)
orbit_start = -int(orbit_period/dt)
theta_orbit = theta[orbit_start:]
SOC_orbit = SOC[orbit_start:, 3]  # 4 panels
P_solar_orbit = P_solar_hist[orbit_start:, 3]
P_load_orbit = P_load_hist[orbit_start:]

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

# Eclipse shading
eclipse_region = (theta_orbit > 120) & (theta_orbit < 270)

ax1.fill_between(theta_orbit, 0, 1, where=eclipse_region, 
                  alpha=0.2, color='gray', label='Eclipse')
ax1.plot(theta_orbit, P_solar_orbit, 'orange', linewidth=2, label='Solar Power')
ax1.plot(theta_orbit, P_load_orbit, 'r--', linewidth=2, label='Load')
ax1.set_ylabel('Power (W)')
ax1.set_title('Single Orbit Analysis (4 Panels)')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.fill_between(theta_orbit, 0, 100, where=eclipse_region, 
                  alpha=0.2, color='gray')
ax2.plot(theta_orbit, SOC_orbit * 100, 'b', linewidth=2)
ax2.axhline(y=30, color='r', linestyle='--', alpha=0.5, label='Safe Mode')
ax2.set_ylabel('SOC (%)')
ax2.legend()
ax2.grid(True, alpha=0.3)

ax3.fill_between(theta_orbit, -5, 20, where=eclipse_region, 
                  alpha=0.2, color='gray', label='Eclipse')
ax3.plot(theta_orbit, P_solar_orbit - P_load_orbit, 'g', linewidth=2)
ax3.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax3.set_xlabel('Orbital Angle θ (degrees)')
ax3.set_ylabel('Net Power (W)')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('single_orbit_detail.png', dpi=300)
plt.show()
