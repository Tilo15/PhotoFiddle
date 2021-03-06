#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# tonemap.py
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
    print "[TONEMAP.PY] " + message


def overlay(B, A, bpp, utype):
    a = A/bpp
    b = B/bpp
    merged = ( 1 - 2*b )*a**2 + 2*a*b
    return (merged*bpp).astype(utype)

def invert(a):
    return a.max() - a


def runTonemap(im, blur, firstopacity, secondopacity, twopas):

    log("Running Tonemap")

    cvi = im

    log("Converting to grayscale")
    gray = cv2.cvtColor(cvi,cv2.COLOR_BGR2GRAY)

    log("Inverting...")
    inverted = invert(gray)


    if (blur > 0):
        log("Blurring")
        height, width = inverted.shape[:2]
        imsize = (height + width)/2
        blur_size = 2*round(round((imsize * (blur/100.0))/2))-1
        blurred = cv2.GaussianBlur(inverted, (int(blur_size), int(blur_size)), 0)
    else:
        blurred = inverted

	log("Blending 1/2")
    colour = cv2.cvtColor(blurred,cv2.COLOR_GRAY2BGR)
    colouredMap = cv2.addWeighted(colour, (firstopacity/100), cvi, 1 - (firstopacity/100), 0)
	


    log("Overlaying")
    bpp = int(str(cvi.dtype).replace("uint", ""))

    blended = overlay(colouredMap, cvi, float((2**bpp)-1), cvi.dtype)

    log("Blending 2/2")
    out = cv2.addWeighted(blended, (secondopacity/100), cvi, 1 - (secondopacity/100), 0)

    if(twopas):
        log("Running second pass")
        out = runTonemap(out, blur, firstopacity, secondopacity, False)

    return out





