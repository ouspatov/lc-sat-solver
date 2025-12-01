import subprocess
from argparse import ArgumentParser


def parse_input(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    header = lines[0].strip().split()
    nodes = int(header[0])
    target = int(header[2])

    adj_matrix = [[False for _ in range(nodes + 1)] for _ in range(nodes + 1)]
    # Iterate over edge lines
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) < 2:
            continue  # Skip any invalid lines

        u = int(parts[0])
        v = int(parts[1])

        adj_matrix[u][v] = True
        adj_matrix[v][u] = True

    return nodes, target, adj_matrix


def get_variable_id(node, pos, length):
    return (node - 1) * length + pos


def encode(nodes, length, adj_matrix):
    clauses = []

    def var(n, p):
        return get_variable_id(n, p, length)

    # Each position is occupied
    for p in range(1, length + 1):
        clause = []
        for n in range(1, nodes + 1):
            clause.append(var(n, p))
        clause.append(0)
        clauses.append(clause)

    # No two vertices in one position
    for p in range(1, length + 1):
        for n1 in range(1, nodes + 1):
            for n2 in range(n1 + 1, nodes + 1):
                clauses.append([-var(n1, p), -var(n2, p), 0])

    # No vertex appears twice
    for n in range(1, nodes + 1):
        for p1 in range(1, length + 1):
            for p2 in range(p1 + 1, length + 1):
                clauses.append([-var(n, p1), -var(n, p2), 0])

    # Adjacent positions are connected by an edge
    for p in range(1, length + 1):
        next_p = 1 if p == length else p + 1
        for n1 in range(1, nodes + 1):
            for n2 in range(1, nodes + 1):
                if n1 == n2:
                    continue
                if not adj_matrix[n1][n2]:
                    clauses.append([-var(n1, p), -var(n2, next_p), 0])

    numb_vars = nodes * length
    return clauses, numb_vars


def call_solver(clauses, numb_vars, output_file, solver_path, verbosity):
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(f"p cnf {numb_vars} {len(clauses)}\n")
        for i in clauses:
            file.write(" ".join(map(str, i)) + "\n")

    verb_level = "1" if verbosity else "0"

    return subprocess.run(
        [solver_path, "-model", "-verb=" + verb_level, output_file],
        stdout=subprocess.PIPE,
        check=False,
    )


def print_result(result, length):
    result_str = result.stdout.decode("utf-8")
    if result.returncode != 10:
        for line in result_str.split("\n"):
            print(line)

    if result.returncode == 20:  # returncode for UNSAT is 20
        return False

    if result.returncode != 10:  # returncode for SAT is 10
        print(f"\n[Solver Error: Exited with code {result.returncode}]")
        return False

    # Print all stats for SAT Case
    for line in result_str.split("\n"):
        print(line)

    model = []
    for line in result_str.split("\n"):
        if line.startswith("v"):  # Model line
            parts = line.strip().split()[1:]
            for p in parts:
                try:
                    val = int(p)
                    if val != 0:
                        model.append(val)
                except ValueError:
                    pass

    # SAT model to decode
    path = [0] * (length + 1)
    for val in model:
        if val > 0:
            tmp = val - 1
            node = (tmp // length) + 1
            pos = (tmp % length) + 1
            if pos <= length:
                path[pos] = node

    # Print the human-readable result
    print()
    print("-" * 20)
    print(f"Found Cycle of Length {length}:")
    readable_path = " -> ".join(str(path[p]) for p in range(1, length + 1))
    print(f"{readable_path} -> {path[1]}")
    print("-" * 20)
    print()

    return True


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "-i", "--input", default="./instances/complex.in", help="Instance File input"
    )
    parser.add_argument("-o", "--output", default="formula.cnf", help="CNF Output file")
    parser.add_argument(
        "-s", "--solver", default="./glucose-syrup", help="The SAT Solver to be used"
    )

    parser.add_argument(
        "-v",
        "--verb",
        action="store_true",
        default=False,
        help="Enable solver verbosity and output statistics",
    )

    args = parser.parse_args()

    # Parse input
    nodes, target, adj_matrix = parse_input(args.input)

    print(f"Graph with {nodes} nodes... Searching for cycle >= {target}...")

    # Interactive Searching
    found = False
    for i in range(nodes, target - 1, -1):  # start from the end
        if args.verb:
            print(f"Trying length {i}...", end=" ", flush=True)

        clauses, numb_vars = encode(
            nodes, i, adj_matrix
        )  # creating CNF Formula for length i

        result = call_solver(clauses, numb_vars, args.output, args.solver, args.verb)

        if print_result(result, i):
            found = True
            break
        else:
            if args.verb:
                print()

    if not found:
        print(f"\nNo simple cycle of length >= {target} exists")


if __name__ == "__main__":
    main()
