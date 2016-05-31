#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# colours.py
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
    print "[COLOURS.PY] " + message



def applyColours(im, hue, saturation, hs, ms, ss, rob, rhb, rmb, rsb, gob, ghb, gmb, gsb, bob, bhb, bmb, bsb):
    if((hue != 0.0) or (saturation != 0.0) or (hs != 0.0) or (ms != 0.0) or (ss != 0.0) or (rob != 0.0) or (rhb != 0.0) or (rmb != 0.0) or (rsb != 0.0) or (gob != 0.0) or (ghb != 0.0) or (gmb != 0.0) or (gsb != 0.0) or (bob != 0.0) or (bhb != 0.0) or (bmb != 0.0) or (bsb != 0.0)):
        bpp = float(str(im.dtype).replace("uint", ""))
        np = float(2**bpp-1)


        out = im.astype(numpy.float32)
        isHr = contrast.isHighlight(out)
        isMr = contrast.isMidtone(out)
        isSr = contrast.isShadow(out)


        log("Converting to HSV")

        out = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)


        log("Hue...")
        if(hue != 0.0):
            out[0:,0:,0] = out[0:,0:,0]+(hue/100.0)*255

        log("Saturation...")
        if(saturation != 0.0):
            out[0:,0:,1] = out[0:,0:,1]+(saturation/10000.0)*255


        log("Saturation Highlights...")
        if(hs != 0.0):
            out[0:,0:,1] = (out[0:,0:,1] + ((hs*isHr[0:,0:,1])/10000.0)*255)


        log("Saturation Midtones...")
        if(ms != 0.0):
            out[0:,0:,1] = (out[0:,0:,1] + ((ms*isMr[0:,0:,1])/10000.0)*255)

        log("Saturation Shadows...")
        if(ss != 0.0):
            out[0:,0:,1] = (out[0:,0:,1] + ((ss*isSr[0:,0:,1])/10000.0)*255)

        out[out < 0.0] = 0.0
        out[out > 4294967296.0] = 4294967296.0

        out = cv2.cvtColor(out, cv2.COLOR_HSV2BGR)

        log("Red...")
        if(rob != 0.0):
            out[0:,0:,2] = out[0:,0:,2]+(rob/100.0)*np

        # Highlights
        if(rhb != 0.0):
            out[0:,0:,2] = (out[0:,0:,2] + ((rhb*isHr[0:,0:,1])/100.0)*np)

        # Midtones
        if(rmb != 0.0):
            out[0:,0:,2] = (out[0:,0:,2] + ((rmb*isMr[0:,0:,1])/100.0)*np)

        # Shadows
        if(rsb != 0.0):
            out[0:,0:,2] = (out[0:,0:,2] + ((rsb*isSr[0:,0:,1])/100.0)*np)



        log("Green...")
        if(gob != 0.0):
            out[0:,0:,1] = out[0:,0:,1]+(gob/100.0)*np

        # Highlights
        if(ghb != 0.0):
            out[0:,0:,1] = (out[0:,0:,1] + ((ghb*isHr[0:,0:,1])/100.0)*np)

        # Midtones
        if(gmb != 0.0):
            out[0:,0:,1] = (out[0:,0:,1] + ((gmb*isMr[0:,0:,1])/100.0)*np)

        # Shadows
        if(gsb != 0.0):
            out[0:,0:,1] = (out[0:,0:,1] + ((gsb*isSr[0:,0:,1])/100.0)*np)




        log("Blue...")
        if(bob != 0.0):
            out[0:,0:,0] = out[0:,0:,0]+(bob/100.0)*np

        # Highlights
        if(bhb != 0.0):
            out[0:,0:,0] = (out[0:,0:,0] + ((bhb*isHr[0:,0:,1])/100.0)*np)

        # Midtones
        if(bmb != 0.0):
            out[0:,0:,0] = (out[0:,0:,0] + ((bmb*isMr[0:,0:,1])/100.0)*np)

        # Shadows
        if(bsb != 0.0):
            out[0:,0:,0] = (out[0:,0:,0] + ((bsb*isSr[0:,0:,1])/100.0)*np)


        log("Done")
        out[out < 0.0] = 0.0
        out[out > np] = np
        return out.astype(im.dtype)

    else:

        return im
