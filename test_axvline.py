import matplotlib.pyplot as plt
fig, ax = plt.subplots()
l = ax.axvline(5)
l.set_xdata([10, 10])
print(l.get_xdata())
