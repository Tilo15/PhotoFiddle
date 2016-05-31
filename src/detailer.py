#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# detailer.py
# Copyright (C) 2016 Billy Barrow <billyb@pcthingz.com>
#
# photofiddle is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# photofiddle is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
import os, sys, numpy, cv2, threading, contrast


def log(message):
    print "[DETAILER.PY] " + message


def overlay(B, A, bpp, utype):
    a = A/bpp
    b = B/bpp
    merged = ( 1 - 2*b )*a**2 + 2*a*b
    return (merged*bpp).astype(utype)

def invert(a):
    return a.max() - a


def runDetailer(im, strength, detail, hb, hc, mb, mc, sb, sc):

    log("Running Detailer")

    cvi = im

    log("Converting to grayscale")
    gray = cv2.cvtColor(cvi,cv2.COLOR_BGR2GRAY)

    log("Inverting...")
    inverted = invert(gray)

    log("Applying Brightness and Contrast Ajustments")
    inverted = contrast.applyContrast(inverted, sb, sc, mb, mc, hb, hc)

    if (detail > 0):
        log("Blurring")
        blur_size = 2*round((round(detail)+1)/2)-1
        blurred = cv2.GaussianBlur(inverted, (int(blur_size), int(blur_size)), 0)
    else:
        blurred = inverted


    log("Overlaying")
    colour = cv2.cvtColor(blurred,cv2.COLOR_GRAY2BGR)

    bpp = int(str(cvi.dtype).replace("uint", ""))

    blended = overlay(colour, cvi, float((2**bpp)-1), cvi.dtype)

    log("Blending")
    out = cv2.addWeighted(blended, (strength/100), cvi, 1 - (strength/100), 0)


    return out




def runEdges(im, strength, t1, t2):

    log("Edge Detect")

    bpp = int(str(im.dtype).replace("uint", ""))

    eight = ((im/float(2**bpp))*255).astype(numpy.uint8)

    grey = cv2.cvtColor(eight,cv2.COLOR_BGR2GRAY)

    edged = cv2.Canny(grey,t1,t2)

    log("Inverting...")
    inverted = edged

    colour = cv2.cvtColor(inverted,cv2.COLOR_GRAY2BGR)

    colour[colour != 0] = 255
    colour[colour == 0] = 128

    nbpp = (colour/255.0)*(2**bpp)



    log("Blurring")

    blurred = cv2.GaussianBlur(nbpp, (7, 7), 0)

    blurred[blurred == (2**bpp) -1] = ((2**bpp)-1)/2.0


    log("Overlaying")

    overlayed = overlay(blurred, im, float((2**bpp)-1), im.dtype)


    log("Blending")
    out = cv2.addWeighted(overlayed, (strength/100), im, 1 - (strength/100), 0)

    return out.astype(im.dtype)





