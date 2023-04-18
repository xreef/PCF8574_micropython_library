#
# PCF8574 GPIO Port Expand
#
# AUTHOR:  Renzo Mischianti
# Website: www.mischianti.org
# VERSION: 0.0.2
#
# Description:
# write value of a pin start high
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

from PCF8574 import PCF8574

pcf = PCF8574(0x38, sda=21, scl=22)

pcf.Pin(PCF8574.P7, Pin.OUT, 1)

pcf.begin()

pcf.digital_write(PCF8574.P7, 0)
