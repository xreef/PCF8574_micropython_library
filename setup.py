import sys
sys.path.pop(0)
from setuptools import setup

setup(
    name="pcf8574-library",
    package_dir={'': 'src'},
    py_modules=["PCF8574"],
    version="0.0.2",
    description="PCF8574 micropython library. i2c digital expander for Arduino, Raspberry Pi Pico and rp2040 boards, esp32, SMT32 and ESP8266",
    long_description="PCF8574 micropython library. i2c digital expander for Arduino, Raspberry Pi Pico and rp2040 boards, esp32, SMT32 and ESP8266. Can read write digital values with only 2 wire. Very simple to use",
    keywords="micropython, digital, i2c, expander, pcf8574, pcf8574a, esp32, esp8266, stm32, SAMD, Arduino, wire, rp2040, Raspberry",
    url="https://github.com/xreef/PCF8574_micropython_library",
    author="Renzo Mischianti",
    author_email="renzo.mischianti@gmail.com",
    maintainer="Renzo Mischianti",
    maintainer_email="renzo.mischianti@gmail.com",
    license="MIT",
    install_requires=[],
    project_urls={
        'Documentation': 'https://www.mischianti.org/category/my-libraries/pcf8574/',
        'Documentazione': 'https://www.mischianti.org/it/category/le-mie-librerie/pcf8574-it/',
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: Implementation :: MicroPython",
        "License :: OSI Approved :: MIT License",
    ],
)