# Micropython SSD1675A driver

The [SSD1675](http://www.solomon-systech.com/en/product/advanced-display/Dot-Matrix_Bistable_Display/SSD1675/) 
is a commonly used controller for E-Paper displays manufactured by [Solomon Systech](http://www.solomon-systech.com/). 

This driver is initially trying to support 
[Mike Rankin's ESP32 E-Paper board](https://twitter.com/mikerankin/status/916268694489096192) (thanks for the prototype Mike!)
under [Micropython](https://micropython.org/). However the intent is to provide a useful Micropython driver for
_any_ SSD1675a-powered display.

## Other libraries

[Drewler's Arduino driver](https://github.com/drewler/arduino-SSD1675A) was _very_ helpful,
especially for initialization.

[Radomir Dopieralski's drivers](https://bitbucket.org/thesheep/micropython-ili9341), particularly for the
[SSD1606](https://bitbucket.org/thesheep/micropython-ili9341/src/1fd322f33fb68194e9a848d9fe5c74789aea15b8/ssd1606.py?at=default&fileviewer=file-view-default), were also useful:

[Peter Hinch's epaper library](https://github.com/peterhinch/micropython-epaper) was another useful reference.

## Example

```python
import ssd1675a
from machine import Pin, SPI
eink = ssd1675a.SSD1675A(spi=SPI(1,
                                 baudrate=100000,
                                 mosi=Pin(23, Pin.OUT),
                                 sck=Pin(18, Pin.OUT),
                                 miso=Pin(19, Pin.IN)),
                         cs=Pin(4, Pin.OUT),
                         dc=Pin(16, Pin.OUT),
                         busy=Pin(17, Pin.IN))
eink.rect(20, 20, 100, 100, 1)
eink.show()
```
