import re
import subprocess
import sys

class Solver():
    def __init__(self, ubcsat = "ubcsat"):
        self._ubcsat = ubcsat
        self._nvar = 0
        self._clauses = []
        self._soft_clauses = []

    def newvar(self):
        self._nvar += 1
        return self._nvar

    def add_clause(self, clause):
        self._clauses.append(clause)

    def add_soft_clause(self, clause, weight = 1):
        self._soft_clauses.append((weight, clause))

    def _write_wcnf(self, file):
        top = sum(w for w, _ in self._soft_clauses) + 1

        sys.stdout.write("p wcnf %d %d %d\n" % (self._nvar, len(self._clauses) + len(self._soft_clauses), top))
        sys.stdout.flush()

        file.write("p wcnf %d %d %d\n" % (self._nvar, len(self._clauses) + len(self._soft_clauses), top))
        for clause in self._clauses:
            file.write(str(top))
            for lit in clause:
                file.write(" ")
                file.write(str(lit))
            file.write(" 0\n")
        for w, clause in self._soft_clauses:
            file.write(str(w))
            for lit in clause:
                file.write(" ")
                file.write(str(lit))
            file.write(" 0\n")
        file.flush()

        return top

    def run(self):
        cmd = [self._ubcsat, "-w", "-alg", "irots", "-seed", "0", "-runs", "10", "-solve", "-r", "bestsol"]
        popen = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        top = self._write_wcnf(popen.stdin)
        try:
            for line in popen.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                m = re.match(r"^\d+ [01] (\d+) ([01]+)$", line)
                if m:
                    obj, model = m.groups()
                    obj = int(obj)
                    if obj < top:
                        model = [None] + [c=='1' for c in model]
                        yield (obj, model)
        finally:
            popen.terminate()

    def optimize(self):
        bestobj = None
        bestmodel = None
        for (obj, model) in self.run():
            if bestobj is None or obj < bestobj:
                bestobj, bestmodel = obj, model
        return bestobj, bestmodel

if __name__ == '__main__':
    solver = Solver()
    for i in xrange(4):
        solver.newvar()
    
    solver.add_clause([1, -2, 4])
    solver.add_clause([-1, -2, 3])
    solver.add_soft_clause([-2, -4], 8)
    solver.add_soft_clause([-3, 2], 4)
    solver.add_soft_clause([3, 1], 3)

    print(solver.optimize())
