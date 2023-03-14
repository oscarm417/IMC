import math as m

labda = 0.4
no_levels = 5
levels = []
avail_orders = 40

for k in range(no_levels):
    poisson = (pow(labda, k)) / (m.factorial(k)) * pow(m.e, -labda)
    current_level = round(poisson * avail_orders)
    levels.append(current_level)


while sum(levels) != avail_orders:
    if sum(levels) > avail_orders:
        idx = len(levels) - next(x for x, value in enumerate(reversed(levels)) if value > 0) - 1
        levels[idx] -= 1
    if sum(levels) < avail_orders:
        levels[1] += 1

print(levels)

