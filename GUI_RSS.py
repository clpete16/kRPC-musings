import GUI
import krpc
import rss_launch
import node_execution
import resonant_orbits
import intercept
import landing

from multiprocessing import Process

from circ_at_ap import circ_node_ap
from circ_at_pe import circ_node_pe

'''
Configured for Real Solar System
'''

def doAscent():
    print('Attempting ascent')
    try:
        ascent_process = Process(target=rss_launch.main)
        ascent_process.start()
    except:
        print('Ascent failed')


def doIntercept(conn):
    print('Attempting intercept')
    try:
        ascent_process = Process(target=intercept.main(conn))
        ascent_process.start()
    except:
        print('Intercept failed')


def doExecuteNode():
    print('Attempting node execution')
    try:
        node_process = Process(target=node_execution.main)
        node_process.start()
    except:
        print('Execution failed')


def doCircNodePe(conn):
    circ_node_pe(conn)


def doCircNodeAp(conn):
    circ_node_ap(conn)


def doResonantOrbit():
    print('Attempting resonant orbit')
    try:
        node_process = Process(target=resonant_orbits.main)
        node_process.start()
    except:
        print('Execution failed')


def land():
    print('Attempting landing')
    try:
        landing_process = Process(target=landing.main)
        landing_process.start()
    except:
        print('Landing script failed')


def add_commands_to_gui(gui, conn):
    lf = gui.leftFrame
    GUI.addLabel(lf, "")
    GUI.addButton(lf, "Launch!", lambda: doAscent())
    GUI.addButton(lf, "Execute Node", lambda: doExecuteNode())
    GUI.addButton(lf, "Circularize at Periapsis", lambda: doCircNodePe(conn))
    GUI.addButton(lf, "Circularize at Apoapsis", lambda: doCircNodeAp(conn))
    GUI.addButton(lf, "Create resonant orbit", lambda: doResonantOrbit())
    GUI.addButton(lf, "Intercept a target", lambda: doIntercept(conn))
    GUI.addButton(lf, "Attempt a landing", lambda: land())
    GUI.addLabel(lf, "")


def main():
    conn = krpc.connect("GUI Program")
    global gui
    gui = GUI.GUI(conn)
    add_commands_to_gui(gui, conn)
    gui.root.title("kRPC GUI (Real Solar System)")
    gui.root.mainloop()


if __name__ == "__main__":
    main()