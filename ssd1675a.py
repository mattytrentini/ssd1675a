''' A Micropython driver for the SSD1675a EPaper controller.

Initially trying to support Mike Rankin's ESP32 + EPaper board (thanks for the prototype Mike!)
but the intent is to ultimately work for any SSD1675a-powered display.

'''

import framebuf
import time
import ubinascii


class SSD1675A:
    def __init__(self, spi, cs_pin, dc_pin, busy_pin, reset_pin, width=296, height=128):
        self.width = width
        self.height = height
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.framebuf = fb
        # Provide methods for accessing FrameBuffer graphics primitives. This is a
        # workround because inheritance from a native class is currently unsupported.
        # http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
        # TODO Need to extend to have two framebuffers - red and black.
        # Will then need to _define_ these functions to allow a colour parameter and modify
        # the appropriate framebuffer
        self.fill = fb.fill
        self.pixel = fb.pixel
        self.hline = fb.hline
        self.vline = fb.vline
        self.line = fb.line
        self.rect = fb.rect
        self.fill_rect = fb.fill_rect
        self.text = fb.text
        self.scroll = fb.scroll
        self.blit = fb.blit

        # Set up the GPIO Pins
        #self.rate = 10 * 1024 * 1024
        dc_pin.init(dc_pin.OUT, value=0)
        cs_pin.init(cs_pin.OUT, value=1)
        busy_pin.init(busy_pin.IN)
        reset_pin.init(reset_pin.OUT, value=0)
        self.spi = spi
        self.dc = dc_pin
        self.cs = cs_pin
        self.busy = busy_pin
        self.reset = reset_pin

        self._init_ssd1675a()

    def write_cmd(self, cmd):
        #self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        #self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)

    def write(self, cmd, data=None):
        print(hex(cmd))
        self.write_cmd(cmd)
        if data:
            print(ubinascii.hexlify(data))
            self.write_data(data)

    def _wait_busy(self):
        while self.busy.value():
            time.sleep_ms(10)

    def _init_ssd1675a(self):
        self.hw_reset()
        self.sw_reset()
        self.write(0x74, b'\x54') # Set Analog Block Control
        self.write(0x7E, b'\x3B') # Set Digital Block Control (Note! There was an error in spi_demo.c, cmd was 75)
        self.write(0x01, b'\x27\x01\x00') # Set MUX as 296
        self.write(0x3A, b'\x35') # Set 130Hz (0x25=100Hz, 0x07=150Hz) (Note! 130Hz isn't listed in datasheet...)
        self.write(0x3B, b'\x04') # Set 130Hz (0x06=100Hz)
        self.write(0x3C, b'\x33') # Border Waveform Control: Level Setting for VBD=VSH2, GS Transition for VBD=LUT3
        self.write(0x11, b'\x03') # Data Entry Mode (increment x and y and update in x direction)
        self.write(0x44, b'\x00\x0F') # set RAM x address start/end, in page 36. Start at 0x00, end at 0x0F(15+1)*8->128
        self.write(0x45, b'\x00\x00\x27\x01') # set RAM y address start/end, in page 37. Start at 0x127, end at 0x00.

        self.write(0x04, b'\x41\xA8\x32') # set VSH1/VSH2/VSL values: 15/5/-15 respectively
        self.write(0x2C, b'\x68') # VCOM = -2.6V
        self._write_lut()

    def _write_lut(self):
        ''' Not really sure what these values mean. See 6.7 in the datasheet. Values taken
        from drewler's spi_demo.c code.'''
        self.write(0x32, b'\x22\x11\x10\x00\x10\x00\x00\x11\x88\x80\x80\x80\x00\x00'
                         b'\x6A\x9B\x9B\x9B\x9B\x00\x00\x6A\x9B\x9B\x9B\x9B\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\x04\x18\x04\x16\x01\x0A\x0A'
                         b'\x0A\x0A\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04'
                         b'\x04\x08\x3C\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

    def set_xy_window(self, xstart=0, xend=15, ystart=0, yend=295):
        self.write(0x44, bytearray([xstart, xend])) # Set RAM x address start/end
        self.write(0x45, bytearray([ystart, ystart >> 8, yend, yend >> 8])) # Set RAM y address start/end

    def set_xy_counter(self, x, y):
        self.write(0x4E, bytearray([x])) # Set RAM x address count
        self.write(0x4F, bytearray([y, y>>8])) # Set RAM y address count

    def clear(self):
        self.set_xy_window()
        self.set_xy_counter(0, 0)
        self.write(0x24, b'\xFF' * 4736)
        self.write(0x20) # Update display
        self._wait_busy()

    def show(self):
        self.set_xy_window(0, 0x0F, 0, 0x127)
        self.set_xy_counter(0, 0)
        self.write(0x24, self.buffer) # Write data
        self.write(0x22, bytearray([0xC7]))
        self.write(0x20) # Update display
        self._wait_busy()

    def sw_reset(self):
        self.write(0x12) # SWRESET
        self._wait_busy()

    def hw_reset(self):
        self.reset.value(0)
        time.sleep_ms(200)
        self.reset.value(1)
        time.sleep_ms(200)

