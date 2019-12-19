import krpc

from stock_launch import launch_gui, get_resources, deploy_stuff, ascent, perform_circ_burn

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
    
        self.atmosphere_height = 140000
        self.gravity_turn_1 = 30000
        self.gravity_turn_2 = 120000
        self.minimum_angle = 10


def main():
    conn = krpc.connect(name="LEO Auto-pilot")
    print('\n'*10)
    params = ascent_parameters()
    launch_gui(params)
    ascent(conn, params)


if __name__ == "__main__":
    main()