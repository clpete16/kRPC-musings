import krpc
import time
import math as m
import tkinter as tk

from node_execution import execute_node
from circ_at_ap import circ_node_ap
from GUI import yn2tf, tf2yn
from stock_launch import launch_gui, get_resources, deploy_stuff

'''
Launch autopilot for a linearly staged launch vehicle.
May work for other vehicles with manual staging.
Configured for Real Solar System.
'''

FUEL_TYPES = ['SolidFuel','LiquidFuel','LqdHydrogen']


class ascent_parameters:
    def __init__(self,
                TARGET_AP = 250000,
                TARGET_INC = 0,
                TARGET_ROLL = 90,
                DO_STAGING = True,
                DEPLOY_SP_ANT = True,
                ):
        self.target_apoapsis = TARGET_AP
        self.target_inclination = TARGET_INC
        self.target_roll = TARGET_ROLL
        self.do_staging = DO_STAGING
        self.deploy_solar_panels_and_antennae = DEPLOY_SP_ANT
    

def main():
    conn = krpc.connect(name="LEO Auto-pilot")
    print('\n'*10)
    params = ascent_parameters()
    launch_gui(params)
    ascent(conn, params)


def ascent(conn, params):
    # Ascend to a sub-orbital trajectory with apoapsis TARGET_AP then circularize
    
    vessel = conn.space_center.active_vessel

    start_time = conn.space_center.ut

    # Activate ACS
    srf_frame = vessel.orbit.body.reference_frame
    ap = vessel.auto_pilot
    target_heading = 90 - params.target_inclination
    ap.target_pitch_and_heading(90,target_heading)
    ap.target_roll = params.target_roll
    ap.engage()

    # Launch!
    vessel.control.throttle = 1
    for i in range(3):
        print('T-'+str(3-i))
        time.sleep(1)
    print('Liftoff!')
    vessel.control.activate_next_stage()

    # Sub-orbital ascent parameters
    gravity_turn_1 = 30000
    gravity_turn_2 = 120000
    stage_num = 1
    fairingDeployed = False
    res_old = get_resources(vessel)
    time.sleep(0.5)

    while True:

        if conn.krpc.paused == True:
            continue

        alt = vessel.flight(srf_frame).mean_altitude
        apoap = vessel.orbit.apoapsis_altitude
        heat_flux = 0.001*vessel.flight(srf_frame).dynamic_pressure*vessel.flight(srf_frame).speed
        ut = conn.space_center.ut

        if ut < start_time:
            # Loaded a quicksave or reset the launch
            print("\nLaunch sequence interrupted!\n\n***ABORTING***\n")
            return

        # Stage when not thrusting (not consuming fuel)
        if params.do_staging:
            res = get_resources(vessel)
            any_consuming = False
            for i in range(len(FUEL_TYPES)):
                if vessel.resources.max(FUEL_TYPES[i]) > 0:
                    if res[i] < res_old[i]:
                        any_consuming = True
            if not any_consuming:
                conn.space_center.physics_warp_factor = 0
                time.sleep(0.2)
                print('Separating stage ' + str(stage_num) + '.')
                stage_num += 1
                vessel.control.activate_next_stage()
                time.sleep(0.2)
            res_old = res

        # Deploy fairings
        if alt > 110000 and heat_flux < 1135 and not fairingDeployed:
            for fairing in vessel.parts.fairings:
                fairing.jettison()
            fairingDeployed = True
        
        # Gravity Turns
        # To 45 degrees by turn 1 altitude until turn 2 altitude
        if alt < gravity_turn_1 and alt >= 300:
            ap.target_pitch_and_heading(85 - 40 * alt / gravity_turn_1, target_heading)
        # To 10 degrees by turn 2 altitude
        elif gravity_turn_2 > alt >= gravity_turn_1 and apoap < params.target_apoapsis:
            ap.target_pitch_and_heading(45 - 35 * (alt - gravity_turn_1) / (gravity_turn_2 - gravity_turn_1), target_heading)
        # hold 10 degrees
        elif alt >= gravity_turn_2 and apoap < params.target_apoapsis:
            ap.target_pitch_and_heading(10,target_heading)
        # Until target apoapsis reached
        elif apoap > params.target_apoapsis:
            vessel.control.throttle = 0
            break

        # Throttle back when nearing target apoapsis
        apoapse_error = abs(apoap - params.target_apoapsis)
        if apoapse_error < 1000:
            if conn.space_center.warp_rate != 1:
                conn.space_center.physics_warp_factor = 0
            vessel.control.throttle = max(0.25, apoapse_error / 500)

        time.sleep(0.1)

    if params.deploy_solar_panels_and_antennae:
        deploy_stuff(vessel)

    perform_circ_burn(conn)


def perform_circ_burn(conn):
    # Perform the circularization burn using the node_execution file

    vessel = conn.space_center.active_vessel
    vessel.control.rcs = True

    srf_frame = vessel.orbit.body.reference_frame
    alt = vessel.flight(srf_frame).mean_altitude
    node = circ_node_ap(conn)
    while alt < 140000:
        node.remove()
        node = circ_node_ap(conn)
        alt = vessel.flight(srf_frame).mean_altitude
        time.sleep(0.1)
    execute_node(conn)

    time.sleep(0.5)

    print('\nFinished!')
    print('Apoapse Altitude:',round(vessel.orbit.apoapsis_altitude))
    print('Periapse Altitude:',round(vessel.orbit.periapsis_altitude))
    print('Eccentricity:',round(vessel.orbit.eccentricity,4))
    print('Time elapsed:',round(vessel.met,1))
    print('\n')       


if __name__ == "__main__":
    main()