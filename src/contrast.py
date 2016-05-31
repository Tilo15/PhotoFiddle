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
    print "[CONTRAST.PY] " + message

def isHighlight(A):
    bleed = float(A.max()/12.0)
    mif = A.max()/3.0*2.0
    a = A.copy()

    a[a < mif - bleed] = 0.0
    a[(a < mif) * (a != 0.0)] = ((mif-(a[(a < mif) * (a != 0.0)]))/bleed)*-1+1
    a[a >= mif] = 1.0
    return a

def isHighlightOld(A):
    hif = A.max()/3.0*2.0
    return numpy.floor(A/hif)


def isMidtone(A):
    bleed = float(A.max()/12.0)
    mif = A.max()/3.0
    mir = A.max()/3.0*2.0
    a = A.copy()

    a[a < mif - bleed] = 0.0
    a[a > mir + bleed] = 0.0

    a[(a < mif) * (a != 0.0)] = ((mif-(a[(a < mif) * (a != 0.0)]))/bleed)*-1+1
    a[(a > mir) * (a != 0.0)] = (((a[(a > mir) * (a != 0.0)])-mir)/bleed)*-1+1
    a[(a >= mif) * (a <= mir) ] = 1.0
    return a


def isShadow(A):
    bleed = float(A.max()/12.0)
    mir = A.max()/3.0
    a = A.copy()

    a[a <= mir] = 1.0
    a[a > mir + bleed] = 0.0
    a[a > mir] = (((a[(a > mir) * (a != 0.0)])-mir)/bleed)*-1+1
    return a

def isShadowOld(A):
    mif = A.min()
    mir = A.max()/3.0
    p = -(A-mif)*(A-mir)

    return numpy.floor((numpy.sign(p) + 1)/2.0)


def applyContrast(im, hb, hc, mb, mc, sb, sc):
    if((hb != 0.0) or (hc != 0.0) or (mb != 0.0) or (mc != 0.0) or (sb != 0.0) or (sc != 0.0)):
        bpp = float(str(im.dtype).replace("uint", ""))
        np = float(2**bpp-1)
        out = im.astype(numpy.float32)
        log("Applying Highlights")
        ## Highlight Contrast
        isHr = isHighlight(out)
        if(hc != 0.0):
            hn = np + 4
            hc = (hc/100.0)*np+0.8
            out = (((hn*((hc*isHr)+np))/(np*(hn-(hc*isHr))))*(out - np/2.0)+np/2.0)

        if(hb != 0):
            ## Highlight Brightness
            out = (out + ((hb*isHr)/100.0)*np)

        log("Applying Midtones")
        ## Midtone Contrast
        isMr = isMidtone(out)
        if(mc != 0.0):
            hn = np + 4
            mc = (mc/100.0)*np+0.8
            #F = ((hn*(mc+np))/(np*(hn-mc)))
            #out = (((hn*(mc*isMr+np))/(np*(hn-mc*isMr)))*(out - np/2.0)+np/2.0)*numpy.ceil(isMr) + out - out*numpy.floor(isMr)
            out = (((hn*((mc*isMr)+np))/(np*(hn-(mc*isMr))))*(out - np/2.0)+np/2.0)

        if(mb != 0.0):
            ## Midtone Brightness
            out = (out + ((mb*isMr)/100.0)*np)


        log("Applying Shadows")
        ## Shadow Contrast
        isSr = isShadow(out)
        if(sc != 0.0):
            hn = np + 4
            mc = (sc/100.0)*np+0.8
            #F = ((hn*(mc+np))/(np*(hn-sc)))
            #out = (F*(out - np/2.0)+np/2.0)*isSr + (out - out*isSr)
            out = (((hn*((sc*isSr)+np))/(np*(hn-(sc*isSr))))*(out - np/2.0)+np/2.0)


        if(sb != 0.0):
            ## Shadow Brightness
            out = (out + ((sb*isSr)/100.0)*np)

        log("Done")
        out[out < 0.0] = 0.0
        out[out > np] = np
        return out.astype(im.dtype)

    else:
        return im

