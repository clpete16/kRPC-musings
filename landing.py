# Landing using a PID controller

import tkinter as tk
import tkinter.ttk as ttk
import math
import krpc
import pid
import time
import random

'''
VERY WIP
'''

'''
Thoughts:
Merge telemetry class with spacecraft controls
Figure out how to raycast for radar altitude
Better attitude controls on descent
Enter velocity control mode when close to the ground
'''

'''
Assumptions:
Constant gravitational acceleration (maximum)
Constant engine ISP (minimum)
'''

class Telemetry:
    def __init__(self, conn, gui=False):
        self.gui = gui
        self.conn = conn
        self.vessel = conn.space_center.active_vessel
        self.body = self.vessel.orbit.body
        self.ap = self.vessel.auto_pilot

        self.g = self.body.surface_gravity
        self.isp = self.vessel.kerbin_sea_level_specific_impulse

        self.descending = False
        self.landed = False

        self.create_throttle_PID()
        self.main_control_loop()
        
    def update_telem(self):
        vessel = self.vessel
        body = self.body
        ref = body.reference_frame
        flight = vessel.flight(ref)

        self.vertical_speed = flight.vertical_speed
        self.horizontal_speed = flight.horizontal_speed

        self.lat = flight.latitude
        self.lon = flight.longitude
        
        self.surface_height = body.surface_height(self.lat, self.lon)
        box = vessel.bounding_box(vessel.reference_frame)
        self.altitude = box[0][1] + flight.mean_altitude - self.surface_height

        self.aero_forces = list(flight.aerodynamic_force)
        for i in range(len(self.aero_forces)):
            if math.isnan(self.aero_forces[i]):
                self.aero_forces[i] = 0
        self.max_thrust = vessel.available_thrust
        self.current_thrust = vessel.thrust
        self.throttle = vessel.control.throttle

        self.pitch = vessel.flight().pitch * math.pi / 180.0
        self.mass = vessel.mass

        if self.gui:
            self.gui.display_telemetry(self)

    def create_throttle_PID(self):
        # Throttle will be controlled based on the estimated burn altitude
        self.throttle_PID = pid.PID()
        self.throttle_PID.Kp = 0.025
        self.throttle_PID.Ki = 0.01
        self.throttle_PID.Kd = 0.001
        self.throttle_PID.clampLow = 0
        self.throttle_PID.clampHi = 1
        self.throttle_PID.clampI = 100

    def main_control_loop(self):
        while not self.landed:

            self.update_telem()

            burn_altitude = estimate_burn_altitude(self)
            if self.vertical_speed < -1 and self.altitude > 1:
                if burn_altitude > self.altitude:
                    self.descending = True
                    print('Estimated altitude: ' + str(burn_altitude))
                    print('Initiated at altitude: ' + str(self.altitude))
                    self.descent_control_loop()
            
            time.sleep(0.1)

    def descent_control_loop(self):
        final_descent = True
        while self.descending:
            
            self.update_telem()
            vessel = self.vessel

            if self.vertical_speed <= -10:
                burn_altitude = estimate_burn_altitude(self) + 1
                vessel.control.throttle = self.throttle_PID.update(self.altitude - burn_altitude)
                point_retro_final_descent(self.conn)

            elif self.vertical_speed > -10:
                if final_descent:
                    vessel.auto_pilot.reference_frame = vessel.surface_reference_frame
                    vessel.auto_pilot.target_direction = (1, 0, 0)
                    self.throttle_PID.set_setpoint(-1)
                    self.throttle_PID.Kp = 0.4
                    self.throttle_PID.Kd = 0.05
                    final_descent = False
    
                vessel.control.throttle = self.throttle_PID.update(self.vertical_speed)

            if self.altitude < 0 or vessel.situation == 'landed' or self.vertical_speed > 0:
                print("Impact velocity: " + str(self.vertical_speed))
                self.descending = False
                self.landed = True
                vessel.control.throttle = 0
                vessel.control.rcs = False

            time.sleep(0.1)
        
        self.main_control_loop()


class GUI:
    def __init__(self, conn):
        self.conn = conn
        self.root = tk.Tk()
        root = self.root
        root.title('Landing GUI')
        root.resizable(width=False, height=False)

        # Makes [x] button do quitApp first
        root.protocol('WM_DELETE_WINDOW', self.quitApp)

        # Left Frame, holds general commands
        self.leftFrame = tk.Frame(root)
        lf = self.leftFrame
        lf.grid(row=0, column=0)

        # Right Frame, holds information
        self.rightFrame = tk.Frame(root)
        rf = self.rightFrame
        rf.grid(row = 0, column=2)

        # Bottom Frame, holds primary info readout (countdown, warnings, etc.)
        self.bottomFrame = tk.Frame(root)
        bf = self.bottomFrame
        bf.grid(row = 2, column = 0, columnspan=3)

        # The following are static
        ttk.Separator(root, orient='vertical').grid(row=0, column=1, sticky='ns')
        ttk.Separator(root, orient='horizontal').grid(row=1, column = 0, columnspan=3, sticky='ew')
        tk.Label(lf, text="Commands:", width=30).pack(side='top')

        # Commands
        tk.Button(lf, text="Reset", command = lambda: self.reset_parameters()).pack()

        # Telemetry
        tk.Label(rf, text="Burn at altitude:").grid(row=0, column=0)
        tk.Label(rf, text="Burn time:").grid(row=0, column=1)
        tk.Label(rf, text="Horizontal Velocity:").grid(row=2, column=0)       
        tk.Label(rf, text="Vertical Velocity:").grid(row=2, column=1)
        tk.Label(rf, text="Throttle:").grid(row=4, column=0) 
        tk.Label(rf, text="Altitude:").grid(row=5, column=0)

        self.est_burn_height_out = tk.Label(rf)
        self.est_burn_time_out = tk.Label(rf)
        self.horizontal_vel_out = tk.Label(rf)
        self.vertical_vel_out = tk.Label(rf)
        self.throttle_out = tk.Label(rf)
        self.altitude_out = tk.Label(rf)

    def display_telemetry(self, telem):
        self.est_burn_height_out.configure(text=(str(round(estimate_burn_altitude(telem)+telem.surface_height)) + " m"))
        self.est_burn_height_out.grid(row=1, column=0)

        # self.est_burn_time_out.configure(text=(str(round(estimate_burn_time(telem), 1)) + " s"))
        self.est_burn_time_out.grid(row=1,column=1)

        self.horizontal_vel_out.configure(text=(str(round(telem.horizontal_speed)) + " m/s"))
        self.horizontal_vel_out.grid(row=3, column=0)

        self.vertical_vel_out.configure(text=(str(round(telem.vertical_speed)) + " m/s"))
        self.vertical_vel_out.grid(row=3,column=1)

        self.throttle_out.configure(text=(str(round(telem.throttle))))
        self.throttle_out.grid(row=4, column=1)

        self.altitude_out.configure(text=(str(round(telem.altitude)) + " m"))
        self.altitude_out.grid(row=5,column=1)

    def reset_parameters(self):
        self.quitApp()
        initiate_test(self.conn)
        self.__init__(self.conn)

    def quitApp(self):
        self.root.destroy()


def point_retro_final_descent(conn):
    vessel = conn.space_center.active_vessel
    ap = vessel.auto_pilot
    ap.reference_frame = vessel.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engage()


def estimate_burn_altitude(telem):
    # Estimate the burn altitude using kinematic equation V^2 = V0^2 + 2*a*h
    thrust_force = telem.max_thrust * math.sin(telem.pitch)
    acceleration = thrust_force / telem.mass - telem.g
    return 1.1*(telem.vertical_speed**2 - 0.5**2) / (2 * acceleration)


def initiate_test(conn):
    vessel = conn.space_center.active_vessel
    ap = vessel.auto_pilot
    ap.target_pitch_and_heading(90, 180)
    ap.engage()

    vessel.control.throttle = 1
    vessel.control.activate_next_stage()

    ref = vessel.orbit.body.reference_frame
    target_speed = random.randint(100,150)
    while vessel.flight(ref).vertical_speed < target_speed:
        pass

    vessel.control.throttle = 0
    vessel.control.rcs = True
    while vessel.flight(ref).vertical_speed > 0:
        ap.target_pitch = 90
    point_retro_final_descent(conn)


def main():
    conn = krpc.connect("GUI Program")
    global gui
    gui = GUI(conn)
    Telemetry(conn, gui)


if __name__ == "__main__":
    main()