"""
Element verification against textbook closed-form natural frequencies.
Run: python fe_validate.py   (uses numpy assembly; elements from fe_elements.py)
"""
import numpy as np
import scipy.linalg as sla
import fe_elements as fe


def solve_gen(K, M, free):
    # Solve M v = mu K v with K positive-definite (mu = 1/omega^2). This is
    # robust when M is singular (massless rotational/drilling DOFs): such DOFs
    # give mu=0 (infinite frequency) and are simply dropped.
    Kf = np.asarray(K)[np.ix_(free, free)]
    Mf = np.asarray(M)[np.ix_(free, free)]
    mu = sla.eigh(Mf, Kf, eigvals_only=True)
    mu = mu[mu > 1e-14*mu.max()]
    f = 1.0/(2*np.pi*np.sqrt(mu))
    return np.sort(f)


def test_cantilever_beam():
    # steel rod, circular, clamped-free; compare 1st bending mode
    E = 210e9; rho = 7800.0; L = 1.0
    d = 0.02; A = np.pi/4*d**2; I = np.pi/64*d**4; J = np.pi/32*d**4
    G = E/(2*(1+0.3))
    n = 12
    nodes = np.array([[i*L/n, 0, 0] for i in range(n+1)])
    ndof = 6*(n+1)
    K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof))
    for e in range(n):
        Ke, Me, _ = fe.beam3d(nodes[e], nodes[e+1], E, A, I, I, J, G, rho)
        Ke = np.asarray(Ke); Me = np.asarray(Me)
        dofs = list(range(6*e, 6*e+6)) + list(range(6*(e+1), 6*(e+1)+6))
        for a in range(12):
            for b in range(12):
                K[dofs[a], dofs[b]] += Ke[a, b]
                M[dofs[a], dofs[b]] += Me[a, b]
    fixed = list(range(6))  # clamp node 0
    free = [d for d in range(ndof) if d not in fixed]
    f = solve_gen(K, M, free)
    f1 = f[f > 1e-3][0]
    beta = 1.875104
    f1_exact = beta**2/(2*np.pi*L**2)*np.sqrt(E*I/(rho*A))
    err = abs(f1-f1_exact)/f1_exact
    print(f"[beam] cantilever f1 = {f1:.4f} Hz  exact = {f1_exact:.4f} Hz  err = {err*100:.3f}%")
    assert err < 0.02, "beam f1 off"
    return err


def test_ss_plate():
    # simply-supported square plate, fundamental f11
    E = 68.9e9; nu = 0.33; rho = 2700.0; t = 0.005; Lp = 0.5
    N = 12  # elements per side
    xs = np.linspace(-Lp/2, Lp/2, N+1)
    ys = np.linspace(-Lp/2, Lp/2, N+1)
    nid = {}
    k = 0
    for j in range(N+1):
        for i in range(N+1):
            nid[(i, j)] = k; k += 1
    nn = k; ndof = 6*nn
    K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof))
    a_half = (xs[1]-xs[0])/2; b_half = (ys[1]-ys[0])/2
    Ke, Me = fe.shell4(a_half, b_half, E, nu, t, rho)
    for j in range(N):
        for i in range(N):
            ns = [nid[(i, j)], nid[(i+1, j)], nid[(i+1, j+1)], nid[(i, j+1)]]
            dofs = []
            for n_ in ns:
                dofs += list(range(6*n_, 6*n_+6))
            for a in range(24):
                for b in range(24):
                    K[dofs[a], dofs[b]] += Ke[a, b]
                    M[dofs[a], dofs[b]] += Me[a, b]
    # Validate the bending element in isolation: keep only plate DOFs
    # (w=2, rx=3, ry=4); membrane (u,v) has in-plane rigid-body modes that are
    # irrelevant here (the full hexapod constrains in-plane via the struts).
    # SS BC: w=0 on boundary nodes.
    fixed = set()
    for j in range(N+1):
        for i in range(N+1):
            if i in (0, N) or j in (0, N):
                fixed.add(6*nid[(i, j)]+2)
    free = []
    for n_ in range(nn):
        for off in (2, 3, 4):
            d = 6*n_+off
            if d not in fixed:
                free.append(d)
    f = solve_gen(K, M, free)
    f11 = f[f > 1e-2][0]
    D = E*t**3/(12*(1-nu**2))
    f11_exact = np.pi*(1/Lp**2)*np.sqrt(D/(rho*t))  # m=n=1 square SS
    err = abs(f11-f11_exact)/f11_exact
    print(f"[plate] SS f11 = {f11:.4f} Hz  exact = {f11_exact:.4f} Hz  err = {err*100:.3f}%")
    assert err < 0.05, "plate f11 off"
    return err


if __name__ == "__main__":
    test_cantilever_beam()
    test_ss_plate()
    print("element verification PASSED")
