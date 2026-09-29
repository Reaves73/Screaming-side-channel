#!/usr/bin/env python3

import numpy as np
from numpy.matlib import repmat
import scipy.stats as st
import matplotlib.pyplot as plt

vco_curve = [
(800, 856.71),
(750, 854.78),
(700, 852.88),
(650, 850.95),
(600, 849.02)
]

sp_curve = [
(280, 433.09),
(300, 432.80),
(350, 430.37),
(400, 426.14),
(420, 423.97),
(440, 421.61),
(450, 420.29)
]

def apply_offset(curve, x_offset, y_offset):
    return [(x - x_offset, y - y_offset) for x, y in curve]


# Reference point for curve 1
vco_curve_offset = (700, 852.88)

# Reference point for curve 2
sp_curve_offset = (350, 430.37)

vco_c = apply_offset(vco_curve, *vco_curve_offset)
sp_c = apply_offset(sp_curve, *sp_curve_offset)

# Plot
x1, y1 = zip(*vco_c)
x2, y2 = zip(*sp_c)

plt.plot(x1, y1, 'o-', label='VCO')
plt.plot(x2, y2, 'o-', label='SP')

# Axes through (0, 0)
plt.axhline(0, color='black', linewidth=0.8)
plt.axvline(0, color='black', linewidth=0.8)

plt.xlabel('X')
plt.ylabel('Y')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
