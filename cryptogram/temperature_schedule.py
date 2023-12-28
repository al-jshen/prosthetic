import numpy as np
import matplotlib.pyplot as plt

max_temp = 5
restarts = 10
aggression = 20
total_iters = 10_000
restart_every = total_iters / restarts
schedule = (
    lambda i: 1
    / (((i) / restart_every) + 1)
    * max_temp
    * (((i % restart_every) / total_iters) + 1) ** (-aggression)
)
xs = np.arange(total_iters)
ys = [schedule(i) for i in xs]
plt.plot(xs, ys)
plt.show()
