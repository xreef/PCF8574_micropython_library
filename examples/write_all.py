#
# PCF8574 GPIO Port Expand
#
# AUTHOR:  Renzo Mischianti
# Website: www.mischianti.org
# VERSION: 0.0.1
#
# Description:
# write all pins
#
#           _____
#     A0  |1    16| Vcc
#     A1  |2    15| SDA
#     A2  |3    14| SCL
#  P0/IO0 |4    13| INT
#  P1/IO1 |5    12| P7/IO7
#  P2/IO2 |6    11| P6/IO6
#  P3/IO3 |7    10| P5/IO5
#     GND |8____ 9| P4/IO4
#
# Porting of PCF8574 library for Arduino
# https://www.mischianti.org/2019/01/02/pcf8574-i2c-digital-i-o-expander-fast-easy-usage/
#

from machine import Pin

from PCF8574 import PCF8574, P0, P7, P6, P1, P2, P3, P5, P4, DigitalInput

pcf = PCF8574(0x38, sda=21, scl=22 )

pcf.Pin(P0, Pin.OUT)
pcf.Pin(P1, Pin.OUT)
pcf.Pin(P2, Pin.OUT)
pcf.Pin(P3, Pin.OUT)
pcf.Pin(P7, Pin.OUT)
pcf.Pin(P6, Pin.OUT)
pcf.Pin(P5, Pin.OUT)
pcf.Pin(P4, Pin.OUT)

pcf.begin()

pcf.digital_write_all_array([1, 1, 1, 1, 1, 1, 1, 1])
# pcf.digital_write_all_bytes(0xFF)
#
# digital_input = DigitalInput()
# digital_input.P0 = 1
# digital_input.P1 = 1
# digital_input.P2 = 1
# digital_input.P3 = 1
# digital_input.P4 = 1
# digital_input.P5 = 1
# digital_input.P6 = 1
# digital_input.P7 = 1
# pcf.digital_write_all(digital_input)
