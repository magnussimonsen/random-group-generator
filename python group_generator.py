# group_generator_notebook.py
# MIT License
# ----------------------------
# Random Group Generator (Notebook-Friendly)
# ----------------------------
# This version is designed for Jupyter/Colab:
# - No argparse, no main(); just edit CONFIG and run the last cell.
# - Class lists use ["Name", present] where present = 1 (present) or 0 (absent).
# - The algorithm minimizes repeated pairings across rounds using simple heuristics.
# ----------------------------

from collections import defaultdict
import random

# ---------- Core functions ----------

def partition_sizes(n_students, n_groups):
    """
    Split n_students into n_groups as evenly as possible.
    Resulting sizes differ by at most 1 (e.g., 10 -> [3,3,2,2]).
    """
    base = n_students // n_groups
    rem  = n_students % n_groups
    return [base + 1] * rem + [base] * (n_groups - rem)

def round_cost(groups, pair_counts):
    """
    Cost function for a single round of groups.
    - For each pair (a,b) that appears in a group, add how many times
      they have met before (pair_counts[(a,b)]).
    - Lower cost = fewer repeated pairings.
    """
    cost = 0
    for g in groups:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g[i], g[j]
                cost += pair_counts[frozenset((a, b))]
    return cost

def build_round(students, n_groups, pair_counts, restarts=200, rng=None):
    """
    Construct one round (set of groups) using a greedy heuristic with restarts.

    Heuristic outline:
    1) Compute desired group sizes via partition_sizes.
    2) For each restart:
       - Shuffle students.
       - Compute 'degree' for each student = how many prior meetings they've had
         with others still unassigned (based on pair_counts).
       - Start each group with the highest-degree 'seed' (to spread conflicts).
       - Fill the group by repeatedly picking the candidate that adds the smallest
         incremental cost with the current group.
       - Keep the best (lowest-cost) grouping found across all restarts.

    Args:
        students: list[str] of present student names.
        n_groups: number of groups to form this round.
        pair_counts: defaultdict(int) tracking prior pairings across earlier rounds.
        restarts: how many randomized attempts to try; higher = better, slower.
        rng: random.Random instance (seeded upstream for reproducibility).

    Returns:
        (best_groups, best_cost)
    """
    if rng is None:
        rng = random.Random()
    sizes = partition_sizes(len(students), n_groups)
    best_groups, best_cost = None, float("inf")

    for _ in range(restarts):
        unassigned = students[:]
        rng.shuffle(unassigned)
        groups = []

        # degree = how often a student has already met others in the unassigned pool
        deg = {s: 0 for s in unassigned}
        for s in unassigned:
            deg[s] = sum(pair_counts[frozenset((s, t))] for t in unassigned if t != s)
        # Sort: handle higher-conflict students first; rng.random() breaks ties fairly
        unassigned.sort(key=lambda s: (-deg[s], rng.random()))

        for size in sizes:
            # Seed group with the highest-degree student remaining
            seed = unassigned.pop(0)
            group = [seed]

            # Greedily add the candidate that increases cost the least
            for _ in range(size - 1):
                best_cand, best_incr = None, float("inf")
                # Sample to keep it fast for large classes
                pool = unassigned if len(unassigned) <= 20 else rng.sample(unassigned, 20)
                for cand in pool:
                    incr = sum(pair_counts[frozenset((cand, x))] for x in group)
                    if incr < best_incr or (incr == best_incr and rng.random() < 0.5):
                        best_cand, best_incr = cand, incr
                if best_cand is None:
                    best_cand = unassigned[0]  # fallback; should rarely happen
                group.append(best_cand)
                unassigned.remove(best_cand)
            groups.append(group)

        cost = round_cost(groups, pair_counts)
        if cost < best_cost:
            best_groups, best_cost = groups, cost
            if best_cost == 0:  # perfect: no repeats in this round
                break

    return best_groups, best_cost

def schedule_groups(students, n_groups, rounds, seed=None, restarts=200):
    """
    Build groups for multiple rounds, updating pair history after each round.

    Args:
        students: list[str] of present student names.
        n_groups: number of groups to form per round.
        rounds: how many rounds to generate.
        seed: int | None. If int, results are reproducible; if None, results vary.
        restarts: passed to build_round; higher explores more possibilities.

    Returns:
        all_rounds: list of rounds; each round is a list of groups (list[list[str]]).
    """
    rng = random.Random(seed)   # Random(None) -> system entropy => non-deterministic
    students = students[:]      # copy to avoid side effects
    pair_counts = defaultdict(int)  # tracks how often each pair has occurred
    all_rounds = []

    for _ in range(rounds):
        groups, _ = build_round(students, n_groups, pair_counts, restarts=restarts, rng=rng)
        all_rounds.append(groups)

        # Update pair history so next round can avoid repeats
        for g in groups:
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    pair_counts[frozenset((g[i], g[j]))] += 1

        # Shuffle order before the next round to avoid positional bias
        rng.shuffle(students)

    return all_rounds

def print_schedule(rounds):
    """
    Pretty-print the schedule:
    -------- Round k --------
    Group 1: A, B, C
    Group 2: D, E, F
    """
    for r, groups in enumerate(rounds, start=1):
        print(f"-------- Round {r} --------")
        for i, g in enumerate(groups, start=1):
            print(f"Group {i}: {', '.join(g)}")

def present_names(class_list):
    """
    Convert class list with attendance flags to a flat list of present names.

    Input format (keep this):
        [["Alice", 1], ["Bob", 0], ["Charlie", 1], ...]
    Only entries with present==1 are included.
    """
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
N_GROUPS = 4                # groups per round (must be <= number of present students)
ROUNDS = 2                  # how many rounds of grouping to generate
SEED = None                 # None => different results each run; set int (e.g., 42) for reproducible results
RESTARTS = 400              # tries per round; higher = better chance to reduce repeats, but slower

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
