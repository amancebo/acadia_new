#!/usr/bin/python
#
# Qt Widget for displaying color scales
#
# Hazen 3/09
#

from PyQt4 import QtGui
import sys

# Camera widget
class QColorGradient(QtGui.QWidget):
    def __init__(self, x_size = 50, y_size = 255, colortable = 0, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.x_size = x_size
        self.y_size = y_size
        self.min = 0
        self.max = 256
        self.image = QtGui.QImage(1, self.max - self.min, QtGui.QImage.Format_Indexed8)

        # initialize color table
        if colortable:
            for i in range(256):
                self.image.setColor(i, QtGui.qRgb(colortable[i][0],
                                                  colortable[i][1],
                                                  colortable[i][2]))
        else:
            for i in range(256):
                self.image.setColor(i, QtGui.qRgb(i, i, i))

        # initialize color gradient image
        i = self.min
        while i < self.max:
            self.image.setPixel(0, i, i)
            i += 1
        self.image.invertPixels()

    def newColorTable(self, colortable):
        for i in range(256):
            self.image.setColor(i, QtGui.qRgb(colortable[i][0], 
                                              colortable[i][1], 
                                              colortable[i][2]))
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.image.scaled(self.x_size, self.y_size))
            

#
# Testing
#

if __name__ == "__main__":
    class Parameters:
        def __init__(self):
            self.x_pixels = 200
            self.y_pixels = 200

    app = QtGui.QApplication(sys.argv)
    width = 120
    height = 500
    gradient = QColorGradient(x_size = width, y_size = height)
    gradient.resize(width, height)
    gradient.show()

    sys.exit(app.exec_())


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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

