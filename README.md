<div>
<a href="https://www.mischianti.org/forums/forum/mischiantis-libraries/pcf8574-i2c-digital-i-o-expander/"><img
  src="https://github.com/xreef/LoRa_E32_Series_Library/raw/master/resources/buttonSupportForumEnglish.png" alt="Support forum pcf8574 English"
   align="right"></a>
</div>
<div>
<a href="https://www.mischianti.org/it/forums/forum/le-librerie-di-mischianti/pcf8574-expander-digitale-i-o-i2c/"><img
  src="https://github.com/xreef/LoRa_E32_Series_Library/raw/master/resources/buttonSupportForumItaliano.png" alt="Forum supporto pcf8574 italiano"
  align="right"></a>
</div>

#
#### www.mischianti.org

# PCF8574 PCF8574AP digital input and output expander with i2c bus.

## Changelog
 - 18/04/2023: v0.0.2 Add static declaration for Px constants inside class.
 - 14/04/2023: v0.0.1 Initial commit of stable version.

I try to simplify the use of this IC, with a minimal set of operations.

Tested with esp8266, esp32, Arduino, Arduino SAMD (Nano 33 IoT, MKR etc.), STM32 and rp2040 (Raspberry Pi Pico and similar)

PCF8574P address map 0x20-0x27 
PCF8574AP address map 0x38-0x3f 

### Installation
To install the library execute the following command:

```bash
pip install pcf8574-library
```

**Constructor:**
Pass the address of I2C 
```python
    from PCF8574 import PCF8574
    
    pcf = PCF8574(0x38, sda=21, scl=22)
```
To use interrupt you must pass the interrupt pin and the function to call when interrupt raised from PCF8574
```python
    from PCF8574 import PCF8574
    
    def keyPressedOnPCF8574(pin):
        # Interrupt called (No Serial no read no wire in this function, and DEBUG disabled on PCF library)
        keyPressed = True
    
    pcf = PCF8574(0x38, sda=21, scl=22, interrupt_callback=keyPressedOnPCF8574, interrupt_pin=18)
```

You must set input/output mode:
```python
    from machine import Pin
    from PCF8574 import PCF8574

    pcf.Pin(PCF8574.P0, Pin.IN)
    pcf.Pin(PCF8574.P1, Pin.IN, Pin.PULL_UP)
    pcf.Pin(PCF8574.P2, Pin.IN)
    pcf.Pin(PCF8574.P3, Pin.IN)
    
    pcf.Pin(PCF8574.P7, Pin.OUT)
    pcf.Pin(PCF8574.P6, Pin.OUT, 1)
    pcf.Pin(PCF8574.P5, Pin.OUT, 0)
    pcf.Pin(PCF8574.P4, Pin.OUT, 0)
```

then IC as you can see in the image has 8 digital input/output ports:

![PCF8574 schema](https://github.com/xreef/PCF8574_library/raw/master/resources/PCF8574-pins.gif)

To read all analog input in one trasmission you can do (even if I use a 10millis debounce time to prevent too much read from i2c):
```python
    digital_input = pcf.digital_read_all()
    
    print(digital_input.p0)
    print(digital_input.p1)
    print(digital_input.p2)
    print(digital_input.p3)
    print(digital_input.p4)
    print(digital_input.p5)
    print(digital_input.p6)
    print(digital_input.p7)
    
    array_input = pcf.digital_read_all_array()
    print(array_input)
    
    byte_input = pcf.digital_read_all_byte()
    print(bin(byte_input))
```

If you want to read a single input:
```python
    digital_input = pcf.digital_read(PCF8574.P1)
    print(digital_input)
```

If you want to write a digital value:
```python
    pcf.digital_write(PCF8574.P1, 1)
```

You can also use an interrupt pin:
You must initialize the pin and the function to call when interrupt raised from PCF8574
```python
    def callback(pin):
        now = utime.ticks_ms()
        global count
        count += 1
        print("Time: {} {}".format(now, count))
    
    
    pcf.attach_interrupt(18, callback)
```

For the examples I use this wire schema on breadboard:
![Breadboard](https://www.mischianti.org/wp-content/uploads/2021/04/WeMos-D1-esp8266-pcf8574-IC-wiring-schema-8-leds.jpg)
![Breadboard](https://www.mischianti.org/wp-content/uploads/2021/04/esp32-pcf8574-IC-wiring-schema-8-leds.jpg)
![Breadboard](https://www.mischianti.org/wp-content/uploads/2022/08/stm32_pcf8574_wiring_4_Led_4_Buttons_bb.jpg)

