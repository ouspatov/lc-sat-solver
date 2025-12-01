# Longest Circuit SAT Solver

The SAT solver used is Glucose, more specifically Glucose 4.2.1. The source code is compiled like the following:

```bash
cmake .
make
```

## 1. Problem Description

The task is to find a simple cycle of length at least $k$ in a given undirected graph $G = (V, E)$.

SAT is a decision problem. Therefore, the script solves a sequence of decision problems: Does a simple cycle of length $i$ exist? Here script iterates from $i = N$ down to $k$ which is the target.
This means it finds the longest possible simple cycle that has a length of at least $k$.

### Input File Format

The input file is a text file defining the graph.

> The first significant line: `[NODES] [EDGES] [TARGET]`
>
> - **NODES**: Total number of vertices.
> - **EDGES**: Total number of edges
> - **TARGET**: The minimum cycle length $k$ from which to start the search.
>
> Subsequent lines: `[u] [v]`
>
> - Defines an edge between vertex $u$ and vertex $v$.

For examples, see the `instances/` directory.

## 2. Encoding

To ensure a satisfying model is a valid simple cycle we use 4 constraints:

| Constraint Description                  | Expanded Formula (Conceptual)                                             |
| :-------------------------------------- | :------------------------------------------------------------------------ |
| **1. Each position is occupied**        | $(X_{1,p} \lor X_{2,p} \lor \dots \lor X_{N,p})$                          |
| **2. No two vertices in one position**  | $(\neg X_{n_1,p} \lor \neg X_{n_2,p})$ for all $n_1 \neq n_2$             |
| **3. No vertex appears twice**          | $(\neg X_{n,p_1} \lor \neg X_{n,p_2})$ for all $p_1 \neq p_2$             |
| **4. Adjacent positions are connected** | $(\neg X_{n_1,p} \lor \neg X_{n_2, p+1})$ for all $(n_1, n_2)$ not in $E$ |

## 3. User Documentation

Basic usage:

```bash
python3 main.py [-h] [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v]
```

**Command-line options:**

- **-i INPUT, --input INPUT**:
  The instance input file. (Default: `complex.in`)
- **-o OUTPUT, --output OUTPUT**:
  Output file for the CNF formula in DIMACS format. (Default: `formula.cnf`)
- **-s SOLVER, --solver SOLVER**:
  Path to the SAT solver executable. (Default: `./glucose-syrup`)
- **-v, --verb**:
  Enable verbose mode. Prints steps (Trying length...) and outputs solver statistics. (Default: Off).

### Example Usage

```
python3 main.py -i instances/small_pos_inst.in -v
```

```
python3 main.py -i instances/complex.in -o formula.cnf
```

## 4. Instances

1.  `complex.in`
2.  `small_neg_inst`
3.  `small_pos_inst`

---

### Instance Test Results

| Instance            | Solvable (SAT/UNSAT) | Time (s) | Max Length Tried |
| :------------------ | :------------------- | :------- | :--------------- |
| `complex.in`        | SAT                  | ~260.0 s | 57               |
| `small_neg_inst.in` | UNSAT                | 0.083 s  | 12               |
| `small_pos_inst.in` | SAT                  | 0.054 s  | 10               |
