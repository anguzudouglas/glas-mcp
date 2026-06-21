# Skill: math_calculate

**Tool:** `math_calculate`  
**Version:** 1.0.0

## Purpose
Execute any Python math code — arithmetic, algebra, calculus, statistics, linear algebra, numerical methods — and return results. The code runs in an isolated subprocess with a configurable timeout.

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `code` | string | **required** | Python math code to execute |
| `timeout` | integer | 15 | Clamped to 1–60 seconds |
| `precision` | integer | 50 | Decimal places for sympy/mpmath |

## Allowed Libraries

```
math, cmath, decimal, fractions, statistics, random,
itertools, functools, operator, collections, numbers,
numpy (as np), scipy, scipy.integrate, scipy.optimize,
scipy.linalg, scipy.stats, scipy.fft, scipy.special,
sympy (+ all common symbols pre-imported), mpmath
```

**Blocked:** `os`, `sys`, `subprocess`, `socket`, `open`, `exec`, `eval`, `__import__`, and all ML/deep-learning libraries.

## Code Patterns

### 1 — Show results with print()
```python
import numpy as np
x = np.linspace(0, 2*np.pi, 1000)
print(f"max sin = {np.max(np.sin(x)):.6f}")
print(f"integral approx = {np.trapz(np.sin(x), x):.6f}")
```

### 2 — Last expression is auto-captured as `result`
```python
import math
math.factorial(20)
# → result: "2432902008176640000"
```

### 3 — Symbolic math with sympy
```python
from sympy import symbols, integrate, sin, pi, simplify
x = symbols('x')
I = integrate(sin(x)**2, (x, 0, pi))
simplify(I)
# → result: "pi/2"
```

### 4 — Linear algebra
```python
import numpy as np
A = np.array([[4, 2], [1, 3]])
eigenvalues, eigenvectors = np.linalg.eig(A)
print("Eigenvalues:", eigenvalues)
print("Det:", np.linalg.det(A))
```

### 5 — Statistics
```python
from scipy import stats
data = [2.3, 4.1, 3.7, 5.2, 4.8, 3.1, 4.5]
print(f"mean = {stats.tmean(data):.3f}")
print(f"95% CI = {stats.t.interval(0.95, len(data)-1, loc=stats.tmean(data), scale=stats.sem(data))}")
```

### 6 — Numerical integration
```python
from scipy import integrate
import math
result, error = integrate.quad(lambda x: math.exp(-x**2), 0, float('inf'))
print(f"∫e^(-x²)dx [0,∞] = {result:.10f}  (√π/2 ≈ {math.sqrt(math.pi)/2:.10f})")
```

### 7 — Solving equations
```python
from sympy import symbols, solve, Eq
x, y = symbols('x y')
sols = solve([Eq(x**2 + y**2, 25), Eq(x + y, 7)], [x, y])
for s in sols:
    print(s)
```

## Output Fields

| Field | Description |
|-------|-------------|
| `success` | Whether execution completed without error |
| `output` | Everything printed to stdout |
| `result` | Value of the last expression (if any) |
| `error` | Error message / traceback (on failure) |
| `execution_time_ms` | Wall-clock time |

## Rules for Quality Code

1. **Always print() intermediate steps** for complex multi-stage calculations so the output is self-explanatory.
2. **Use descriptive variable names** — the output is returned to the user, not just to you.
3. **For large computations** (millions of iterations), check time complexity first and set `timeout` accordingly.
4. **Use sympy for exact answers**; use numpy/scipy for numerical approximations.
5. **Never hardcode paths or try to write files** — all I/O is blocked.
6. **For precision arithmetic** set `precision: 100` and use `mpmath` or `sympy.N(expr, 100)`.

## Timeout Guidelines

| Task | Suggested timeout |
|------|-------------------|
| Basic arithmetic | 5s (default works) |
| NumPy matrix ops | 10s |
| SciPy optimization | 20s |
| SymPy symbolic solve | 30s |
| Large Monte Carlo | 60s |
