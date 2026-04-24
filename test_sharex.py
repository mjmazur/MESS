import matplotlib.pyplot as plt
import numpy as np

strip = np.random.rand(10, 100)
profile = np.mean(strip, axis=0)
wls = np.linspace(300, 700, 100)
ref_spec_wls = np.linspace(200, 800, 200)
ref_spec_y = np.sin(ref_spec_wls/10)

fig, (ax_star, ax_prof, ax_strip) = plt.subplots(3, 1, figsize=(8, 6), sharex=True)

ax_star.plot(ref_spec_wls, ref_spec_y, 'r-')
ax_prof.plot(wls, profile, 'b-')

extent = [wls[0], wls[-1], strip.shape[0], 0]
ax_strip.imshow(strip, aspect='auto', extent=extent)

ax_star.set_xlim(wls[0], wls[-1])

plt.savefig('test_sharex.png')
print("Done")
