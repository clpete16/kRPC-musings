import krpc
import math as m
import time

'''
Node execution script. Heavily borrowed from the example provided by Art Whaley
May be run directly or imported to be run at will by the program
'''

# TO DO:
# Improve burn time if need to stage during burn

def main():
    connection = krpc.connect(name="Node execution")
    execute_node(connection)


def get_node(vessel):
    try:
        node = vessel.control.nodes[0]
        return node
    except:
        print('\nNo node.')
        return False


def execute_node(conn):
    # Connect with KSP via kRPC
    scen = conn.space_center
    vessel = scen.active_vessel
    ap = vessel.auto_pilot

    if get_node(vessel):
        node = get_node(vessel)
    else:
        return

    # Orient to the node
    rf = vessel.orbit.body.reference_frame
    try:
        ap.sas = True
        time.sleep(0.1)
        ap.sas_mode = vessel.auto_pilot.sas_mode.maneuver
        using_SAS = True
    except:
        ap.reference_frame=rf
        ap.target_roll = float("nan")
        vessel.control.rcs = False
        ap.target_direction = node.remaining_burn_vector(rf)
        ap.engage()
        using_SAS = False

    time.sleep(0.25)
    while ap.error >= 1:
        if not get_node(vessel):
            print('Execution aborted.')
            return

    # Pass time until 10 second before the node
    burn_time = calc_burn_time(vessel, node)
    scen.warp_to(node.ut - (burn_time / 2.0) - 10.0)
    while node.time_to > (burn_time / 2.0):
        if not get_node(vessel):
            print('Execution aborted.')
            return
        if not using_SAS:
            ap.target_direction = node.remaining_burn_vector(rf)

    # Perform the burn. 
    # Stop if less than 0.005 m/s remaining, burning against node, or node deleted.
    dv_min = node.remaining_delta_v
    while node.remaining_delta_v > 0.005 and get_node(vessel):
        dv_min = min(node.remaining_delta_v, dv_min)
        try:
            acc = vessel.available_thrust / vessel.mass
            vessel.control.throttle = node.remaining_delta_v / acc
            if node.remaining_delta_v < 4 * acc and scen.warp_rate != 1:
                scen.physics_warp_factor = 0
        except ZeroDivisionError:
            # Zero acceleration == out of fuel
            vessel.control.activate_next_stage()
        if node.remaining_delta_v > 1.05*dv_min:
            break
        if not using_SAS:
            ap.target_direction = node.remaining_burn_vector(rf)
        time.sleep(0.05)
    
    # Clean up
    vessel.control.throttle = 0
    ap.disengage()
    vessel.control.sas = True
    node.remove()


def calc_burn_time(vessel, node):
    # Rearranged Tsiolkovsky Rocket Equation
    isp = vessel.specific_impulse
    mass = vessel.mass
    T = vessel.available_thrust
    g = 9.80665
    v_eq = isp*g
    return mass*v_eq/T*(1 - m.exp(-node.delta_v/(v_eq)))


if __name__ == "__main__" : 
    main()