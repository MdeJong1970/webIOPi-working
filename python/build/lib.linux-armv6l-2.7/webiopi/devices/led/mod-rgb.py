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
from time import sleep


class MODRGB(I2C):

    # ----------------------------------------------------------------------
    # Constants

    # ----------------------------------------------------------------------
    # Constructor

    def __init__(self, busnum=0, slave=0x40):
        I2C.__init__(self, toint(slave))
        self.red = 0
        self.green = 0
        self.blue = 0
        data = [ 0x05, 0x03, self.red, self.green, self.blue ]
        self.writeBytes(data)

    def __str__(self):
        return "MODRGB"

    def __family__(self):
        return "led"

    def set_red( self, red ):
        self.red = red
        data = [ 0x05, 0x03, self.red, self.green, self.blue ]
        self.writeBytes(data)

    def set_green( self, green ):
        self.green = green
        data = [ 0x05, 0x03, self.red, self.green, self.blue ]
        self.writeBytes(data)


    def set_blue( self, blue ):
        self.blue = blue
        data = [ 0x05, 0x03, self.red, self.green, self.blue ]
        self.writeBytes(data)


    def set_rgb( self, red, green, blue ):
        self.red = red
        self.green = green
        self.blue = blue
        data = [ 0x05, 0x03, self.red, self.green, self.blue ]
        self.writeBytes(data)


    def set_channel( self, value ):
        if channel == 1:
            self.red = value
        elif channel == 2:
            self.green = value
        else:
            self.blue = value
        data = [ 0x05, 0x03, self.red, self.green, self.blue ]
        self.writeBytes(data)


    def set_all_channel( self, value ):
        self.red = value
        self.green = value
        self.blue = value
        data = [ 0x05, 0x03, self.red, self.green, self.blue ]
        try:
            self.writeBytes(data)
        except:
            pass

