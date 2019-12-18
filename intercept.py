import krpc
import math as m
import gauss_problem as gp

'''
Program to plan a Hohmann transfer to a target within the same SOI
VERY WIP
'''

# Values in meters, seconds, kg, radians unless otherwise specified
# 'mu' refers to gravitational parameter G*M
# 'nu' refers to True Anomaly
# 'ecc' refers to eccentricity
# 'r_' refers to radius
# 'a_' refers to semi-major axis
# 'w_' refers to angular velocity


def calc_eccentricity_transfer(ra, atx):
    # Eccentricity of the transfer orbit
    return 1 - ra / atx


def calc_true_anomaly(atx, ra, rb):
    ecc = calc_eccentricity_transfer(ra, atx)
    aa = atx*(1 - ecc**2) / rb
    return m.acos((aa - 1)/ecc)


def period(atx, mu):
    return 2*m.pi*m.sqrt(atx**3/mu)


def time_of_flight(ecc_anomaly, ecc, atx, mu):
    # Time of flight for orbit with ecc & atx across ecc_anomaly
    return (ecc_anomaly - ecc*m.sin(ecc_anomaly))*m.sqrt(atx**3 / mu)


def calc_eccentric_anomaly(nu, ecc):
    return m.acos((ecc + m.cos(nu))/(1 + ecc*m.cos(nu)))


def phase_angle(dNu, dt, wt):
    # state 1 == departure, state 2 == arrival
    # wt = angular velocity of target body to sun
    return dNu - wt*dt


def vis_viva(r, a, mu):
    # Orbital velocity equation
    return m.sqrt(mu*(2/r - 1/a))


def seconds_to_days(seconds):
    days = 0
    hours = 0
    minutes = 0

    seconds_in_min = 60
    seconds_in_hour = 60 * seconds_in_min
    seconds_in_day = 24 * seconds_in_hour
    
    while seconds > seconds_in_day:
        seconds -= seconds_in_day
        days += 1
    while seconds > seconds_in_hour:
        seconds -= seconds_in_hour
        hours += 1
    while seconds > seconds_in_min:
        seconds -= seconds_in_min
        minutes += 1
    seconds = round(seconds, 3)
    return (days, hours, minutes, seconds)


def print_days_format(ttp):
    print(
        "Time: " +
        str(ttp[0]) + " days, " +
        str(ttp[1]) + " hours, " + 
        str(ttp[2]) + " minutes, " +
        str(ttp[3]) + " seconds"
    )


def get_target_main_influence(conn):
    targ_body = conn.space_center.target_body
    targ_vess = conn.space_center.target_vessel
    if targ_body:
        return targ_body.orbit.body
    elif targ_vess:
        return targ_vess.orbit.body
    else:
        print('No target selected.')
        return False


def get_phase_angle(ra, rb, atx, mu, targ):
    ecc = calc_eccentricity_transfer(ra, atx)
    nu = calc_true_anomaly(atx, ra, rb)
    ecc_anomaly = calc_eccentric_anomaly(nu, ecc)
    TOF = time_of_flight(ecc_anomaly, ecc, atx, mu)

    wt = targ.angular_velocity
    wt = wt * m.pi / 180 / 3600 / 24 # rad / s

    print(m.degrees(phase_angle(nu, TOF, wt)))

if __name__ == "__main__":
    AU = 1.496 * 10**11
    mu = 1.327 * 10**20

    ra = 1 * AU
    rb = 1.524 * AU
    atx = 1.3 * AU
    
    ecc = calc_eccentricity_transfer(ra, atx)
    nu = calc_true_anomaly(atx, ra, rb)
    ecc_anomaly = calc_eccentric_anomaly(nu, ecc)
    TOF = time_of_flight(ecc_anomaly, ecc, atx, mu)
    print_days_format(seconds_to_days(TOF))

    wt = 0.5240 # degrees / day
    wt = wt * m.pi / 180 / 3600 / 24 # rad / s

    print(m.degrees(phase_angle(nu, TOF, wt)))

    t = 207 * 24 * 60 * 60                  # seconds
    r1_v = (0.473265, -0.899215, 0)         # AU
    r2_v = (0.066842, 1.561256, 0.030948)   # AU
    mu = 3.964016 * 10**-14                 # AU^3 / s^2
    orbit = gp.main(t, r1_v, r2_v, mu)