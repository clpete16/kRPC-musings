import time
import krpc

'''
PID class derived from Art Whaley's example
'''

class PID(object):
    '''
    Generic PID Controller Class based on the PID recipe at :
    http://code.activestate.com/recipes/577231-discrete-pid-controller/

    and the code and discussions in the blog at:
    http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/
    
    '''  
    '''
    PID controllers are advanced ways to control 
    the input of a signal based on the output.

    P is a proportional output based on the error to the target value 
        and can function on its own (albeit not perfectly)
    I is the additive history of error (integral) and decreases response time
    D is the rate of change (derivative) of the input towards the target value
        and acts as a damper 

    The combination of P, I, and D values are modified by their respective gain
        values, and their sum is converted into the input signal. This signal 
        may be clamped by a set of simple comparisons based on physical or 
        design constraints. A perfectly tuned PID will rapidly approach the 
        target value without overshooting the value (increasing the error). 
        The designer may opt for a more rapid approach with acceptable overshoot, 
        or vice versa, by tuning the proper PID values.
    
    Control theory on choosing gain values intelligently, knowing whether the 
        gain values will produce a stable output, and in general smarter design 
        and implementation is based on the dynamics of the system.
    '''

    def __init__(self, P=1.0, I=0.1, D=0.01):   
        self.Kp = P     # Gain for proportional error
        self.Ki = I     # Gain for integral error
        self.Kd = D     # Gain for rate of change
        self.P = 0.0    # Value for proportional error
        self.I = 0.0    # Value for integral error
        self.D = 0.0    # Value for rate of change
        self.setpoint = 0.0  #Target value for controller
        self.clampI = 10.0
        self.clampHi = 1.0  #clamps i_term to prevent 'windup.'
        self.clampLow = -1.0
        self.lastTime = time.time()
        self.lastMeasure = 0.0
                
    def update(self, measure):
        # Update the values of P, I, and D corresponding to the change in error
        # achieved from the previous update

        now = time.time()
        change_in_time = now - self.lastTime
        # Avoid potential divide by zero if PID just created.
        if not change_in_time:
            change_in_time = 1.0   
       
        error = self.setpoint - measure
        self.P = error
        self.I += error
        self.I = self.clamp_i(self.I)
        self.D = (self.lastMeasure - measure) / (change_in_time)

        self.lastMeasure = measure
        self.lastTime = now

        output = (self.Kp * self.P) + (self.Ki * self.I) + (self.Kd * self.D)
        return self.clamp_output(output)

    def clamp_i(self, i):
        # Limit the integral value to prevent windup or down
        if i > self.clampI:
            return self.clampI
        elif i < -self.clampI:
            return -self.clampI
        else:
            return i

    def clamp_output(self, out):
        # Limit the output signal to within the low and high clamp values
        if out > self.clampHi:
            return self.clampHi
        elif out < self.clampLow:
            return self.clampLow
        else:
            return out
        
    def set_setpoint(self, value):
        # Set the target value of which the PID will attempt to reach
        self.setpoint = value
        self.I = 0.0