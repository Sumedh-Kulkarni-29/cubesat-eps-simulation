# CubeSat Electrical Power Subsystem (EPS) Simulation

This repository contains a time-domain simulation of a CubeSat Electrical Power Subsystem (EPS).
The simulation models solar power generation, battery state-of-charge (SOC) dynamics,
spacecraft power loads, and energy-aware operational logic over orbital day–night cycles.

The project is intended as a system-level study of EPS behavior rather than a component-level
circuit simulation.

---

## Objectives

- Simulate EPS energy balance over one or more orbits
- Analyze battery SOC evolution under sunlight and eclipse
- Study the effect of varying the number of solar panels
- Evaluate energy margins for nominal operation and communication events

---

## Features

- Orbital sunlight and eclipse modeling
- Solar power generation based on panel count
- Battery SOC dynamics with charge and discharge efficiency
- Nominal and reduced power load profiles
- Net power and SOC visualization
- Parametric study of SOC vs number of solar panels

---

## Simulation Overview

At each time step, the simulator computes:

- Solar power input based on orbital position
- Spacecraft power consumption
- Net power available to charge or discharge the battery
- Updated battery state-of-charge

The simulation captures expected EPS behavior such as SOC decay during eclipse
and recovery during sunlight.

---

## Example Outputs

- Solar power and load vs orbital angle
- Battery SOC vs orbital angle
- Net power balance vs orbital angle
- Minimum SOC vs number of solar panels

These plots are used to assess EPS sizing and operational feasibility.

---

## Assumptions

- Circular Low Earth Orbit (LEO)
- Fixed solar panel orientation
- Lumped battery model
- Ideal power conversion (no DC-DC losses)
- Thermal effects neglected

These assumptions are intentionally simple to focus on system-level energy flow.

---

## How to Run

```bash
pip install -r requirements.txt
python src/eps_simulation.py
