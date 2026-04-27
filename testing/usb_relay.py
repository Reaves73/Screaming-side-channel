#!/usr/bin/env python3

from nanpy import SerialManager
from nanpy import ArduinoApi

connection = SerialManager("/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0")
arduino = ArduinoApi(connection=connection)

def set_pin(pin, on, opendrain=True):
	if opendrain:
		if on:
			# on means floating! this is important!
			arduino.digitalWrite(pin, arduino.LOW)
			arduino.pinMode(pin, arduino.INPUT)
		else:
			arduino.digitalWrite(pin, arduino.LOW)
			arduino.pinMode(pin, arduino.OUTPUT)
	else:
		arduino.digitalWrite(pin, arduino.HIGH if on else arduino.LOW)
		arduino.pinMode(pin, arduino.OUTPUT)

relay_pin = 2
def set_relay(on):
	set_pin(relay_pin, not on, opendrain=True)
	print(f"!!! relay is {'ON' if on else 'OFF'}.")
	set_pin(13, on, opendrain=False) # on-board LED

relay_state = False
set_relay(relay_state)
def toggle_relay():
	global relay_state
	relay_state ^= True
	set_relay(relay_state)

try:
	while (True):
		input("hit enter to toggle relay...")
		toggle_relay()
except KeyboardInterrupt:
	print("")
	print("")

