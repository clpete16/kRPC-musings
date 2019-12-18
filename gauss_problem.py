import math as m
import time
from vector_math import *

'''
Requires inputs:
r1_v & r2_v, position vectors of departure and arrival (Earth, Mars, etc.)
dNu, true anomaly between positions
t, time of flight
mu, standard gravitational parameter of primary transfer influencer
'''

'''
All math described here
http://www.braeunig.us/space/interpl.htm

1) Evaluate the constants k, l, and m from r1, r2 and using equations 
    (5.9) through (5.11).
2) Determine the limits on the possible values of p by evaluating 
    pi and pii from equations (5.18) and (5.19).
3) Pick a trial value of p within the appropriate limits.
4) Using the trial value of p, solve for a from equation (5.12). 
    The type conic orbit will be known from the value of a.
5) Solve for f, g and fdot from equations (5.5), (5.6) and (5.7).
6) Solve for dE or dF, as appropriate, using equations (5.13) and (5.14)
    or equation (5.15).
7) Solve for t from equation (5.16) or (5.17) and compare it with 
    the desired time-of-flight.
8) Adjust the trial value of p using one of the iteration methods 
    discussed above until the desired time-of-flight is obtained.
9) Evaluate gdot from equation (5.8) and then solve for v1 and v2 using 
    equations (5.3) and (5.4).
'''


class TransferOrbit:
    def __init__(self,
                tof = 0,
                r1_vec = (0, 0, 0),
                r2_vec = (0, 0, 0),
                mu = 1.327*10**20,
                arg_peri = 0,
                inc = 0,
                long_asc_node = 0,
                sma = 0,
                ecc = 0,
                t_peri = 0,
                v1_vec = (0, 0, 0),
                v2_vec = (0, 0, 0)
                ):
        
        # Given
        self.r1_vec = r1_vec
        self.r2_vec = r2_vec 
        self.time_of_flight = tof
        self.mu = mu

        # Gauss/Lambert solve
        self.v1_vec = v1_vec
        self.v2_vec = v2_vec

        # Find via r1, v1
        self.argument_of_periapsis = arg_peri
        self.inclination = inc
        self.longitude_of_ascending_node = long_asc_node
        self.semi_major_axis = sma
        self.eccentricity = ecc
        self.time_of_periapsis = t_peri
        


def v1(r1_v, r2_v, f, g):
    # Eq 3
    one = (r2_v[0] - f*r1_v[0]) / g
    two = (r2_v[1] - f*r1_v[1]) / g
    three = (r2_v[2] - f*r1_v[2]) / g
    return (one, two, three)


def v2(fdot, gdot, r1_v, v1_v):
    # Eq 4
    one = fdot*r1_v[0] + gdot*v1_v[0]
    two = fdot*r1_v[1] + gdot*v1_v[1]
    three = fdot*r1_v[2] + gdot*v1_v[2]
    return (one, two, three)


def f_nu(r2, p, dNu):
    # Eq 5a
    return 1 - r2 / p * (1 - m.cos(dNu))


def fdot_nu(mu, p, dNu, r1, r2):
    # Eq 7a
    a = m.sqrt(mu / p)
    b = m.tan(dNu / 2)
    c = (1 - m.cos(dNu)) / p - 1 / r1 - 1 / r2
    return a*b*c


def g_nu(r1, r2, dNu, mu, p):
    # Eq 6a
    return r1 * r2 * m.sin(dNu) / m.sqrt(mu * p)


def gdot_nu(r1, p, dNu):
    # Eq 8a
    return 1 - r1 / p * (1 - m.cos(dNu))


def k_func(r1, r2, dNu):
    # Eq 9
    return r1 * r2 * (1 - m.cos(dNu))


def l_func(r1, r2):
    # Eq 10
    return r1 + r2


def m_func(r1, r2, dNu):
    # Eq 11
    return r1 * r2 * (1 + m.cos(dNu))


def sma(k, l, m, p):
    # Eq 12
    return m * k * p / ((2*m - l**2) * p**2 + 2 * k * l * p - k**2)


def E_ellipt_cos(r1, a, f):
    # Eq 13
    return m.acos(1 - r1 / a * (1 - f))


def F_hyperb_cosh(r1, a, f):
    # Eq 15
    return m.acosh(1 - r1 / a * (1 - f))


def t_ellipt(g, a, mu, dE):
    # Eq 16
    return g + m.sqrt(a**3 / mu) * (dE - m.sin(dE))


def t_hyperb(g, a, mu, dF):
    # Eq 17
    return g + m.sqrt((-a)**3 / mu) * (m.sinh(dF) - dF)


def p_i(k, l, m_func):
    # Eq 18
    return k / (l + m.sqrt(2 * m_func))


def p_ii(k, l, m_func):
    # Eq 19
    return k / (l - m.sqrt(2 * m_func))


def p_next(p_current, p_prev, t_goal, t_current, t_prev):
    # Eq 20
    return p_current + (t_goal - t_current) * (p_current - p_prev) / (t_current - t_prev)


def check_p_value(p, k, l, m, r1, r2, mu, dNu):
    a_val = sma(k, l, m, p)
    f = f_nu(r2, p, dNu)
    g = g_nu(r1, r2, dNu, mu, p)
    fdot = fdot_nu(mu, p, dNu, r1, r2)

    if a_val > 0:
        dE = E_ellipt_cos(r1, a_val, f)
        t = t_ellipt(g, a_val, mu, dE)

    elif a_val < 0:
        dF = F_hyperb_cosh(r1, a_val, f)
        t = t_hyperb(g, a_val, mu, dF)

    return t


def find_orbital_elements(orbit):
    x = (1, 0, 0)
    y = (0, 1, 0)
    z = (0, 0, 1)

    h_vec = cross_product(orbit.r1_vec, orbit.r2_vec)

    e_vec = scalar_multiplication((orbit.v1_val**2 - orbit.mu / orbit.r1_val), orbit.r1_vec)
    e_vec = vector_subtraction(e_vec, scalar_multiplication(dot_product(orbit.r1_vec, orbit.v1_vec), orbit.v1_vec))
    e_vec = scalar_multiplication(1 / orbit.mu, e_vec)

    n_vec = cross_product(z, h_vec)

    orbit.inclination = m.acos(dot_product(z, h_vec) / magnitude(h_vec))

    raan = m.acos(dot_product(x, n_vec) / magnitude(n_vec))
    if n_vec[1] < 0:
        raan = 2*m.pi - raan
    orbit.longitude_of_ascending_node = raan

    arg_peri = m.acos(dot_product(n_vec, e_vec) / (magnitude(n_vec)*magnitude(e_vec)))
    if e_vec[2] < 0:
        arg_peri = 2*m.pi - arg_peri
    orbit.argument_of_periapsis = arg_peri

    orbit.true_anomaly_at_epoch = m.acos(dot_product(e_vec, orbit.r1_vec) / (magnitude(e_vec)*orbit.r1_val))


def main(t, r1_v, r2_v, mu):
    new_transfer_orbit = TransferOrbit()

    new_transfer_orbit.r1_vec = r1_v
    new_transfer_orbit.r1_val = magnitude(r1_v)
    new_transfer_orbit.r2_vec = r2_v
    new_transfer_orbit.r2_val = magnitude(r2_v)
    new_transfer_orbit.mu = mu

    r1 = magnitude(r1_v)
    r2 = magnitude(r2_v)

    dNu = m.acos(dot_product(r1_v, r2_v) / (r1 * r2))

    k_val = k_func(r1, r2, dNu)
    l_val = l_func(r1, r2)
    m_val = m_func(r1, r2, dNu)

    if dNu < m.pi:
        # p_i < p < inf
        p_i_val = p_i(k_val, l_val, m_val)
        p_max = m.inf
        p_current = 1.25*p_i_val
        p_prev = 1.5*p_i_val

    elif dNu > m.pi:
        # 0 < p < p_ii
        p_ii_val = p_ii(k_val, l_val, m_val)
        p_min = 0
        p_current = 0.75*p_ii_val
        p_prev = 0.5*p_ii_val

    t_current = check_p_value(p_current, k_val, l_val, m_val, r1, r2, mu, dNu)
    t_prev = check_p_value(p_prev, k_val, l_val, m_val, r1, r2, mu, dNu)
    t_diff = abs(t_current - t)

    while t_diff > 1:
        p_next_val = p_next(p_current, p_prev, t, t_current, t_prev)
        t_next = check_p_value(p_next_val, k_val, l_val, m_val, r1, r2, mu, dNu)
        t_diff = abs(t_current - t_next)

        t_prev = t_current
        p_prev = p_current

        t_current = t_next
        p_current = p_next_val
        
    p_val = p_current
    a_val = sma(k_val, l_val, m_val, p_val)

    new_transfer_orbit.semi_major_axis = a_val
    new_transfer_orbit.eccentricity = m.sqrt(1 - p_val / a_val)

    f_val = f_nu(r2, p_val, dNu)
    g_val = g_nu(r1, r2, dNu, mu, p_val)
    fdot_val = fdot_nu(mu, p_val, dNu, r1, r2)
    gdot_val = gdot_nu(r1, p_val, dNu)

    v1_vec = v1(r1_v, r2_v, f_val, g_val)
    v2_vec = v2(fdot_val, gdot_val, r1_v, v1_vec)

    new_transfer_orbit.v1_vec = v1_vec
    new_transfer_orbit.v1_val = magnitude(v1_vec)
    new_transfer_orbit.v2_vec = v2_vec
    new_transfer_orbit.v2_val = magnitude(v2_vec)

    # find_orbital_elements(new_transfer_orbit)

    return new_transfer_orbit


if __name__ == "__main__":
    # http://www.braeunig.us/space/problem.htm#5.3

    start = time.time()

    for i in range(100000):
        t = 207 * 24 * 60 * 60                  # seconds
        r1_v = (0.473265, -0.899215, 0)         # AU
        r2_v = (0.066842, 1.561256, 0.030948)   # AU
        mu = 3.964016 * 10**-14                 # AU^3 / s^2
        orbit = main(t, r1_v, r2_v, mu)

    print(time.time() - start)