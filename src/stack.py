#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# stack.py
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
import os, sys, subprocess, shutil, glob


def log(message):
    print "[STACK.PY] " + message

def focusStack(files):

    log("Setting up dir")

    try:
        os.mkdir("/tmp/stack")
    except:
        pass

    filelist = []

    for image in files:
        log("Copying " + image)
        sp = image.split("/")
        shutil.copy(image, "/tmp/stack/" + sp[len(sp)-1])
        filelist.append("/tmp/stack/" + sp[len(sp)-1])

    log("Aligning")

    command = ["align_image_stack", "-m", "-a", "/tmp/stack/OUT"] + filelist
    subprocess.call(command)

    aligned_list = glob.glob('/tmp/stack/OUT*.tif')
    aligned_list.reverse()
    print aligned_list

    log ("Stacking")

    # Now run through enfuse
    sp = files[0].split("/")
    path = ""
    for i in sp[:len(sp)-1]:
        path += i + "/"

    path += sp[len(sp)-1].split(".")[0]
    path += " - Stacked.tiff"

    command = ["enfuse", "--output=/tmp/stacked.tiff", "--exposure-weight=0", "--saturation-weight=0", "--contrast-weight=1", "--hard-mask" , "-v"] + aligned_list
    print command
    subprocess.call(command)

    for i in aligned_list:
        os.remove(i)

    shutil.copyfile("/tmp/stacked.tiff", path)

    return path



