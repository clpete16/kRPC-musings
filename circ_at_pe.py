import krpc
import math as m

from node_execution import execute_node

'''
Circularize the vehicle's orbit at the current periapse.
May be imported to simply create the node or ran directly
to perform the circularization.
'''

def circ_node_pe(conn):
    # Connect with KSP via kRPC
    vessel = conn.space_center.active_vessel
    pe = vessel.orbit.periapsis
    a = vessel.orbit.semi_major_axis

    # Delta-V using vis-viva, difference in orbital velocity before and after burn
    mu = vessel.orbit.body.gravitational_parameter
    vel_pe = m.sqrt(mu*((2 / pe) - (1 / a)))
    vel_circ = m.sqrt(mu / pe)
    dV = vel_circ - vel_pe

    # Create the node
    pe_time = conn.space_center.ut + vessel.orbit.time_to_periapsis
    return vessel.control.add_node(pe_time, dV, 0, 0)


def main(conn):
    circ_node_pe(conn)
    execute_node(conn)


if __name__ == "__main__":
    connection = krpc.connect(name="Node execution")
    main(connection)