import subprocess
from argparse import ArgumentParser


def parse_input(filename):
    """
    Reads a graph instance file and returns its properties.
    """
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
    """
    Maps a (node, position) pair to a unique integer variable ID.
    """
    return (node - 1) * length + pos


def encode(nodes, length, adj_matrix):
    """
    Encodes into a CNF Formula.
    """
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
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(f"p cnf {numb_vars} {len(clauses)}\n")
            for i in clauses:
                file.write(" ".join(map(str, i)) + "\n")
    except IOError as error:
        err_msg = f"Could not write CNF file to {output_file}, reason: {error}"
        print(err_msg)
        return "s UNKNOWN", err_msg

    cmd = [solver_path, "-model", output_file]

    verb_level = 1 if verbosity else 0
    cmd.append(f"-verb={verb_level}")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=600,  # 10 min without response
            check=False,
        )
        if result.returncode == 10 or result.returncode == 20:
            return result.stdout, result.stderr
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )
    except subprocess.CalledProcessError as error:
        err_msg = f"\nSolver crashed with code {error.returncode}\n--- Solver Stderr ---\n{error.stderr.strip()}"
        return "s UNKNOWN", err_msg
    except FileNotFoundError:
        err_msg = f"\nSolver executable not found at {solver_path}"
        return "s UNKNOWN", err_msg
    except subprocess.TimeoutExpired:
        err_msg = "\nSolver timed out after 10 minutes."
        return "s UNKNOWN", err_msg


def print_result(result_str, length):
    """
    Parses the SAT solver output to find & print the cycle.
    """
    lines = result_str.split("\n")
    sat = False
    model = []

    for line in lines:
        if line.startswith("s SATISFIABLE"):
            sat = True
        if line.startswith("v"):
            parts = line.strip().split()[1:]
            for p in parts:
                try:
                    val = int(p)
                    if val != 0:
                        model.append(val)
                except ValueError:
                    pass

    if not sat:
        return False
    # We have a SAT model to decode
    path = [0] * (length + 1)
    for val in model:
        if val > 0:
            tmp = val - 1
            node = (tmp // length) + 1
            pos = (tmp % length) + 1
            if pos <= length:
                path[pos] = node

    print("-" * 20)
    print(f"Found Cycle of Length {length}:")
    readable_path = " -> ".join(str(path[p]) for p in range(1, length + 1))
    print(f"{readable_path} -> {path[1]}")
    print("-" * 20)

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
    for i in range(nodes, target - 1, -1):
        if args.verb:
            print(f"Trying length {i}...", end=" ", flush=True)

        clauses, numb_vars = encode(
            nodes, i, adj_matrix
        )  # creating CNF Formula for length i

        result_str, stats_str = call_solver(
            clauses, numb_vars, args.output, args.solver, args.verb
        )

        if print_result(result_str, i):
            found = True

            if args.verb:
                print("\n=== Solver Statistics ===")
                for line in result_str.split("\n"):
                    if line.startswith("c "):
                        print(line)
                print("-------------------------")
            break  # Stop searching, we found the longest cycle >= target
        else:
            if args.verb:
                print("UNSAT")
                if stats_str and stats_str.strip():
                    print(stats_str.strip())

    if not found:
        print(f"\nNo simple cycle of length >= {target} exists")


if __name__ == "__main__":
    main()
