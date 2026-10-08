import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid

knots = np.arange(0.0, 13.0)
x = np.linspace(0.0, 12.0, 12001)


def basis(order=4, rho=1.5):
    arr = []
    for i in range(len(knots) - 2):
        z = np.zeros_like(x)
        left = (x >= knots[i]) & (x < knots[i + 1])
        right = (x >= knots[i + 1]) & (x < knots[i + 2])
        if rho == 0:
            z[left] = (x[left] - knots[i]) / (knots[i + 1] - knots[i])
            z[right] = (knots[i + 2] - x[right]) / (knots[i + 2] - knots[i + 1])
        else:
            z[left] = np.sinh(rho * (x[left] - knots[i])) / np.sinh(
                rho * (knots[i + 1] - knots[i])
            )
            z[right] = np.sinh(rho * (knots[i + 2] - x[right])) / np.sinh(
                rho * (knots[i + 2] - knots[i + 1])
            )
        arr.append(z)
    for k in range(3, order + 1):
        cumulative = []
        for z in arr:
            integral = cumulative_trapezoid(z, x, initial=0)
            cumulative.append(integral / integral[-1] if integral[-1] > 0 else integral)
        arr = [cumulative[i] - cumulative[i + 1] for i in range(len(cumulative) - 1)]
    return np.array(arr)


b = basis(4, 10)
fig, axs = plt.subplots(
    2, 1, figsize=(10, 7.7), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]}
)
for j in range(2, 8):
    axs[0].plot(x, b[j], lw=2, label=f"B$_{{{j},4}}$(t)")

axs[0].set_xlim(2, 10)
axs[0].set_ylim(-0.02, 0.75)
axs[0].set_ylabel("Basis value")
axs[0].set_title(
    "Order-4 tension B-spline basis functions  (rho = 1.5, uniform knots)"
)
axs[0].legend(ncol=3, loc="upper right")
axs[0].grid(alpha=0.25)
for k in range(2, 11):
    axs[0].axvline(k, color="gray", alpha=0.12)

axs[1].plot(x, b[4], lw=2.5, label="Tension B-spline, rho = 1.5")
axs[1].plot(x, basis(rho=0)[4], "--", lw=2.3, label="Polynomial B-spline, rho = 0")
axs[1].set_xlim(2, 10)
axs[1].set_ylabel("B$_{4,4}$(t)")
axs[1].set_xlabel("Knot parameter t")
axs[1].grid(alpha=0.25)
axs[1].legend()
fig.tight_layout()
fig.savefig("figure/basis_functions.png", dpi=180)
print(
    "shape",
    b.shape,
    "minimum",
    b.min(),
    "central unity error",
    np.max(np.abs(b[:, (x >= 4) & (x <= 8)].sum(axis=0) - 1)),
)

plt.show()
