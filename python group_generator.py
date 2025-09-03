# group_generator_notebook.py
# MIT License
# ----------------------------
# Random Group Generator
# ----------------------------
#
# HOW TO USE:
# 1) Edit ClassA / ClassB below. Each student is ["Name", present],
#    where "student is present" = 1 "student is absent" or 0.
# 2) Set the CONFIG variables (SELECTED_CLASS, N_GROUPS, ROUNDS, etc.)
# 3) Run the last cell to generate and print the schedule.
# ----------------------------

from collections import defaultdict
import random

# ---------- Core functions ----------

def partition_sizes(n_students, n_groups):
    """Divide n_students evenly into n_groups (sizes may differ by at most 1)."""
    base = n_students // n_groups
    rem  = n_students % n_groups
    return [base + 1] * rem + [base] * (n_groups - rem)

def round_cost(groups, pair_counts):
    """Compute the 'cost' of a grouping = how many times pairs have already occurred."""
    cost = 0
    for g in groups:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g[i], g[j]
                cost += pair_counts[frozenset((a, b))]
    return cost

def build_round(students, n_groups, pair_counts, restarts=200, rng=None):
    """Try multiple randomized groupings, return the one with lowest cost."""
    if rng is None:
        rng = random.Random()
    sizes = partition_sizes(len(students), n_groups)
    best_groups, best_cost = None, float("inf")

    for _ in range(restarts):
        unassigned = students[:]
        rng.shuffle(unassigned)
        groups = []

        # degree = how often a student has already met others
        deg = {s: 0 for s in unassigned}
        for s in unassigned:
            deg[s] = sum(pair_counts[frozenset((s, t))] for t in unassigned if t != s)
        unassigned.sort(key=lambda s: (-deg[s], rng.random()))

        for size in sizes:
            seed = unassigned.pop(0)
            group = [seed]
            for _ in range(size - 1):
                best_cand, best_incr = None, float("inf")
                pool = unassigned if len(unassigned) <= 20 else rng.sample(unassigned, 20)
                for cand in pool:
                    incr = sum(pair_counts[frozenset((cand, x))] for x in group)
                    if incr < best_incr or (incr == best_incr and rng.random() < 0.5):
                        best_cand, best_incr = cand, incr
                if best_cand is None:
                    best_cand = unassigned[0]
                group.append(best_cand)
                unassigned.remove(best_cand)
            groups.append(group)

        cost = round_cost(groups, pair_counts)
        if cost < best_cost:
            best_groups, best_cost = groups, cost
            if best_cost == 0:
                break

    return best_groups, best_cost

def schedule_groups(students, n_groups, rounds, seed=None, restarts=200):
    """Schedule groups for multiple rounds, updating pair history each round."""
    rng = random.Random(seed)
    students = students[:]
    pair_counts = defaultdict(int)
    all_rounds = []

    for _ in range(rounds):
        groups, _ = build_round(students, n_groups, pair_counts, restarts=restarts, rng=rng)
        all_rounds.append(groups)

        # update pair counts
        for g in groups:
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    pair_counts[frozenset((g[i], g[j]))] += 1
        rng.shuffle(students)

    return all_rounds

def print_schedule(rounds):
    """Print groups in a nice format."""
    for r, groups in enumerate(rounds, start=1):
        print(f"-------- Round {r} --------")
        for i, g in enumerate(groups, start=1):
            print(f"Group {i}: {', '.join(g)}")

def present_names(class_list):
    """Filter class list for present students (value == 1)."""
    return [name for name, present in class_list if present == 1]


# ---------- Example Classes ----------
# Keep the format ["Name", present] where present is 1 (present) or 0 (absent).

ClassA = [
    ["StudentA01", 1],
    ["StudentA02", 1],
    ["StudentA03", 1],
    ["StudentA04", 1],
    ["StudentA05", 1],
    ["StudentA06", 1],
    ["StudentA07", 1],
    ["StudentA08", 1],
    ["StudentA09", 1],
    ["StudentA10", 1],
    ["StudentA11", 1],
    ["StudentA12", 1],
]

ClassB = [
    ["StudentB01", 1],
    ["StudentB02", 1],
    ["StudentB03", 1],
    ["StudentB04", 1],
    ["StudentB05", 1],
    ["StudentB06", 1],
    ["StudentB07", 1],
    ["StudentB08", 1],
    ["StudentB09", 1],
    ["StudentB10", 1],
    ["StudentB11", 1],
    ["StudentB12", 1],
    ["StudentB13", 1],
]

CLASS_MAP = {
    "ClassA": ClassA,
    "ClassB": ClassB,
}


# ---------- CONFIG + RUN ----------
# Edit these values and re-run this cell.

SELECTED_CLASS = "ClassA"   # "ClassA" or "ClassB"
N_GROUPS = 4                # number of groups per round
ROUNDS = 2                  # number of rounds
SEED = 42                   # random seed for reproducibility
RESTARTS = 400              # heuristic restarts per round

# Build inputs from the selected class and run the scheduler
_students = present_names(CLASS_MAP[SELECTED_CLASS])

if len(_students) < N_GROUPS:
    raise ValueError(f"Not enough present students ({len(_students)}) for {N_GROUPS} groups.")

_plan = schedule_groups(
    _students,
    n_groups=N_GROUPS,
    rounds=ROUNDS,
    seed=SEED,
    restarts=RESTARTS,
)

print(f"Students (present): {len(_students)} | Groups per round: {N_GROUPS}")
print_schedule(_plan)
