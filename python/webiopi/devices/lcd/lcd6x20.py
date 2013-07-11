#   Copyright 2013 Mark de Jong - Mark@mdejong.de
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from webiopi.utils import *
from webiopi.utils.types import toint
from webiopi.devices.i2c import I2C
from time import sleep, localtime, strftime


class LCD6x20(I2C):

    # ----------------------------------------------------------------------
    # Constants

    # Port expander registers
    MCP23008_IODIR          = 0x00
    MCP23008_IPOL           = 0x01
    MCP23008_GPINTEN        = 0x02
    MCP23008_DEFVAL         = 0x03
    MCP23008_INTCON         = 0x04
    MCP23008_IOCON          = 0x05
    MCP23008_GPPU           = 0x06
    MCP23008_INTF           = 0x07
    MCP23008_INTCAP         = 0x08
    MCP23008_GPIO           = 0x09
    MCP23008_OLAT           = 0x0A

    # LED backlight
    LCD_LED_OFF             = 0x00
    LCD_LED_ON              = 0x80

    LCD_DATA_E1             = 0x04
    LCD_DATA_E2             = 0x01
    LCD_DATA_RS             = 0x02

    # LCD Commands
    LCD_CLEARDISPLAY        = 0x01
    LCD_RETURNHOME          = 0x02
    LCD_ENTRYMODESET        = 0x04
    LCD_DISPLAYCONTROL      = 0x08
    LCD_CURSORSHIFT         = 0x10
    LCD_FUNCTIONSET         = 0x20
    LCD_SETCGRAMADDR        = 0x40
    LCD_SETDDRAMADDR        = 0x80

    # Flags for display on/off control
    LCD_DISPLAYON           = 0x04
    LCD_DISPLAYOFF          = 0x00
    LCD_CURSORON            = 0x02
    LCD_CURSOROFF           = 0x00
    LCD_BLINKON             = 0x01
    LCD_BLINKOFF            = 0x00

    # Flags for display entry mode
    LCD_ENTRYRIGHT          = 0x00
    LCD_ENTRYLEFT           = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00

    # Flags for display/cursor shift
    LCD_DISPLAYMOVE         = 0x08
    LCD_CURSORMOVE          = 0x00
    LCD_MOVERIGHT           = 0x04
    LCD_MOVELEFT            = 0x00

    # DDRAM settings for BT62005
    KS0073_LINE1_START      = 0x00
    KS0073_LINE2_START      = 0x20
    KS0073_LINE3_START      = 0x40
    KS0073_LINE4_START      = 0x00
    KS0073_LINE5_START      = 0x20
    KS0073_LINE6_START      = 0x40


    # ----------------------------------------------------------------------
    # Constructor

    def __init__(self, slave=0x20):
        slave = toint(slave)
        I2C.__init__(self, slave)
        self.porta = self.LCD_LED_ON
        self.led = self.LCD_LED_ON
        self.writeRegister(self.MCP23008_IODIR, 0x00)
        self.writeRegisters( self.MCP23008_IODIR,
            [0b00000000,      # IODIR
             0b00000000,   # IPOL
             0b00000000,   # GPINTEN
             0b00000000,   # DEFVAL
             0b00000000,   # INTCON
             0b00000000,   # IOCON
             0b00000000,   # GPPU
             0b00000000,   # INTF
             0b00000000,   # INTCAP
             self.porta | self.led,   # GPIO
             self.porta | self.led ])# OLAT
        self.writeRegister( self.MCP23008_IOCON, 0x20 )
        self.displayshift   = (self.LCD_CURSORMOVE |
                               self.LCD_MOVERIGHT)
        self.displaymode    = (self.LCD_ENTRYLEFT |
                               self.LCD_ENTRYSHIFTDECREMENT)
        self.displaycontrol = (self.LCD_DISPLAYON |
                               self.LCD_CURSOROFF |
                               self.LCD_BLINKOFF)
        self.write_lcd(self.LCD_DATA_E1, 0x33) # Init
        self.write_lcd(self.LCD_DATA_E1, 0x32) # Init
        self.write_lcd(self.LCD_DATA_E1, 0x24) # 2 line 5x8 matrix
        self.write_lcd(self.LCD_DATA_E1, 0x09) # 2 line 5x8 matrix
        self.write_lcd(self.LCD_DATA_E1, 0x20) # 2 line 5x8 matrix
        self.write_lcd(self.LCD_DATA_E1, self.LCD_CLEARDISPLAY)
        self.write_lcd(self.LCD_DATA_E1, self.LCD_CURSORSHIFT    | self.displayshift)
        self.write_lcd(self.LCD_DATA_E1, self.LCD_ENTRYMODESET   | self.displaymode)
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E1, self.LCD_RETURNHOME)
        self.write_lcd(self.LCD_DATA_E2, 0x33) # Init
        self.write_lcd(self.LCD_DATA_E2, 0x32) # Init
        self.write_lcd(self.LCD_DATA_E2, 0x24) # 2 line 5x8 matrix
        self.write_lcd(self.LCD_DATA_E2, 0x09) # 2 line 5x8 matrix
        self.write_lcd(self.LCD_DATA_E2, 0x20) # 2 line 5x8 matrix
        self.write_lcd(self.LCD_DATA_E2, self.LCD_CLEARDISPLAY)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_CURSORSHIFT    | self.displayshift)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_ENTRYMODESET   | self.displaymode)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_RETURNHOME)


    def __str__(self):
        return "lcd 6x20"

    def __family__(self):
        return "lcd"

    # ----------------------------------------------------------------------
    # Write operations

    # Low-level 4-bit interface for LCD output.  This doesn't actually
    # write data, just returns a byte array of the PORTB state over time.
    # Can concatenate the output of multiple calls (up to 8) for more
    # efficient batch write.
    def out4(self, chip_cs, bitmask, value):
       hi = bitmask | ((value >> 4)<<3)
       lo = bitmask | ((value & 0x0F)<<3)
       return [(hi | chip_cs), hi, (lo | chip_cs), lo]


    # The speed of LCD accesses is inherently limited by I2C through the
    # port expander.  A 'well behaved program' is expected to poll the
    # LCD to know that a prior instruction completed.  But the timing of
    # most instructions is a known uniform 37 mS.  The enable strobe
    # can't even be twiddled that fast through I2C, so it's a safe bet
    # with these instructions to not waste time polling (which requires
    # several I2C transfers for reconfiguring the port direction).
    # The D7 pin is set as input when a potentially time-consuming
    # instruction has been issued (e.g. screen clear), as well as on
    # startup, and polling will then occur before more commands or data
    # are issued.

    pollables = ( LCD_CLEARDISPLAY, LCD_RETURNHOME )

    # Write byte, list or string value to LCD
    def write_lcd(self, chip_cs, value, char_mode=False):
        """ Send command/data to LCD """
        bitmask = self.led;
        if char_mode:
            bitmask |= self.LCD_DATA_RS   # Set data bit if not a command
        self.writeRegister( self.MCP23008_IOCON, 0x20 )
        # If string or list, iterate through multiple write ops
        if isinstance(value, str):
            last = len(value) - 1 # Last character in string
            if last>self.cols:
                last = self.cols
            data = []             # Start with blank list
            for i, v in enumerate(value): # For each character...
                # Append 4 bytes to list representing PORTB over time.
                # First the high 4 data bits with strobe (enable) set
                # and unset, then same with low 4 data bits (strobe 1/0).
                data.extend(self.out4(chip_cs, bitmask, ord(v)))
                # I2C block data write is limited to 32 bytes max.
                # If limit reached, write data so far and clear.
                # Also do this on last byte if not otherwise handled.
                if (len(data) >= 32) or (i == last):
                    self.writeRegisters( self.MCP23008_GPIO, data)
                    data       = []       # Clear list for next iteration
        elif isinstance(value, list):
            # Same as above, but for list instead of string
            last = len(value) - 1
            data = []
            for i, v in enumerate(value):
                data.extend(self.out4(chip_cs, bitmask, v))
                if (len(data) >= 32) or (i == last):
                    self.writeRegisters( self.MCP23008_GPIO, data)
                    data       = []
        else:
            # Single byte
            data = self.out4(chip_cs, bitmask, value)
            self.writeRegisters( self.MCP23008_GPIO, data)
            data       = []
        self.writeRegister( self.MCP23008_IOCON, 0 )
        # If a poll-worthy instruction was issued, reconfigure D7
        # pin as input to indicate need for polling on next call.
        if (not char_mode) and (value in self.pollables):
            sleep(0.015)


    # ----------------------------------------------------------------------
    # Utility methods

    def begin(self, cols, lines):
        self.currline = 0
        self.cols = cols
        self.numlines = lines
        self.clear()


    # Puts the MCP23008 back in Bank 0 + sequential write mode so
    # that other code using the 'classic' library can still work.
    # Any code using this newer version of the library should
    # consider adding an atexit() handler that calls this.
    def stop(self):
        self.porta = 0b10000000  # Turn off LEDs on the way out
        sleep(0.0015)
        self.writeRegister( self.MCP23008_IOCON, 0 )
        self.writeRegisters(
           0,
          [ 0b00000000,   # IODIR
            0b00000000,   # IPOL
            0b00000000,   # GPINTEN
            0b00000000,   # DEFVAL
            0b00000000,   # INTCON
            0b00000000,   # IOCON
            0b00000000,   # GPPU
            0b00000000,   # INTF
            0b00000000,   # INTCAP
            self.porta,   # GPIO
            self.porta ]) # OLAT


    def clear(self):
        self.write_lcd(self.LCD_DATA_E1, self.LCD_CLEARDISPLAY)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_CLEARDISPLAY)


    def home(self):
        self.write_lcd(self.LCD_DATA_E1, self.LCD_RETURNHOME)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_RETURNHOME)


    row_offsets = ( KS0073_LINE1_START, KS0073_LINE2_START, KS0073_LINE3_START, KS0073_LINE4_START, KS0073_LINE5_START, KS0073_LINE6_START )
    row_chip_select = ( LCD_DATA_E1, LCD_DATA_E1, LCD_DATA_E1, LCD_DATA_E2, LCD_DATA_E2, LCD_DATA_E2 )
    def setCursor(self, col, line_nr):
        if line_nr > self.numlines:
            line_nr = self.numlines - 1
        elif line_nr < 0:
            line_nr = 0
        self.write_lcd(self.row_chip_select[line_nr], self.LCD_SETDDRAMADDR |  (col+self.row_offsets[line_nr]) )


    def display(self):
        """ Turn the display on (quickly) """
        self.displaycontrol |= self.LCD_DISPLAYON
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def noDisplay(self):
        """ Turn the display off (quickly) """
        self.displaycontrol &= ~self.LCD_DISPLAYON
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def cursor(self):
        """ Underline cursor on """
        self.displaycontrol |= self.LCD_CURSORON
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def noCursor(self):
        """ Underline cursor off """
        self.displaycontrol &= ~self.LCD_CURSORON
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def ToggleCursor(self):
        """ Toggles the underline cursor On/Off """
        self.displaycontrol ^= self.LCD_CURSORON
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def blink(self):
        """ Turn on the blinking cursor """
        self.displaycontrol |= self.LCD_BLINKON
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def noBlink(self):
        """ Turn off the blinking cursor """
        self.displaycontrol &= ~self.LCD_BLINKON
        self.write_lcd(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def ToggleBlink(self):
        """ Toggles the blinking cursor """
        self.displaycontrol ^= self.LCD_BLINKON
        self.write(self.LCD_DATA_E1, self.LCD_DISPLAYCONTROL | self.displaycontrol)
        self.write(self.LCD_DATA_E2, self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def scrollDisplayLeft(self):
        """ These commands scroll the display without changing the RAM """
        self.displayshift = self.LCD_DISPLAYMOVE | self.LCD_MOVELEFT
        self.write_lcd(self.LCD_DATA_E1, self.LCD_CURSORSHIFT | self.displayshift)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_CURSORSHIFT | self.displayshift)


    def scrollDisplayRight(self):
        """ These commands scroll the display without changing the RAM """
        self.displayshift = self.LCD_DISPLAYMOVE | self.LCD_MOVERIGHT
        self.write_lcd(self.LCD_DATA_E1, self.LCD_CURSORSHIFT | self.displayshift)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_CURSORSHIFT | self.displayshift)


    def leftToRight(self):
        """ This is for text that flows left to right """
        self.displaymode |= self.LCD_ENTRYLEFT
        self.write_lcd(self.LCD_DATA_E1, self.LCD_ENTRYMODESET | self.displaymode)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_ENTRYMODESET | self.displaymode)


    def rightToLeft(self):
        """ This is for text that flows right to left """
        self.displaymode &= ~self.LCD_ENTRYLEFT
        self.write_lcd(self.LCD_DATA_E1, self.LCD_ENTRYMODESET | self.displaymode)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_ENTRYMODESET | self.displaymode)


    def autoscroll(self):
        """ This will 'right justify' text from the cursor """
        self.displaymode |= self.LCD_ENTRYSHIFTINCREMENT
        self.write_lcd(self.LCD_DATA_E1, self.LCD_ENTRYMODESET | self.displaymode)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_ENTRYMODESET | self.displaymode)


    def noAutoscroll(self):
        """ This will 'left justify' text from the cursor """
        self.displaymode &= ~self.LCD_ENTRYSHIFTINCREMENT
        self.write_lcd(LCD_DATA_E1, self.LCD_ENTRYMODESET | self.displaymode)
        self.write_lcd(LCD_DATA_E2, self.LCD_ENTRYMODESET | self.displaymode)


    def createChar(self, location, bitmap):
        self.write_lcd(self.LCD_DATA_E1, self.LCD_SETCGRAMADDR | ((location & 7) << 3))
        self.write_lcd(self.LCD_DATA_E1, bitmap, True)
        self.write_lcd(self.LCD_DATA_E1, self.LCD_SETDDRAMADDR)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_SETCGRAMADDR | ((location & 7) << 3))
        self.write_lcd(self.LCD_DATA_E2, bitmap, True)
        self.write_lcd(self.LCD_DATA_E2, self.LCD_SETDDRAMADDR)


    def message(self, text):
        """ Send string to LCD. Newline wraps to second line"""
        lines = str(text).split('\n')    # Split at newline(s)
        for i, line in enumerate(lines): # For each substring...
            if i > 0:                    # If newline(s),
                self.write_lcd(self.LCD_DATA_E1, 0xC0)         #  set DDRAM address to 2nd line
            self.write_lcd(self.LCD_DATA_E1, line, True)       # Issue substring


    def message_line(self, line_nr, text):
        self.setCursor(0, line_nr)
        self.write_lcd(self.row_chip_select[line_nr], text, True)


    def message_line_pos(self, line_nr, pos, text):
        self.setCursor(pos, line_nr)
        self.write_lcd(self.row_chip_select[line_nr], text, True)


    def backlight(self, onoff):
        self.led = onoff
        self.writeRegister( self.MCP23008_GPIO, self.led )

