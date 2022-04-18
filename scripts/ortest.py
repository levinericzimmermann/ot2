from ortools.sat.python import cp_model

model = cp_model.CpModel()

num_vals = 3
x = model.NewIntVar(0, num_vals - 1, 'x')
y = model.NewIntVar(0, num_vals - 1, 'y')
z = model.NewIntVar(0, 2, 'z')

model.Add(x != y)
model.Add([x, y][z] != 0)


solver = cp_model.CpSolver()
status = solver.Solve(model)
