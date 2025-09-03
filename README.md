# Random Group Generator

This project provides a simple Python tool for generating random student groups across multiple rounds,  
while minimizing repeated pairings. It is designed for classrooms, workshops, or study sessions.

## Features
- Balances group sizes automatically.  
- Minimizes repeated pairings across rounds.  
- Supports marking students as **present** or **absent** using `[ "Name", 1/0 ]` format.  
- Works both as a standalone Python script (`group_generator.py`) or inside Jupyter/Colab.  

## Usage

### 1. Marking attendance
Each student is defined as a pair:
```python
["Alice", 1],   # 1 = present
["Bob", 0],     # 0 = absent
```
Only students with `1` are included when generating groups.

### 2. Running in terminal
Edit the `ClassA` or `ClassB` lists in the script to match your students, then run:

```bash
python group_generator.py --class ClassA --groups 4 --rounds 2
```

Optional arguments:
- `--class` (`ClassA` or `ClassB`, default `ClassA`)
- `--groups` number of groups per round (default 4)
- `--rounds` number of rounds (default 2)
- `--seed` random seed for reproducibility (default 42)

### 3. Running in Jupyter / Colab
Use the notebook-friendly version `group_generator_notebook.py`.  
Set the config variables (`SELECTED_CLASS`, `N_GROUPS`, `ROUNDS`) and run the last cell to see the schedule.

## Example output
```
Students (present): 12 | Groups per round: 4
-------- Round 1 --------
Group 1: StudentA02, StudentA04, StudentA06
Group 2: StudentA03, StudentA08, StudentA10
Group 3: StudentA01, StudentA12, StudentA07
Group 4: StudentA05, StudentA11, StudentA09
-------- Round 2 --------
Group 1: StudentA03, StudentA02, StudentA09
Group 2: StudentA01, StudentA11, StudentA06
Group 3: StudentA12, StudentA08, StudentA05
Group 4: StudentA10, StudentA07, StudentA04
-------- Round 3 --------
Group 1: StudentA12, StudentA10, StudentA09
Group 2: StudentA06, StudentA07, StudentA08
Group 3: StudentA01, StudentA02, StudentA05
Group 4: StudentA03, StudentA04, StudentA11
```

## License
This project is licensed under the MIT License.
