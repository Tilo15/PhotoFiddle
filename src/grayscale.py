#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# grayscale.py
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
import os, sys, cv2, numpy, contrast

def log(message):
    print "[GRAYSCALE.PY] " + message



def applyBW(im, mode, r, g, b):
    bpp = float(str(im.dtype).replace("uint", ""))
    np = float(2**bpp-1)
    out = im.astype(numpy.float32)

    # Average
    if(mode == 0):
        log("Mode: Average")
        bc = out[0:,0:,0]
        gc = out[0:,0:,1]
        rc = out[0:,0:,2]

        out = (bc + gc + rc)/3

    if(mode == 1):
        log("Mode: Weighted Average")
        bc = out[0:,0:,0]
        gc = out[0:,0:,1]
        rc = out[0:,0:,2]

        out = 0.114*bc + 0.587*gc + 0.299*rc

    if(mode == 2):
        log("Mode: Luma")
        hsl = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)

        out = hsl[0:, 0:, 2]

    if(mode == 3):
        log("Mode: Custom Values")
        bc = out[0:,0:,0]
        gc = out[0:,0:,1]
        rc = out[0:,0:,2]

        out = b*bc + g*gc + r*rc

    out[out < 0.0] = 0.0
    out[out > np] = np

    out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)

    return out.astype(im.dtype)
