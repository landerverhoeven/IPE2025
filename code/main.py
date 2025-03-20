import numpy as np
import matplotlib.pyplot as plt
from calculations_power import power_output, load_power
from average_power import average_power

# Constants for PV system
beta = np.radians(20)  # Panel tilt angle (radians)
A = 2  # Panel area (m^2)
eta = 0.18  # Panel efficiency (18%)
N = 15  # Number of panels
phi_panel = np.radians(180)  # Panel azimuth angle (radians)

# Costs
scissor_lift_cost = 170  # incl. vat
installation_cost = 1200  # incl.vat
uniet_solar_panel_cost = 110  # incl. vat

average_power(N, beta, A, eta, phi_panel)
