import krpc
import math as m
import gauss_problem as gp
import vector_math as vm
import time

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
    try:
        return m.acos((aa - 1)/ecc)
    except ValueError:
        # Floating point errors :(
        if (aa - 1) / ecc > 1:
            return 0
        elif (aa - 1) / ecc < -1:
            return m.pi


def calc_phase_angle(ra, rb, atx, mu, targ):
    # Angle which we should target to achieve a transfer
    nu = calc_true_anomaly(atx, ra, rb)
    TOF = time_of_flight(ra, rb, atx, mu)
    wt = 2 * m.pi / targ.orbit.period # rad / s
    return nu - wt*TOF


def time_of_flight(ra, rb, atx, mu):
    # Time of flight for orbit with ecc & atx across ecc_anomaly
    ecc = calc_eccentricity_transfer(ra, atx)
    nu = calc_true_anomaly(atx, ra, rb)
    ecc_anomaly = calc_eccentric_anomaly(nu, ecc)
    return (ecc_anomaly - ecc*m.sin(ecc_anomaly))*m.sqrt(atx**3 / mu)


def calc_eccentric_anomaly(nu, ecc):
    return m.acos((ecc + m.cos(nu))/(1 + ecc*m.cos(nu)))


def vis_viva(r, a, mu):
    # Orbital velocity equation
    return m.sqrt(mu*(2/r - 1/a))


def hyperbolic_excess_velocity(transfer, target, ref, ut):
    # Excess velocity upon arrival to a body in a different SOI
    target_velocity = target.velocity(ref)
    

def get_target_main_influence(conn):
    # Determine what body the target is orbiting and target type
    targ_body = conn.space_center.target_body
    targ_vess = conn.space_center.target_vessel
    if targ_body:
        return targ_body, "body"
    elif targ_vess:
        return targ_vess, "vessel"
    else:
        print('No target selected.')
        return False


def calc_transfer_date(ut, ref, vessel, targ, mu):
    '''
    Calculate the time after epoch of when the transfer should be initiated
    Currently really only works for orbits higher than the starting orbit
    Does not include plane changes
    '''
    timestep = vessel.orbit.period / 120 # Move 3 degrees at a time
    x = (1, 0, 0)
    refining = False

    start = time.time()

    while time.time() - start < 5:
        ra_vec = vessel.orbit.position_at(ut, ref)
        rb_vec = targ.orbit.position_at(ut, ref)

        # Get vessel and target angles relative to fixed point on orbiting body surface
        vessel_angle = vm.angle_between_vectors(x, ra_vec)
        if ra_vec[2] < 0:
            vessel_angle = 2 * m.pi - vessel_angle

        target_angle = vm.angle_between_vectors(x, rb_vec)
        if rb_vec[2] < 0:
            target_angle = 2 * m.pi - target_angle

        current_angle = target_angle - vessel_angle
        if current_angle < -m.pi:
            current_angle += 2 * m.pi

        # Get phase angle required for transfer
        ra = vm.magnitude(ra_vec)
        rb = vm.magnitude(rb_vec)
        atx = (ra + rb) / 2
        phase_angle = calc_phase_angle(ra, rb, atx, mu, targ)

        # Compare actual angle to phase angle
        diff = abs(phase_angle - current_angle)

        # If close, refine
        if not refining and diff <= m.pi / 60:
            refining = True
            ut -= 3*timestep
            timestep /= 30

        # If very close, return
        elif diff <= m.pi / 1800:
            return ut

        # Else keep looking
        ut += timestep
    
    print("Intercept calculator timed out.")


def main(conn):
    vessel = conn.space_center.active_vessel
    current_time = conn.space_center.ut

    if not get_target_main_influence(conn):
        return
    else:
        targ, targ_type = get_target_main_influence(conn)

    if targ.orbit.body == vessel.orbit.body:
        # Target and vessel share same orbiting body (LEO to Moon etc.)
        mu = vessel.orbit.body.gravitational_parameter
        ref_frame = vessel.orbit.body.reference_frame
        date = calc_transfer_date(current_time, ref_frame, vessel, targ, mu)
        
        ra_vec = vessel.orbit.position_at(date, ref_frame)
        rb_vec = targ.orbit.position_at(date, ref_frame)

        ra = vm.magnitude(ra_vec)
        rb = vm.magnitude(rb_vec)
        atx = (ra + rb) / 2

        dv1 = vis_viva(ra, atx, mu) - vis_viva(ra, vessel.orbit.semi_major_axis, mu)
        vessel.control.add_node(date, prograde=dv1)

        '''
        Include code to differentiate between vessels and bodies
        so that we do not transfer to the COM of bodies
        '''

    elif targ.orbit.body == vessel.orbit.body.orbit.body:
        # Target in same SOI as current orbiting planet
        # Should work for Moon to Earth or Earth to Mars etc.
        pass


if __name__ == "__main__":
    conn = krpc.connect(name="Interceptor")
    main(conn)