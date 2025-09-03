# Random Group Generator — Dashboard with Attendance Tabs (Jupyter/Colab)
# MIT License

from collections import defaultdict
import random
import itertools

# ----------------------------
# Core grouping logic
# ----------------------------

def partition_sizes(n_students, n_groups):
    """Split n_students into n_groups as evenly as possible."""
    base = n_students // n_groups
    rem  = n_students % n_groups
    return [base + 1] * rem + [base] * (n_groups - rem)

def round_cost(groups, pair_counts):
    """Cost for a grouping: sum of prior-meeting counts for pairs within groups."""
    cost = 0
    for g in groups:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g[i], g[j]
                cost += pair_counts[frozenset((a, b))]
    return cost

def build_round(students, n_groups, pair_counts, restarts=200, rng=None):
    """Build one round with a greedy heuristic and multiple randomized restarts."""
    if rng is None:
        rng = random.Random()
    sizes = partition_sizes(len(students), n_groups)
    best_groups, best_cost = None, float("inf")

    for _ in range(restarts):
        unassigned = students[:]
        rng.shuffle(unassigned)
        groups = []

        # degree = how often a student has already met others in the pool
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
            if best_cost == 0:  # perfect: no repeats
                break

    return best_groups, best_cost

def schedule_groups(students, n_groups, rounds, seed=None, restarts=200):
    """Build groups for multiple rounds, updating pair history after each round."""
    rng = random.Random(seed)
    students = students[:]              # avoid side effects
    pair_counts = defaultdict(int)      # track how often each pair occurred
    all_rounds = []

    for _ in range(rounds):
        groups, _ = build_round(students, n_groups, pair_counts, restarts=restarts, rng=rng)
        all_rounds.append(groups)

        # Update pair history
        for g in groups:
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    pair_counts[frozenset((g[i], g[j]))] += 1

        # Shuffle before next round to avoid positional bias
        rng.shuffle(students)

    return all_rounds

# ----------------------------
# Quality metrics & reporting
# ----------------------------

def schedule_quality(rounds):
    """
    Measure quality (pair repetition).
    100% means all pairs across all rounds are unique (no repeats).
    Returns: overall_pct, per_round_pct, counts
    """
    seen_pairs = set()
    total_pairs = 0
    new_pairs = 0
    per_round_pct = []
    per_round_counts = []

    for groups in rounds:
        r_total = 0
        r_new = 0
        for g in groups:
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    a, b = g[i], g[j]
                    pair = tuple(sorted((a, b)))
                    total_pairs += 1
                    r_total += 1
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        new_pairs += 1
                        r_new += 1
        r_pct = 100.0 * r_new / r_total if r_total else 100.0
        per_round_pct.append(r_pct)
        per_round_counts.append({"nye": r_new, "totalt": r_total})

    overall_pct = 100.0 * new_pairs / total_pairs if total_pairs else 100.0
    counts = {
        "overall": {"nye": new_pairs, "totalt": total_pairs},
        "per_round": per_round_counts,
    }
    return overall_pct, per_round_pct, counts

def collect_pair_stats(rounds):
    """Count pair occurrences and the rounds in which they occur."""
    pair_counts = defaultdict(int)
    pair_rounds = defaultdict(list)
    for r_index, groups in enumerate(rounds, start=1):
        for g in groups:
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    a, b = sorted((g[i], g[j]))
                    pair_counts[(a, b)] += 1
                    pair_rounds[(a, b)].append(r_index)
    return pair_counts, pair_rounds

def list_repeated_pairs(rounds, min_repeats=2):
    """List pairs that appear at least 'min_repeats' times."""
    pair_counts, pair_rounds = collect_pair_stats(rounds)
    repeated = [ (pair, c, pair_rounds[pair])
                 for pair, c in pair_counts.items() if c >= min_repeats ]
    repeated.sort(key=lambda x: (-x[1], x[0]))
    return repeated

def print_quality_report(rounds):
    overall, per_round, counts = schedule_quality(rounds)
    o = counts["overall"]
    print(f"\n=== KVALITETSINDEKS ===")
    print(f"Totalt: {overall:6.2f}%  (nye par: {o['nye']} / {o['totalt']})")
    for r, (pct, c) in enumerate(zip(per_round, counts["per_round"]), start=1):
        print(f"Runde {r}: {pct:6.2f}%  (nye par: {c['nye']} / {c['totalt']})")

def print_repeated_pairs(rounds, min_repeats=2, limit=None):
    """Print pairs appearing >= min_repeats times, with the rounds."""
    repeated = list_repeated_pairs(rounds, min_repeats=min_repeats)
    print(f"\n=== GJENTATTE PAR (minst {min_repeats} ganger) ===")
    count = 0
    for (a, b), c, rs in repeated:
        print(f"{a} – {b}: {c} ganger  (runder: {', '.join(map(str, rs))})")
        count += 1
        if limit is not None and count >= limit:
            break

# ----------------------------
# Plots (matplotlib)
# ----------------------------

import matplotlib.pyplot as plt

def plot_quality(rounds):
    """Two plots: % new pairs per round, and # repeated pairs per round."""
    _, per_round_pct, counts = schedule_quality(rounds)

    plt.figure()
    plt.plot(range(1, len(per_round_pct)+1), per_round_pct, marker="o")
    plt.title("Andel nye par per runde (%)")
    plt.xlabel("Runde")
    plt.ylabel("Nye par (%)")
    plt.ylim(0, 105)
    plt.grid(True)
    plt.show()

    repeated_per_round = [c["totalt"] - c["nye"] for c in counts["per_round"]]
    plt.figure()
    plt.bar(range(1, len(repeated_per_round)+1), repeated_per_round)
    plt.title("Antall gjentatte par per runde")
    plt.xlabel("Runde")
    plt.ylabel("Antall gjentatte par")
    plt.grid(True)
    plt.show()

def plot_pair_matrix(rounds):
    """Heatmap: how many times each pair of students co-occur in the same group."""
    names = sorted({name for round_ in rounds for group in round_ for name in group})
    index = {name: i for i, name in enumerate(names)}
    n = len(names)

    M = [[0]*n for _ in range(n)]
    for groups in rounds:
        for g in groups:
            for i in range(len(g)):
                for j in range(i+1, len(g)):
                    a, b = index[g[i]], index[g[j]]
                    M[a][b] += 1
                    M[b][a] += 1

    plt.figure()
    plt.imshow(M, interpolation="nearest")
    plt.title("Samlokasjonsmatrise (antall ganger i samme gruppe)")
    plt.xticks(range(n), names, rotation=90)
    plt.yticks(range(n), names)
    plt.colorbar()
    plt.tight_layout()
    plt.show()

# ----------------------------
# Dashboard with Attendance Tabs (ipywidgets)
# ----------------------------

from IPython.display import display
import ipywidgets as widgets

def _render_schedule(plan):
    for r, groups in enumerate(plan, start=1):
        print(f"-------- Runde {r} --------")
        for i, g in enumerate(groups, start=1):
            print(f"Gruppe {i}: {', '.join(g)}")
        print("")

def make_attendance_tabs(CLASS_MAP):
    """
    Create a Tab widget with one tab per class.
    Each tab has checkboxes for attendance + 'Alle'/'Ingen' buttons.
    Returns: tabs, class_names, checkbox_map
      - tabs: widgets.Tab
      - class_names: list[str] in tab order
      - checkbox_map: dict[class_name] -> list[widgets.Checkbox]
    """
    class_names = sorted(CLASS_MAP.keys())
    checkbox_map = {}
    tab_children = []

    for cname in class_names:
        # Create a checkbox per student, default value from present flag (1/0)
        checks = []
        for name, present in CLASS_MAP[cname]:
            cb = widgets.Checkbox(value=bool(present), description=name, indent=False)
            checks.append(cb)
        checkbox_map[cname] = checks

        # Select all / none buttons
        btn_all = widgets.Button(description="Marker alle")
        btn_none = widgets.Button(description="Fjern alle")

        def make_handler(boxes, val):
            def _h(_):
                for b in boxes:
                    b.value = val
            return _h

        btn_all.on_click(make_handler(checks, True))
        btn_none.on_click(make_handler(checks, False))

        # Layout the tab
        header = widgets.HBox([btn_all, btn_none])
        body = widgets.VBox(checks, layout=widgets.Layout(max_height="600px", overflow="auto"))
        tab_box = widgets.VBox([header, body])
        tab_children.append(tab_box)

    tabs = widgets.Tab(children=tab_children)
    for i, cname in enumerate(class_names):
        tabs.set_title(i, cname)

    return tabs, class_names, checkbox_map

def get_present_from_tab(selected_class, checkbox_map):
    """Return list of present student names from the selected class' checkboxes."""
    cbs = checkbox_map[selected_class]
    return [cb.description for cb in cbs if cb.value]

def build_dashboard_with_attendance(CLASS_MAP):
    """
    Interactive dashboard with attendance tabs:
    - Tabs: one per class, with checkboxes for each student (attendance).
    - Controls: groups, rounds, seed (None/int), restarts.
    - Output tabs: Plan, Kvalitet, Matrises.
    """
    # Attendance tabs
    att_tabs, class_names, checkbox_map = make_attendance_tabs(CLASS_MAP)

    # Controls
    groups_int = widgets.BoundedIntText(value=4, min=1, max=100, step=1, description="Grupper:",
                                        layout=widgets.Layout(width="200px"))
    rounds_int = widgets.BoundedIntText(value=2, min=1, max=50, step=1, description="Runder:",
                                        layout=widgets.Layout(width="200px"))
    seed_txt = widgets.Text(value="None", description="Seed:", layout=widgets.Layout(width="200px"))
    restarts_int = widgets.BoundedIntText(value=400, min=1, max=10000, step=1, description="Restarts:",
                                          layout=widgets.Layout(width="220px"))
    run_btn = widgets.Button(description="Lag plan", button_style="primary")

    # Outputs
    out_schedule = widgets.Output()
    out_quality  = widgets.Output()
    out_matrix   = widgets.Output()
    tabs_out = widgets.Tab(children=[out_schedule, out_quality, out_matrix])
    tabs_out.set_title(0, "Plan")
    tabs_out.set_title(1, "Kvalitet")
    tabs_out.set_title(2, "Matrise")

    # Help
    help_html = widgets.HTML(
        value=("""<b>Tips:</b> Bruk avhuking for oppmøte i fanen for riktig klasse. 
        Seed = <code>None</code> gir ulike resultater hver gang; angi et tall (f.eks. <code>42</code>) for reproduksjon.
        Restarts høyere = bedre (færre repetisjoner), men tregere.""")
    )

    controls = widgets.HBox([groups_int, rounds_int, seed_txt, restarts_int, run_btn])
    ui = widgets.VBox([att_tabs, controls, help_html, tabs_out])

    def _parse_seed(text):
        t = text.strip()
        if t.lower() == "none" or t == "":
            return None
        try:
            return int(t)
        except ValueError:
            return None

    def on_run_clicked(_):
        out_schedule.clear_output()
        out_quality.clear_output()
        out_matrix.clear_output()

        # Which class tab is selected?
        idx = att_tabs.selected_index
        selected_class = class_names[idx]
        students = get_present_from_tab(selected_class, checkbox_map)

        n_groups = groups_int.value
        n_rounds = rounds_int.value
        seed_val = _parse_seed(seed_txt.value)
        restarts = restarts_int.value

        if len(students) < n_groups:
            with out_schedule:
                print(f"Feil: Ikke nok tilstedeværende elever ({len(students)}) for {n_groups} grupper.")
            return

        plan = schedule_groups(
            students,
            n_groups=n_groups,
            rounds=n_rounds,
            seed=seed_val,
            restarts=restarts
        )

        # Plan
        with out_schedule:
            print(f"Klasse: {selected_class} | Elever (tilstede): {len(students)} | Grupper/runde: {n_groups} | Runder: {n_rounds}")
            _render_schedule(plan)

        # Quality (text + plots)
        with out_quality:
            print_quality_report(plan)
            print("")
            print_repeated_pairs(plan, min_repeats=2, limit=50)
            plot_quality(plan)

        # Matrix heatmap
        with out_matrix:
            plot_pair_matrix(plan)

    run_btn.on_click(on_run_clicked)
    display(ui)


# --------
# Classes 
# ---------

MyMathClass = [
    ["Taylor Swift", 1],
    ["Dwayne Johnson", 1],
    ["Scarlett Johansson", 1],
    ["Robert Downey Jr.", 1],
    ["Zendaya", 1],
    ["Chris Hemsworth", 1],
    ["Emma Watson", 1],
    ["Tom Hanks", 1],
    ["Rihanna", 1],
    ["Keanu Reeves", 1],
    ["Adele", 1],
    ["Leonardo DiCaprio", 1],
    ["Natalie Portman", 1],
    ["Beyoncé", 1],
    ["Ryan Gosling", 1],
]

MyPhysicsClass = [
    ["Bruno Mars", 1],
    ["Margot Robbie", 1],
    ["Idris Elba", 1],
    ["Gal Gadot", 1],
    ["Timothée Chalamet", 1],
    ["Billie Eilish", 1],
    ["Hugh Jackman", 1],
    ["Lady Gaga", 1],
    ["Michael B. Jordan", 1],
    ["Selena Gomez", 1],
    ["Jason Momoa", 1],
    ["Anne Hathaway", 1],
    ["Pedro Pascal", 1],
    ["Jennifer Lawrence", 1],
    ["Chris Evans", 1],
]

CLASS_MAP = {
    "MyMathClass": MyMathClass,
    "MyPhysicsClass": MyPhysicsClass,
}


# Show the dashboard:
build_dashboard_with_attendance(CLASS_MAP)
