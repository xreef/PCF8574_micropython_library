#
# PCF8574 GPIO Port Expand
#
# AUTHOR:  Renzo Mischianti
# VERSION: 0.0.1
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
# The MIT License (MIT)
#
# Copyright (c) 2017 Renzo Mischianti www.mischianti.org All right reserved.
#
# You may copy, alter and reuse this code in any way you like, but please leave
# reference to www.mischianti.org in your comments if you redistribute this code.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from machine import Pin, I2C
import utime


class Logger:
    def __init__(self, enable_debug):
        self.enable_debug = enable_debug
        self.name = ''

    def debug(self, msg, *args):
        if self.enable_debug:
            print(self.name, ' DEBUG ', msg, *args)

    def info(self, msg, *args):
        if self.enable_debug:
            print(self.name, ' INFO ', msg, *args)

    def error(self, msg, *args):
        if self.enable_debug:
            print(self.name, ' ERROR ', msg, *args)

    def getLogger(self, name):
        self.name = name
        return Logger(self.enable_debug)


logging = Logger(True)

logger = logging.getLogger(__name__)

P0 = 0
P1 = 1
P2 = 2
P3 = 3
P4 = 4
P5 = 5
P6 = 6
P7 = 7

DEBOUNCE_LATENCY = 100

class PCF8574:
    def __init__(self, address, i2c=None, i2c_id=0, sda=None, scl=None, interrupt_pin=None, interrupt_callback=None):
        if i2c:
            self._i2c = i2c
        elif sda and scl:
            self._i2c = I2C(i2c_id, scl=Pin(scl), sda=Pin(sda))
        else:
            raise ValueError('Either i2c or sda and scl must be provided')

        self._address = address

        self._interrupt_pin = None
        self._interrupt_callback = None
        self.irq_pin = None

        if interrupt_pin is not None and interrupt_callback is not None:
            self.attach_interrupt(interrupt_pin, interrupt_callback)
        # self._interrupt_pin = interrupt_pin
        # self._interrupt_callback = interrupt_callback

        self.encoder_pins = [False] * 8

        self.write_mode = 0
        self.read_mode = 0
        self.read_mode_pull_down = 0
        self.read_mode_pull_up = 0
        self.write_mode_up = 0
        self.last_read_millis = utime.ticks_ms()  # Change this line
        self.reset_initial = 0
        self.initial_buffer = 0

        self.byte_buffered = 0
        self.write_byte_buffered = 0
        self.encoder_values = 0

        if self._i2c.scan().count(address) == 0:
            raise OSError('PCF8574 not found at I2C address {:#x}'.format(address))

    def attach_interrupt(self, interrupt_pin, callback, trigger_event=Pin.IRQ_FALLING):
        self._interrupt_pin = interrupt_pin
        self._interrupt_callback = callback

        self.irq_pin = Pin(interrupt_pin, Pin.IN, Pin.PULL_UP)
        self.irq_pin.irq(handler=callback, trigger=trigger_event)

    def detach_interrupt(self):
        if self._interrupt_pin is not None and self._interrupt_callback is not None:
            self.irq_pin.irq(handler=None)
            # self._interrupt_pin = None

    def reattach_interrupt(self):
        if self._interrupt_pin is not None and self._interrupt_callback is not None:
            self.attach_interrupt(self._interrupt_pin, self._interrupt_callback)

    def begin(self):
        # Check if there are pins to set low
        if self.write_mode > 0 or self.read_mode > 0:
            logger.debug(
                'Begin with write_mode: {} and read_mode: {}'.format(bin(self.write_mode), bin(self.read_mode)))
            self.reset_initial = self.write_mode_up | self.read_mode_pull_up
            self.initial_buffer = self.write_mode_up | self.read_mode_pull_up
            self.byte_buffered = self.initial_buffer
            self.write_byte_buffered = self.write_mode_up
            logger.debug(
                'Reset initial: {} and initial buffer: {}'.format(bin(self.reset_initial), bin(self.initial_buffer)))

            byte_to_send = (self.write_byte_buffered & self.write_mode) | (self.reset_initial & self.read_mode)
            logger.debug('Byte to send: {}'.format(bin(byte_to_send)))
            nack = self._i2c.writeto(self._address, bytearray([byte_to_send]))
            if not nack:
                logger.error('Error writing to PCF8574')
                return False
            self.digital_write_all_byte(byte_to_send)

        # Initialize last read
        self.last_read_millis = utime.ticks_ms()

        if self._interrupt_pin is not None and self._interrupt_callback is not None:
            self.attach_interrupt(self._interrupt_pin, self._interrupt_callback)

        return True

    def Pin(self, pin, mode, output_start=None):
        if mode == Pin.OUT:
            self.write_mode = self.write_mode | 1 << pin
            if output_start == 1:
                self.write_mode_up = self.write_mode_up | 1 << pin

            self.read_mode = self.read_mode & ~(1 << pin)
            self.read_mode_pull_down = self.read_mode_pull_down & ~(1 << pin)
            self.read_mode_pull_up = self.read_mode_pull_up & ~(1 << pin)

        elif mode == Pin.IN and (output_start is None or output_start == Pin.PULL_DOWN):
            self.write_mode = self.write_mode & ~(1 << pin)

            self.read_mode = self.read_mode | 1 << pin
            self.read_mode_pull_down = self.read_mode_pull_down | 1 << pin
            self.read_mode_pull_up = self.read_mode_pull_up & ~(1 << pin)

        elif mode == Pin.IN and output_start == Pin.PULL_UP:
            self.write_mode = self.write_mode & ~(1 << pin)

            self.read_mode = self.read_mode | 1 << pin
            self.read_mode_pull_down = self.read_mode_pull_down & ~(1 << pin)
            self.read_mode_pull_up = self.read_mode_pull_up | 1 << pin

        else:
            raise ValueError('Invalid mode')

        logger.debug('Pin: {}, Mode: {}, Output Start: {}'.format(pin, mode, output_start))
        # debug Write mode in binary format
        logger.debug('Write Mode: {}, Read Mode: {}, Read Mode Pull Down: {}, Read Mode Pull Up: {}'.format(
            bin(self.write_mode), bin(self.read_mode), bin(self.read_mode_pull_down), bin(self.read_mode_pull_up)))

    # def encoder(self, pinA, pinB):
    #     # self.set_pin_mode(pinA, 'INPUT_PULLUP')
    #     # self.set_pin_mode(pinB, 'INPUT_PULLUP')
    #     #
    #     self.Pin(pinA, Pin.IN, Pin.PULL_UP)
    #     self.Pin(pinB, Pin.IN, Pin.PULL_UP)
    #
    #     self.encoder_pins[pinA] = True
    #     self.encoder_pins[pinB] = True

    def get_bit(self, n, position):
        return (n >> position) & 1

    def read_buffer(self, force=False):
        current_millis = utime.ticks_ms()
        if utime.ticks_diff(current_millis, self.last_read_millis) > DEBOUNCE_LATENCY or force:
            logger.debug('Read buffer')
            self._i2c.writeto(self._address, bytearray([self.read_mode]))
            i_input = int.from_bytes(self._i2c.readfrom(self._address, 1), 'little')
            logger.debug('Read: {}'.format(bin(i_input)))

            logger.debug('Read mode pd: {}'.format(bin(self.read_mode_pull_down)))
            logger.debug('Read mode pu: {}'.format(bin(self.read_mode_pull_up)))

            if (i_input & self.read_mode_pull_down) > 0 and (~i_input & self.read_mode_pull_up) > 0:
                logger.debug('Change detected')

                logger.debug('i_input & self.read_mode_pull_down: {}'.format(bin((i_input & self.read_mode_pull_down))))
                logger.debug('~i_input & self.read_mode_pull_up: {}'.format(bin((~i_input & self.read_mode_pull_up))))

                logger.debug('Byte buffered: {}'.format(bin(self.byte_buffered)))
                self.byte_buffered = (self.byte_buffered & ~self.read_mode) | i_input
                logger.debug('Byte buffered: {}'.format(bin(self.byte_buffered)))
            self.last_read_millis = current_millis

    # def digital_read(self, pin, force=False):
    #     self.read_buffer(force)
    #     return (self.byte_buffered & (1 << pin)) > 0

    def digital_read(self, pin, force_read_now=False):
        value = 1 if (1 << pin & self.read_mode_pull_up) else 0

        if (value == 1 and (1 << pin & self.read_mode_pull_down & self.byte_buffered)) or \
                (value == 0 and (1 << pin & self.read_mode_pull_up & ~self.byte_buffered)):
            # The pin was already set high or low
            if 1 << pin & self.byte_buffered:
                value = 1
            else:
                value = 0
        elif force_read_now or utime.ticks_diff(utime.ticks_ms(), self.last_read_millis) > DEBOUNCE_LATENCY:
            # Read from buffer
            self._i2c.writeto(self._address, bytearray([self.read_mode]))
            self.last_read_millis = utime.ticks_ms()
            incoming = self._i2c.readfrom(self._address, 1)
            if incoming:
                i_input = incoming[0]
                if (self.read_mode_pull_down & i_input) or (self.read_mode_pull_up & ~i_input):
                    # Change detected
                    self.byte_buffered = (self.byte_buffered & ~self.read_mode) | i_input
                    if 1 << pin & self.byte_buffered:
                        value = 1
                    else:
                        value = 0

        # If HIGH set to low to read buffer only one time
        if 1 << pin & self.read_mode_pull_down and value == 1:
            self.byte_buffered ^= 1 << pin
        elif 1 << pin & self.read_mode_pull_up and value == 0:
            self.byte_buffered ^= 1 << pin
        elif 1 << pin & self.write_byte_buffered:
            value = 1

        return value

    def digital_write(self, pin, value):
        if value == 1:
            self.write_byte_buffered = self.write_byte_buffered | (1 << pin)
        else:
            self.write_byte_buffered = self.write_byte_buffered & ~(1 << pin)
        self.write_buffer()

    def write_buffer(self):
        byte_to_send = (self.write_byte_buffered & self.write_mode) | (self.write_mode_up & ~self.write_mode)
        self._i2c.writeto(self._address, bytearray([byte_to_send]))

    def digital_write_all_byte(self, allpins):
        self._i2c.writeto(self._address,
                          bytearray([(allpins & self.write_mode) | (self.reset_initial & self.read_mode)]))

        self.byte_buffered = (allpins & self.write_mode) | (self.initial_buffer & self.read_mode)

    def digital_read_all(self):
        digital_input = DigitalInput()

        self._i2c.writeto(self._address, bytearray([self.read_mode]))
        self.last_read_millis = utime.ticks_ms()
        incoming = self._i2c.readfrom(self._address, 1)
        if incoming:
            i_input = incoming[0]
            if (self.read_mode_pull_down & i_input) or (self.read_mode_pull_up & ~i_input):
                # Change detected
                self.byte_buffered = (self.byte_buffered & ~self.read_mode) | i_input

        if 1 << 0 & self.read_mode:
            digital_input.p0 = 1 if (self.byte_buffered & (1 << 0)) != 0 else 0
        if 1 << 1 & self.read_mode:
            digital_input.p1 = 1 if (self.byte_buffered & (1 << 1)) != 0 else 0
        if 1 << 2 & self.read_mode:
            digital_input.p2 = 1 if (self.byte_buffered & (1 << 2)) != 0 else 0
        if 1 << 3 & self.read_mode:
            digital_input.p3 = 1 if (self.byte_buffered & (1 << 3)) != 0 else 0
        if 1 << 4 & self.read_mode:
            digital_input.p4 = 1 if (self.byte_buffered & (1 << 4)) != 0 else 0
        if 1 << 5 & self.read_mode:
            digital_input.p5 = 1 if (self.byte_buffered & (1 << 5)) != 0 else 0
        if 1 << 6 & self.read_mode:
            digital_input.p6 = 1 if (self.byte_buffered & (1 << 6)) != 0 else 0
        if 1 << 7 & self.read_mode:
            digital_input.p7 = 1 if (self.byte_buffered & (1 << 7)) != 0 else 0

        if 1 << 0 & self.write_mode:
            digital_input.p0 = 1 if (self.write_byte_buffered & (1 << 0)) else 0
        if 1 << 1 & self.write_mode:
            digital_input.p1 = 1 if (self.write_byte_buffered & (1 << 1)) else 0
        if 1 << 2 & self.write_mode:
            digital_input.p2 = 1 if (self.write_byte_buffered & (1 << 2)) else 0
        if 1 << 3 & self.write_mode:
            digital_input.p3 = 1 if (self.write_byte_buffered & (1 << 3)) else 0
        if 1 << 4 & self.write_mode:
            digital_input.p4 = 1 if (self.write_byte_buffered & (1 << 4)) else 0
        if 1 << 5 & self.write_mode:
            digital_input.p5 = 1 if (self.write_byte_buffered & (1 << 5)) else 0
        if 1 << 6 & self.write_mode:
            digital_input.p6 = 1 if (self.write_byte_buffered & (1 << 6)) else 0
        if 1 << 7 & self.write_mode:
            digital_input.p7 = 1 if (self.write_byte_buffered & (1 << 7)) else 0

        self.byte_buffered = (self.initial_buffer & self.read_mode) | (self.byte_buffered & ~self.read_mode)

        return digital_input

    def digital_read_all_byte(self):
        return self.digital_read_all().to_byte()

    def digital_read_all_array(self):
        return self.digital_read_all().to_array()

    def digital_write_all_array(self, all_pins_array):
        self.write_byte_buffered = (all_pins_array[0] << 0) | (all_pins_array[1] << 1) | (all_pins_array[2] << 2) | \
                                   (all_pins_array[3] << 3) | (all_pins_array[4] << 4) | (all_pins_array[5] << 5) | \
                                   (all_pins_array[6] << 6) | (all_pins_array[7] << 7)
        self.write_buffer()

    def set_val(self, pin, value):
        if value == 1:
            self.write_byte_buffered = self.write_byte_buffered | (1 << pin)
            self.byte_buffered = self.write_byte_buffered | (1 << pin)
        else:
            self.write_byte_buffered = self.write_byte_buffered & ~(1 << pin)
            self.byte_buffered = self.write_byte_buffered & ~(1 << pin)

    def digital_write_all(self, digital_input):
        self.set_val(0, digital_input.p0)
        self.set_val(1, digital_input.p1)
        self.set_val(2, digital_input.p2)
        self.set_val(3, digital_input.p3)
        self.set_val(4, digital_input.p4)
        self.set_val(5, digital_input.p5)
        self.set_val(6, digital_input.p6)
        self.set_val(7, digital_input.p7)

        return self.digital_write_all_byte(self.write_byte_buffered)

    def read_encoder_value_sequence_reduced(self, pin_a, pin_b, encoder_value, reverse_rotation=False):
        self.detach_interrupt()

        changed = False

        na = self.digital_read(pin_a, True)
        nb = self.digital_read(pin_b, True)

        encoder_pin_a_last = 1 if (self.encoder_values & (1 << pin_a)) > 0 else 0
        encoder_pin_b_last = 1 if (self.encoder_values & (1 << pin_b)) > 0 else 0

        encoded = (na << 1) | nb
        last_encoded = (encoder_pin_a_last << 1) | encoder_pin_b_last
        sum_val = (last_encoded << 2) | encoded

        if (
                sum_val == 0b1101
                or sum_val == 0b0010
        ):
            encoder_value = encoder_value + (1 if not reverse_rotation else -1)
            changed = True
        if (
                sum_val == 0b1110
                or sum_val == 0b0001
        ):
            encoder_value = encoder_value + (-1 if not reverse_rotation else 1)
            changed = True

        self.encoder_values = (encoder_pin_a_last != na) if self.encoder_values ^ (1 << pin_a) else self.encoder_values
        self.encoder_values = (encoder_pin_b_last != nb) if self.encoder_values ^ (1 << pin_b) else self.encoder_values
        self.reattach_interrupt()

        return changed, encoder_value

    def read_encoder_value(self, pin_a, pin_b, encoder_value, reverse_rotation=False):
        self.detach_interrupt()

        changed = False

        na = self.digital_read(pin_a, True)
        nb = self.digital_read(pin_b, True)

        encoder_pin_a_last = (self.encoder_values & (1 << pin_a)) > 0
        encoder_pin_b_last = (self.encoder_values & (1 << pin_b)) > 0

        encoded = (na << 1) | nb
        last_encoded = (encoder_pin_a_last << 1) | encoder_pin_b_last
        sum_values = (last_encoded << 2) | encoded

        if sum_values in [0b1101, 0b0010]:
            encoder_value += (1 if not reverse_rotation else -1)
            changed = True
        elif sum_values in [0b1110, 0b0001]:
            encoder_value += (-1 if not reverse_rotation else 1)
            changed = True

        self.encoder_values = (self.encoder_values ^ (1 << pin_a)) if encoder_pin_a_last != na else self.encoder_values
        self.encoder_values = (self.encoder_values ^ (1 << pin_b)) if encoder_pin_b_last != nb else self.encoder_values

        self.reattach_interrupt()

        return changed, encoder_value


class DigitalInput:
    def __init__(self):
        self.p0 = 0
        self.p1 = 0
        self.p2 = 0
        self.p3 = 0
        self.p4 = 0
        self.p5 = 0
        self.p6 = 0
        self.p7 = 0

    def get(self):
        return [self.p0, self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7]

    def set(self, pin, value):
        if pin == 0:
            self.p0 = value
        elif pin == 1:
            self.p1 = value
        elif pin == 2:
            self.p2 = value
        elif pin == 3:
            self.p3 = value
        elif pin == 4:
            self.p4 = value
        elif pin == 5:
            self.p5 = value
        elif pin == 6:
            self.p6 = value
        elif pin == 7:
            self.p7 = value

    def set_all(self, value):
        self.p0 = value[0]
        self.p1 = value[1]
        self.p2 = value[2]
        self.p3 = value[3]
        self.p4 = value[4]
        self.p5 = value[5]
        self.p6 = value[6]
        self.p7 = value[7]

    def to_byte(self):
        return self.p0 | self.p1 << 1 | self.p2 << 2 | self.p3 << 3 | self.p4 << 4 | self.p5 << 5 | self.p6 << 6 | self.p7 << 7

    def to_array(self):
        return [self.p0, self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7]
