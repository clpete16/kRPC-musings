import krpc
import math as m

from node_execution import execute_node

'''
Circularize the vehicle's orbit at the current apoapse.
May be imported to simply create the node or ran directly
to perform the circularization.
'''

def circ_node_ap(conn):
    # Connect with KSP via kRPC
    vessel = conn.space_center.active_vessel
    apoap = vessel.orbit.apoapsis
    a = vessel.orbit.semi_major_axis

    # Delta-V using vis-viva, difference in orbital velocity before and after burn
    mu = vessel.orbit.body.gravitational_parameter
    vel_ap = m.sqrt(mu*((2 / apoap) - (1 / a)))
    vel_circ = m.sqrt(mu / apoap)
    dV = vel_circ - vel_ap

    # Create the node
    ap_time = conn.space_center.ut + vessel.orbit.time_to_apoapsis
    return vessel.control.add_node(ap_time, dV, 0, 0)


def main(conn):
    circ_node_ap(conn)
    execute_node(conn)


if __name__ == "__main__":
    connection = krpc.connect(name="Node execution")
    main(connection)