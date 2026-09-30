#!/usr/bin/env python3

import numpy as np

file_to_trunc = "/sharpwhisperer_mirror/safe_2_paper/2026-06-12_20-35-44_stm32f3_cwDACwlna_vddarevert_500000/traces_chipwhisperer.npy"
file_to_write = "/sharpwhisperer_experiments/2026-06-12_20-35-44_stm32f3_cwDACwlna_vddarevert_500000_truncd3/traces_chipwhisperer.npy"

#arr = np.load("/sharpwhisperer_mirror/safe_2_paper/2026-07-16_16-56-53_stm32f3_cwPWR_1000/traces_chipwhisperer.npy")
#print(arr.shape)

# Variables
input_path = file_to_trunc
output_path = file_to_write

# Load the array
arr = np.load(input_path)

# Cut
#cut_arr = arr[:, 154:303]
#cut_arr = arr[:, :310]
cut_arr = arr[:, :380]

# Save the result
np.save(output_path, cut_arr)

print("Original shape:", arr.shape)
print("New shape:", cut_arr.shape)
print("Saved to:", output_path)

