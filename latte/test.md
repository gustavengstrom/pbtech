integrate --valuation=volume --cone-decompose manual.hrep.latte

integrate --valuation=volume --cone-decompose --vrep manual.vrep.latte


$p4 = new Polytope(INEQUALITIES=>[[0, 2, -1],[0, 1, 0],[1, -1, 0],[0, 0, 1],[1, 0, -1]]);


1 -1 1
1 0 -1
1 -1 -1
0 1 0
0 0 1


$m = new Polytope(INEQUALITIES=>[[1, -1, 0],[1, 0, -1],[1, -1, -1],[0, 1, 0],[0, 0, 1]]);
print_constraints($m->INEQUALITIES);
print $m->FACETS;

$m2 = new Polytope(INEQUALITIES=>[[1, -1, 0],[1, 0, -1],[1, -2, -1],[0, 1, 0],[0, 0, 1]]);
print_constraints($m2->INEQUALITIES);