import tkinter as tk
import tkinter.ttk as ttk

'''
Primary GUI to display telemetry and house commands
'''

# TO DO:
# Add dV etc. stats when in hangar
# Other stuff idk

INFO_FRAME = False

class Telemetry:
    def __init__(self, conn):
        vessel = conn.space_center.active_vessel
        flight = vessel.flight(vessel.orbit.body.reference_frame)
        self.apoapsis = vessel.orbit.apoapsis_altitude
        self.periapsis = vessel.orbit.periapsis_altitude
        self.time_to_apo = vessel.orbit.time_to_apoapsis
        self.time_to_peri = vessel.orbit.time_to_periapsis
        self.velocity = vessel.orbit.speed
        self.inclination = vessel.orbit.inclination * 3.14159265 / 180.0
        self.altitude = flight.mean_altitude


class GUI:
    def __init__(self, conn):
        self.conn = conn
        self.root = tk.Tk()
        root = self.root
        root.resizable(width=False, height=False)

        # Makes [x] button do quitApp first
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
        # Don't put into root yet, in case not showing telemetry
        
        # Bottom Frame, holds messages (warnings, etc.)
        # Typical use is to hide message after being resolved using .grid_forget()
        self.bottomFrame = tk.Frame(root)
        bf = self.bottomFrame

        tk.Label(bf, text="").pack()
        self.message_label = tk.Label(bf)
        self.message_label.pack()
        
        # Telemetry out
        tk.Label(rf, text="Apoapsis:").grid(row=0, column=0)
        self.apoapsis_readout = tk.Label(rf)
        self.apoapsis_readout.grid(row=0, column=1)

        tk.Label(rf, text="Time to Apoapsis:").grid(row=1, column=0)
        self.time_to_apoapsis_readout = tk.Label(rf)
        self.time_to_apoapsis_readout.grid(row=1,column=1)

        tk.Label(rf, text="Periapsis:").grid(row=2, column=0)
        self.periapsis_readout = tk.Label(rf)
        self.periapsis_readout.grid(row=2, column=1) 

        tk.Label(rf, text="Time to Periapsis:").grid(row=3, column=0)
        self.time_to_periapsis_readout = tk.Label(rf)
        self.time_to_periapsis_readout.grid(row=3, column=1)

        tk.Label(rf, text="Orbital Velocity:").grid(row=4, column=0)
        self.velocity_readout= tk.Label(rf)
        self.velocity_readout.grid(row=4, column=1)

        tk.Label(rf, text="Altitude:").grid(row=5, column=0)
        self.altitude_readout = tk.Label(rf)
        self.altitude_readout.grid(row=5, column=1)
        
        if INFO_FRAME:
            # Draw the right telemetry frame
            rf.grid(row = 0, column=2)
            ttk.Separator(root, orient='vertical').grid(row=0, column=1, sticky='ns')
            ttk.Separator(root, orient='horizontal').grid(row=1, column = 0, columnspan=3, sticky='ew')
        self.showing = True
        self.refresh_gui()
        
    def message(self, txt):
        # Send a message to the bottom message frame
        self.message_label.configure(text=txt)
        self.bottomFrame.grid(row=2, column=0, columnspan=3)

    def refresh_gui(self):
        conn = self.conn

        if conn.krpc.current_game_scene == conn.krpc.GameScene.flight:
            self.bottomFrame.grid_forget()
            if not self.showing:
                self.root.deiconify()
                self.showing = True
            
        else:
            if self.showing:
                self.root.withdraw()
                self.showing = False
            self.apoapsis_readout.configure(text="N/A")
            self.time_to_apoapsis_readout.configure(text="N/A")
            self.periapsis_readout.configure(text="N/A")
            self.time_to_periapsis_readout.configure(text="N/A")
            self.velocity_readout.configure(text="N/A")  
            self.altitude_readout.configure(text="N/A")

        self.root.after(100, self.refresh_gui)

    def display_telemetry(self):
        conn = self.conn
        telem = Telemetry(conn)

        self.apoapsis_readout.configure(text=m_to_xm(telem.apoapsis))
        self.time_to_apoapsis_readout.configure(text=(str(round(telem.time_to_apo,1)) + " s"))
        self.periapsis_readout.configure(text=m_to_xm(telem.periapsis))
        self.time_to_periapsis_readout.configure(text=(str(round(telem.time_to_peri,1)) + " s"))
        self.velocity_readout.configure(text=(str(round(telem.velocity,1)) + " m/s"))      
        self.altitude_readout.configure(text=m_to_xm(telem.altitude))

    def quitApp(self):
        self.root.destroy()


def addButton(frame, txt, cmd):
    button = tk.Button(frame, text=txt, command=cmd)
    button.pack()


def addLabel(frame, txt):
    label = tk.Label(frame, text=txt)
    label.pack()


def m_to_xm(meters):
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
    try:
        return int(string)
    except ValueError:
        if string == 'y' or string == 'yes':
            return 1
        elif string == 'n' or string == 'no':
            return 0


def tf2yn(boolean):
    # Convert true, false to yes, no
    if boolean:
        return 'YES'
    if not boolean:
        return 'NO'


if __name__ == "__main__":
    test = GUI(1)
    test.root.title("GUI Testing")
    test.root.mainloop()