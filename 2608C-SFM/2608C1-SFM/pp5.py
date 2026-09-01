import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


import matplotlib.pyplot as plt
import types





# --- figure1 ---
plt.figure()
plt.plot([1, 2, 3])
plt.title("figure1")
#plt.gcf().canvas.manager.set_window_title("figure1")
#add_pan_zoom(plt.gcf(), plt.gca())

# --- figure2 ---
plt.figure()
plt.plot([3, 2, 1])
plt.title("figure2")

#plt.gcf().canvas.manager.set_window_title("figure2")
#add_pan_zoom(plt.gcf(), plt.gca())

plt.show()

"""# --- figure2 ---
fig2, ax2 = plt.subplots()
ax2.plot([3, 2, 1])
fig2.canvas.manager.set_window_title("figure1")
add_pan_zoom(fig2, ax2)
"""