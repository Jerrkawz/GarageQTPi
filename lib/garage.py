import time
import RPi.GPIO as GPIO
import datetime
from lib.eventhook import EventHook


SHORT_WAIT = .2 #S (200ms)
"""
    The purpose of this class is to map the idea of a garage door to the pinouts on 
    the raspberrypi. It provides methods to control the garage door and also provides
    and event hook to notify you of the state change. It also doesn't maintain any
    state internally but rather relies directly on reading the pin.
"""
class GarageDoor(object):
    
    def __init__(self, config):

        # Config
        self.relay_pin = config['relay']
        self.state_pin = config['state']
        self.id = config['id']
        self.mode = int(config.get('state_mode') == 'normally_closed')
        self.closing_delay = int(config['closing_delay'])
        self.done_closing = datetime.datetime.now()
        self.done_opening = datetime.datetime.now()

        # Setup
        self._state = None
        self.onStateChange = EventHook()

        # Set relay pin to output, state pin to input, and add a change listener to the state pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        GPIO.setup(self.state_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.state_pin, GPIO.BOTH, callback=self.__stateChanged, bouncetime=300)


        # Set default relay state to true (off)
        GPIO.output(self.relay_pin, True)

    # Release rpi resources
    def __del__(self):
        GPIO.cleanup()

    def is_closing(self):
        tnow = datetime.datetime.now()
        return tnow < self.done_closing

    def is_opening(self):
        tnow = datetime.datetime.now()
        return tnow < self.done_opening

    # These methods all just mimick the button press, they dont differ other than that
    # but for api sake I'll create three methods. Also later we may want to react to state
    # changes or do things differently depending on the intended action

    def open(self):
        if not self.is_opening():
            if self.is_closing():
                self.__press()  #stop first
				time.sleep(SHORT_WAIT)
                self.done_closing = datetime.datetime.now()
            self.__press()
            self.done_opening = datetime.datetime.now() + datetime.timedelta(seconds=self.closing_delay)

    def close(self):
        if not self.is_closing():
            if self.is_opening():
                self.__press()  #stop first
				time.sleep(SHORT_WAIT)
                self.done_opening = datetime.datetime.now()
            self.__press()
            self.done_closing = datetime.datetime.now() + datetime.timedelta(seconds=self.closing_delay)

    def stop(self):
        if self.is_closing() or self.is_opening()
            self.__press()
            self.done_closing = datetime.datetime.now()
            self.done_opening = datetime.datetime.now()

    # State is a read only property that actually gets its value from the pin
    @property
    def state(self):
        # Read the mode from the config. Then compare the mode to the current state. IE. If the circuit is normally closed and the state is 1 then the circuit is closed.
        # and vice versa for normally open
        state = GPIO.input(self.state_pin)
        if self.is_closing()
            return 'closing'
        else if state == self.mode:
            return 'closed'
        else:
            return 'open'

    # Mimick a button press by switching the GPIO pin on and off quickly
    def __press(self):
        GPIO.output(self.relay_pin, False)
        time.sleep(SHORT_WAIT)
        GPIO.output(self.relay_pin, True)

   
    # Provide an event for when the state pin changes
    def __stateChanged(self, channel):
        if channel == self.state_pin:
            # Had some issues getting an accurate value so we are going to wait for a short timeout
            # after a statechange and then grab the state
            time.sleep(SHORT_WAIT)
            self.onStateChange.fire(self.state)

    