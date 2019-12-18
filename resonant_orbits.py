import math as m
import tkinter as tk
import krpc
import time

from node_execution import execute_node
from GUI import yn2tf, tf2yn

'''
Automatically insert a craft containing n satellites into a
synchronous orbit for relay creation
'''

class resonant_parameters(object):
    def __init__(self,
                num_sats = 3,
                insertion = True):

        # The number of satellites to deploy
        self.num_sats = num_sats

        '''
        Whether we are combining the insertion burn and resonant orbit
        Cheaper to insert at (n+1)/n compared (n-1)/n
        Usually only false if deploying around Kerbin/Earth 
        '''
        self.insertion = insertion

class resonant_gui:
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
        self.num_label = tk.Label(f, text="Number of satellites:")
        self.num_label.grid(row=row, column=0)
        self.num_input = tk.Entry(f)
        self.num_input.insert(0, params.num_sats)
        self.num_input.grid(row=row, column=1)
        row += 1

        self.insertion_label = tk.Label(f, text="Insertion burn? (Y/N):")
        self.insertion_label.grid(row=row, column=0)
        self.insertion_input = tk.Entry(f)
        self.insertion_input.insert(0, params.insertion)
        self.insertion_input.grid(row=row, column=1)
        row += 1

        self.confirm_button = tk.Button(f, text="Create maneuver", command=self.sendParams)
        self.confirm_button.grid(row=row, column=0, columnspan=2)

        root.mainloop()

    def sendParams(self):
        p = self.params
        p.num_sats = float(self.num_input.get())
        p.insertion = yn2tf(self.insertion_input.get())
        self.root.destroy()


def main():
    connection = krpc.connect(name="Relay Auto-pilot")
    mission_parameters = resonant_parameters()
    resonant_gui(mission_parameters)
    set_resonant_orbit(connection, mission_parameters)


def calc_insertion_burn(conn, params):
    '''
    Insert the main craft into a resonant orbit to target orbit
    '''
    # Connect to KSP
    scen = conn.space_center
    vessel = scen.active_vessel

    mu = vessel.orbit.body.gravitational_parameter
    ut = scen.ut

    if params.insertion == True:
        '''
        Burn at periapsis to an orbit with 
        period = (n+1)/n * the target period
        assuming the target orbit is circular with r = periapsis
        '''
        periapsis = vessel.orbit.periapsis
        
        T_circ = 2 * m.pi * m.sqrt( periapsis**3 / mu )
        T_res = (params.num_sats + 1) / params.num_sats * T_circ

        a1 = vessel.orbit.semi_major_axis
        v1 = m.sqrt(mu * (2 / periapsis - 1 / a1))

        a2 = (mu * (T_res / 2 / m.pi)**2)**(1 / 3)
        v2 = m.sqrt(mu * (2 / periapsis - 1 / a2))

        vessel.control.add_node(ut + vessel.orbit.time_to_periapsis, 
                                prograde=(v2-v1))

    elif params.insertion == False:
        '''
        Burn at apoapsis to an orbit with 
        period = (n-1)/n * target period
        assuming the target orbit is circular with r = apoapsis
        '''
        apoapsis = vessel.orbit.apoapsis

        T_circ = 2 * m.pi * m.sqrt(apoapsis**3 / mu)
        T_res = (params.num_sats - 1) / params.num_sats * T_circ

        a1 = vessel.orbit.semi_major_axis
        v1 = m.sqrt(mu * (2 / apoapsis - 1 / a1))

        a2 = (mu * (T_res / 2 / m.pi)**2)**(1 / 3)
        v2 = m.sqrt(mu * (1 / a2))

        vessel.control.add_node(ut + vessel.orbit.time_to_apoapsis, 
                                prograde=(v2-v1))


def set_resonant_orbit(conn, params):
    calc_insertion_burn(conn, params)


if __name__ == "__main__" : 
    main()
    execute_node(conn)