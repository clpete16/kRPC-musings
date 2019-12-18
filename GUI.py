import tkinter as tk
import tkinter.ttk as ttk

'''
Add sub-GUIs for each command that needs its own 
    parameters or readouts (launch, resonant orbits, etc.)
Add more things
'''

class Telemetry:
    def __init__(self, conn):
        try:
            vessel = conn.space_center.active_vessel
            flight = vessel.flight(vessel.orbit.body.reference_frame)
            self.apoapsis = vessel.orbit.apoapsis_altitude
            self.periapsis = vessel.orbit.periapsis_altitude
            self.time_to_apo = vessel.orbit.time_to_apoapsis
            self.time_to_peri = vessel.orbit.time_to_periapsis
            self.velocity = vessel.orbit.speed
            self.inclination = vessel.orbit.inclination*3.14153/180.0
            self.altitude = flight.mean_altitude
        except AttributeError:
            # Bullshit error for testing purposes
            raise ValueError

class GUI:
    def __init__(self, conn):
        self.conn = conn
        self.root = tk.Tk()
        root = self.root
        root.resizable(width=False, height=False)

        # Makes [x] button do quitApp first and keeps window on top
        root.protocol('WM_DELETE_WINDOW', self.quitApp)
        root.wm_attributes("-topmost", 1)

        # Left Frame, holds general commands
        self.leftFrame = tk.Frame(root)
        lf = self.leftFrame
        lf.grid(row=0, column=0)

        tk.Label(lf, text="Commands:", width=30).pack(side='top')

        # Right Frame, holds telemetry
        self.rightFrame = tk.Frame(root)
        rf = self.rightFrame
        rf.grid(row = 0, column=2)
        
        # Bottom Frame, holds messages (warnings, etc.)
        # Typical use is to hide message after being resolved using .grid_forget()
        self.bottomFrame = tk.Frame(root)
        bf = self.bottomFrame

        tk.Label(bf, text="").pack()
        self.message_label = tk.Label(bf)
        self.message_label.pack()

        # Static separators between frames
        ttk.Separator(root, orient='vertical').grid(row=0, column=1, sticky='ns')
        ttk.Separator(root, orient='horizontal').grid(row=1, column = 0, columnspan=3, sticky='ew')
        
        # Telemetry out
        tk.Label(rf, text="Apoapsis:").grid(row=0, column=0)
        self.apoapsis_readout = tk.Label(rf)
        self.apoapsis_readout.grid(row=1, column=0)

        tk.Label(rf, text="Time to Apoapsis:").grid(row=2, column=0)
        self.time_to_apoapsis_readout = tk.Label(rf)
        self.time_to_apoapsis_readout.grid(row=3,column=0)

        tk.Label(rf, text="Periapsis:").grid(row=0, column=1)
        self.periapsis_readout = tk.Label(rf)
        self.periapsis_readout.grid(row=1, column=1) 

        tk.Label(rf, text="Time to Periapsis:").grid(row=2, column=1)
        self.time_to_periapsis_readout = tk.Label(rf)
        self.time_to_periapsis_readout.grid(row=3, column=1)

        tk.Label(rf, text="Orbital Velocity:").grid(row=4, column=0)
        self.velocity_readout= tk.Label(rf)
        self.velocity_readout.grid(row=5, column=0)

        tk.Label(rf, text="Altitude:").grid(row=4, column=1)
        self.altitude_readout = tk.Label(rf)
        self.altitude_readout.grid(row=5, column=1)
        
        self.display_telemetry()
        
    def message(self, txt):
        # Send a message to the bottom message frame
        self.message_label.configure(text=txt)
        self.bottomFrame.grid(row = 2, column = 0, columnspan=3)

    def display_telemetry(self):
        conn = self.conn
        
        if conn.krpc.current_game_scene == conn.krpc.GameScene.flight:
            if updateTelemetry(conn):
                telem = updateTelemetry(conn)
                self.bottomFrame.grid_forget()

                self.apoapsis_readout.configure(text=m_to_xm(telem.apoapsis))
                self.time_to_apoapsis_readout.configure(text=(str(round(telem.time_to_apo,1)) + " s"))
                self.periapsis_readout.configure(text=m_to_xm(telem.periapsis))
                self.time_to_periapsis_readout.configure(text=(str(round(telem.time_to_peri,1)) + " s"))
                self.velocity_readout.configure(text=(str(round(telem.velocity,1)) + " m/s"))      
                self.altitude_readout.configure(text=m_to_xm(telem.altitude))
            else:
                self.message("Error updating telemetry.")
                self.display_telemetry_failure()
        else:
            self.display_telemetry_failure()
        
        self.root.after(100, self.display_telemetry)

    def display_telemetry_failure(self):
        self.apoapsis_readout.configure(text="N/A")
        self.time_to_apoapsis_readout.configure(text="N/A")
        self.periapsis_readout.configure(text="N/A")
        self.time_to_periapsis_readout.configure(text="N/A")
        self.velocity_readout.configure(text="N/A")  
        self.altitude_readout.configure(text="N/A")

    def quitApp(self):
        self.root.destroy()


def addButton(frame, txt, cmd):
    button = tk.Button(frame, text=txt, command=cmd)
    button.pack()


def addLabel(frame, txt):
    label = tk.Label(frame, text=txt)
    label.pack()


def m_to_xm(meters):
    # Convert meters to km if greater than 10 km
    if meters < 10000:
        return (str(round(meters)) + " m")
    elif 10000000 > meters >= 10000:
        meters /= 1000
        return (str(round(meters, 3)) + " km")
    elif meters >= 10000000:
        meters /= 1000000
        return (str(round(meters, 3)) + " Mm")


def yn2tf(string):
    # Convert yes, no to true, false
    string = string.lower()
    if int(string) == 1 or int(string) == 0:
        return int(string)
    elif string == 'y' or string == 'yes':
        return 1
    elif string == 'n' or string == 'no':
        return 0


def tf2yn(boolean):
    # Convert true, false to yes, no
    if boolean:
        return 'YES'
    if not boolean:
        return 'NO'


def updateTelemetry(conn):
    try:
        return Telemetry(conn)
    except:
        return False


if __name__ == "__main__":
    test = GUI(1)
    test.root.title("GUI Testing")
    test.root.mainloop()