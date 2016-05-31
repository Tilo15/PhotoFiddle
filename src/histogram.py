#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# contrast.py
# Copyright (C) 2016 Billy Barrow <billyb@pcthingz.com>
#
# workflow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# workflow is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GdkPixbuf, Gdk, GObject, GLib, Gio
import os, sys, cv2, numpy

def log(message):
    print "[HISTOGRAM.PY] " + message

def drawHistFor(img):
    log("Drawing Histogram")
    bpp = float(str(img.dtype).replace("uint", ""))
    im = ((img/2**bpp)*255).astype('uint8')
    bpp = float(str(im.dtype).replace("uint", ""))
    hv = 2**bpp
    hist = numpy.zeros(shape=(128,330, 3))

    color = ('b','g','r')
    for i,col in enumerate(color):
        histr = cv2.calcHist([im],[i],None,[hv],[0,hv])
        log("Drawing " + col + " Histogram")
        for i2, hval in enumerate(histr):
            hi = max(histr)
            hist[int(-(hval/hi)*127)+127][int((i2/hv)*330)][i] = 255;

    log("Done")

    cv2.imwrite("/tmp/phf-hist.tiff", hist)

    return GdkPixbuf.Pixbuf.new_from_file("/tmp/phf-hist.tiff")



    
