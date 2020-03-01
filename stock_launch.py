import krpc
import time
import math as m
import tkinter as tk

from node_execution import execute_node
from circ_at_ap import circ_node_ap
from GUI import yn2tf, tf2yn

'''
Launch Auto Pilot for a linearly staged launch vehicle.
Will also assume that the first stage may have SRBs.
Should work for other vehicles with manual staging.
Configured for Stock Solar System.
'''

'''
TO DO
PID / More robust altitude control
PID / More robust inclination control
'''

FUEL_TYPES = ['SolidFuel','LiquidFuel']


class ascent_parameters:
    def __init__(self,
                TARGET_AP = 100000,
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

        self.atmosphere_height = 70000
        self.gravity_turn_1 = 22000
        self.gravity_turn_2 = 50000
        self.minimum_angle = 0


class launch_gui:
    def __init__(self, params):
        self.params = params
        self.root = tk.Tk()
        root = self.root

        root.title("Launch parameters")
        root.resizable(width=False, height=False)
        root.protocol('WM_DELETE_WINDOW', self.sendParams)

        self.frame = tk.Frame(root)
        f = self.frame
        f.pack()

        self.title = tk.Label(f, text='Please enter the target orbital parameters')
        self.title.grid(row=0, column=0, columnspan=2)

        row = 1
        self.target_ap_label = tk.Label(f, text="Target Apoapsis (m):")
        self.target_ap_label.grid(row=row, column=0)
        self.target_ap_input = tk.Entry(f)
        self.target_ap_input.insert(0, params.target_apoapsis)
        self.target_ap_input.grid(row=row, column=1)
        row += 1

        self.target_inc_label = tk.Label(f, text="Target Inclination (deg):")
        self.target_inc_label.grid(row=row, column=0)
        self.target_inc_input = tk.Entry(f)
        self.target_inc_input.insert(0, params.target_inclination)
        self.target_inc_input.grid(row=row, column=1)
        row += 1

        self.target_roll_label = tk.Label(f, text="Target Roll (deg):")
        self.target_roll_label.grid(row=row, column=0)
        self.target_roll_input = tk.Entry(f)
        self.target_roll_input.insert(0, params.target_roll)
        self.target_roll_input.grid(row=row, column=1)
        row += 1

        self.stage_label = tk.Label(f, text="Do staging? (Y/N):")
        self.stage_label.grid(row=row, column=0)
        self.stage_input = tk.Entry(f)
        self.stage_input.insert(0, tf2yn(params.do_staging))
        self.stage_input.grid(row=row, column=1)
        row += 1

        self.deploy_label = tk.Label(f, text="Deploy solar panels? (Y/N):")
        self.deploy_label.grid(row=row, column=0)
        self.deploy_input = tk.Entry(f)
        self.deploy_input.insert(0, tf2yn(params.deploy_solar_panels_and_antennae))
        self.deploy_input.grid(row=row, column=1)
        row += 1

        self.confirm_button = tk.Button(f, text="Confirm and launch!", command=self.sendParams)
        self.confirm_button.grid(row=row, column=0, columnspan=2)

        root.mainloop()

    def sendParams(self):
        p = self.params
        p.target_apoapsis = float(self.target_ap_input.get())
        p.target_inclination = float(self.target_inc_input.get())
        p.target_roll = float(self.target_roll_input.get())
        p.do_staging = yn2tf(self.stage_input.get())
        p.deploy_solar_panels_and_antennae = yn2tf(self.deploy_input.get())
        self.root.destroy() 
    

def main():
    conn = krpc.connect(name="LEO Auto-pilot")
    print('\n'*10)
    params = ascent_parameters()
    launch_gui(params)
    ascent(conn, params)


def get_resources(vessel):
    # Get the amount of solid and liquid fuel left in the craft
    res = []
    for fuel in FUEL_TYPES:
        res.append(vessel.resources.amount(fuel))
    return res


def ascent(conn, params):
    # Ascend to a sub-orbital trajectory with apoapsis TARGET_AP then circularize
    
    vessel = conn.space_center.active_vessel
    start_time = conn.space_center.ut

    # Activate ACS
    srf_frame = vessel.orbit.body.reference_frame
    ap = vessel.auto_pilot
    target_heading = 90 - params.target_inclination
    ap.target_pitch_and_heading(90, target_heading)
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
    gravity_turn_1 = params.gravity_turn_1
    gravity_turn_2 = params.gravity_turn_2
    fairingDeployed = False
    res_old = get_resources(vessel)
    time.sleep(0.5)

    if vessel.resources.max('SolidFuel') > 0:
        srbDeployed = False
    else:
        srbDeployed = True

    while True:

        if conn.krpc.paused == True:
            continue

        alt = vessel.flight(srf_frame).mean_altitude
        apoap = vessel.orbit.apoapsis_altitude
        ut = conn.space_center.ut
        inc = vessel.orbit.inclination / m.pi * 180

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
            if not srbDeployed and res[0] ==  res_old[0]:
                any_consuming = False
                srbDeployed = True
            if not any_consuming:
                conn.space_center.physics_warp_factor = 0
                time.sleep(0.2)
                vessel.control.activate_next_stage()
                time.sleep(0.2)
            res_old = res

        # Deploy fairings
        if alt > 5 / 7 * params.atmosphere_height and not fairingDeployed:
            for fairing in vessel.parts.fairings:
                fairing.jettison()
            fairingDeployed = True

        # Deploy sp & ant
        if alt > params.atmosphere_height and params.deploy_solar_panels_and_antennae:
            deploy_stuff(vessel)
        
        # Gravity Turns
        # To 45 degrees by turn 1 altitude until turn 2 altitude
        if alt < gravity_turn_1 and alt >= 300:
            ap.target_pitch = 85 - 40 * alt / gravity_turn_1
        # To 5 degrees by turn 2 altitude
        elif gravity_turn_2 > alt >= gravity_turn_1 and apoap < params.target_apoapsis:
            ap.target_pitch = 45 - (45 - params.minimum_angle) * (alt - gravity_turn_1) / (gravity_turn_2 - gravity_turn_1)
        # hold 5 degrees
        elif alt >= gravity_turn_2 and apoap < params.target_apoapsis:
            ap.target_pitch = params.minimum_angle
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

        # Adjust to target inclination
        inclination_diff = inc - params.target_inclination
        if inclination_diff > 0.05:
            # Overshot inclination
            ap.target_heading = 90 - params.target_inclination + min(8, inclination_diff) + 1
        elif inclination_diff < -0.05:
            # Undershot inclination
            ap.target_heading = 90 - params.target_inclination + max(-8, inclination_diff) - 1
        else:
            ap.target_heading = 90 - params.target_inclination

        time.sleep(0.1)

    if params.deploy_solar_panels_and_antennae:
        deploy_stuff(vessel)

    perform_circ_burn(conn, params)
    

def deploy_stuff(vessel):
    # Deploy solar panels and antennae
    try:
        vessel.control.solar_panels = True
    except:
        print('Solar panel(s) could not be deployed.')
    try:
        vessel.control.antennas = True
    except:
        print('Antenna(s) could not be deployed.')


def perform_circ_burn(conn, params):
    # Perform the circularization burn using the node_execution file

    vessel = conn.space_center.active_vessel
    vessel.control.rcs = True

    srf_frame = vessel.orbit.body.reference_frame
    alt = vessel.flight(srf_frame).mean_altitude
    node = circ_node_ap(conn)
    while alt < params.atmosphere_height:
        node.remove()
        node = circ_node_ap(conn)
        alt = vessel.flight(srf_frame).mean_altitude
        time.sleep(0.1)
    execute_node(conn)

    time.sleep(0.5)

    print('\nFinished!')
    print('Apoapse Altitude:',round(vessel.orbit.apoapsis_altitude))
    print('Periapse Altitude:',round(vessel.orbit.periapsis_altitude))
    print('Eccentricity:',round(vessel.orbit.eccentricity, 4))
    print('Time elapsed:',round(vessel.met, 1))
    print('\n')       


if __name__ == "__main__":
    main()