from collections import defaultdict
import random

def partition_sizes(n_students, n_groups):
    base = n_students // n_groups
    rem  = n_students % n_groups
    return [base + 1] * rem + [base] * (n_groups - rem)

def round_cost(groups, pair_counts):
    cost = 0
    for g in groups:
        for i in range(len(g)):
            for j in range(i+1, len(g)):
                a, b = g[i], g[j]
                cost += pair_counts[frozenset((a,b))]
    return cost

def build_round(students, n_groups, pair_counts, restarts=200, rng=None):
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
    rng = random.Random(seed)
    students = students[:]
    pair_counts = defaultdict(int)
    all_rounds = []

    for _ in range(rounds):
        groups, _ = build_round(students, n_groups, pair_counts, restarts=restarts, rng=rng)
        all_rounds.append(groups)

        for g in groups:
            for i in range(len(g)):
                for j in range(i+1, len(g)):
                    pair_counts[frozenset((g[i], g[j]))] += 1
        rng.shuffle(students)

    return all_rounds

def print_schedule(rounds):
    for r, groups in enumerate(rounds, start=1):
        print(f"-------- Round {r} --------")
        for i, g in enumerate(groups, start=1):
            print(f"Group {i}: {', '.join(g)}")

# --- Classe and names of students ---

# Names are placeholders.
ClassA = [
    "StudentA01", "StudentA02", "StudentA03", "StudentA04",
    "StudentA05", "StudentA06", "StudentA07", "StudentA08",
    "StudentA09", "StudentA10", "StudentA11", "StudentA12"
]

ClassB = [
    "StudentB01", "StudentB02", "StudentB03", "StudentB04",
    "StudentB05", "StudentB06", "StudentB07", "StudentB08",
    "StudentB09", "StudentB10", "StudentB11", "StudentB12", "StudentB13"
]

if __name__ == "__main__":
    # choose which class to schedule
    klass = ClassA              # or ClassB
    n_groups = 4                # number of groups per round
    rounds   = 2                # number of rounds
    plan = schedule_groups(klass, n_groups=n_groups, rounds=rounds, seed=42, restarts=400)
    print(f"Students: {len(klass)} | Groups per round: {n_groups}")
    print_schedule(plan)

