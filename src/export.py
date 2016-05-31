#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# export.py
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
import os, sys, threading, shutil, subprocess
from wand.image import Image


#Comment the first line and uncomment the second before installing
#or making the tarball (alternatively, use project variables)
UI_FILE_EX = "src/photofiddle-export.glade"
#UI_FILE_EX = "/usr/local/share/photofiddle/ui/photofiddle-export.glade"


class GUI:

    imageWidth = 0
    imageHeight = 0


    callback = None

    processor = None

    def __init__(self):

        self.builder_ex = Gtk.Builder()
        self.builder_ex.add_from_file(UI_FILE_EX)
        self.builder_ex.connect_signals(self)

        self.window = self.builder_ex.get_object('exportWindow')

        exportStack = self.builder_ex.get_object('exportStack')
        exportStack.add_titled(self.builder_ex.get_object('exportWatermark'), "watermark", "Watermark")
        exportStack.add_titled(self.builder_ex.get_object('exportProfile'), "profile", "File Options")
        exportStack.add_titled(self.builder_ex.get_object('exportSave'), "fileWidget", "Save As")


    def beginExport(self, callback, processorFunc, parent):
        self.callback = callback
        self.processor = processorFunc
        self.window.set_transient_for(parent)
        self.window.set_attached_to(parent)
        self.window.show_all()


    def on_exportButton_clicked(self, button):
        im = Image(filename = self.path + "/" + self.bitmapImage)
        self.imageWidth, self.imageHeight = im.size

        wAjust = self.builder_ex.get_object('imageWidthAjustment')
        hAjust = self.builder_ex.get_object('imageHeightAjustment')

        wAjust.set_upper(self.imageWidth)
        hAjust.set_upper(self.imageHeight)

        wSpin = self.builder_ex.get_object('exportWidth')
        hSpin = self.builder_ex.get_object('exportHeight')

        wSpin.set_value(self.imageWidth)
        hSpin.set_value(self.imageHeight)

        self.builder_ex.get_object('exportSave').set_filename(self.path + "/" + "Exported Image")

        exportWindow = self.builder_ex.get_object('exportWindow')
        exportWindow.show_all()

    def on_exportWidth_value_changed(self, widget):
        newW = widget.get_value()
        ratio = newW/self.imageWidth
        self.builder_ex.get_object('exportHeight').set_value(ratio*self.imageHeight)

    def on_exportHeight_value_changed(self, widget):
        newH = widget.get_value()
        ratio = newH/self.imageHeight
        self.builder_ex.get_object('exportWidth').set_value(ratio*self.imageWidth)

    def on_exportCancelButton_clicked(self, button):
        exportWindow = self.builder_ex.get_object('exportWindow')
        exportWindow.hide()
        GLib.idle_add(self.callback, False)

    def on_exportWatermarkSwitch_state_set(self, switch, state):
        fileBrowser = self.builder_ex.get_object('exportWatermarkFile')
        combo = self.builder_ex.get_object('exportWatermarkPosition')

        fileBrowser.set_sensitive(switch.get_active())
        combo.set_sensitive(switch.get_active())

    def checkExportValid(self, sender, state = True):
        exportButton = self.builder_ex.get_object('exportExportButton')
        watermarkToggle = self.builder_ex.get_object('exportWatermarkSwitch')
        watermarkFile = self.builder_ex.get_object('exportWatermarkFile')
        exportFile = self.builder_ex.get_object('exportSave')

        error = False

        if(watermarkToggle.get_active()):
            if(watermarkFile.get_filename() == None):
                error = True
            else:
                error = not os.path.isfile(watermarkFile.get_filename())

        if(exportFile.get_filename() == None):
            error = True
        else:
            if(os.path.isdir(exportFile.get_filename())):
                error = True

        exportButton.set_sensitive(not error)

    def on_exportFormat_changed(self, combo):
        self.builder_ex.get_object('exportPngcrushEnabled').set_sensitive(combo.get_active() == 0)
        self.builder_ex.get_object('exportPngcrushEnabled').set_active(False)
        self.builder_ex.get_object('exportJpegQuality').set_sensitive(combo.get_active() == 1)


    def on_exportPreset_changed(self, combo):
        pngcrush = self.builder_ex.get_object('exportPngcrushEnabled')
        quality = self.builder_ex.get_object('exportJpegQuality')
        width = self.builder_ex.get_object('exportWidth')
        height = self.builder_ex.get_object('exportHeight')
        filetype = self.builder_ex.get_object('exportFormat')

        if(combo.get_active() == 0):
            width.set_sensitive(True)
            height.set_sensitive(True)
            filetype.set_sensitive(True)
            pngcrush.set_sensitive(filetype.get_active() == 0)
            quality.set_sensitive(filetype.get_active() == 1)
        else:

            if(combo.get_active() == 1):
                width.set_value(2048)
                filetype.set_active(1)
                quality.set_value(85)

            if(combo.get_active() == 2):
                width.set_value(self.imageWidth)
                filetype.set_active(0)
                pngcrush.set_active(True)

            if(combo.get_active() == 3):
                width.set_value(1920)
                filetype.set_active(1)
                quality.set_value(67)

            if(combo.get_active() == 4):
                if(self.builder_ex.get_object('exportWatermarkSwitch').get_active()):
                    errorm = self.builder_ex.get_object('watermarkPrintMessage')
                    errorm.run()
                    errorm.hide()
                width.set_value(self.imageWidth)
                filetype.set_active(2)

            width.set_sensitive(False)
            height.set_sensitive(False)
            filetype.set_sensitive(False)
            pngcrush.set_sensitive(False)
            quality.set_sensitive(False)


    def on_exportExportButton_clicked(self, button):

        continueFlag = True

        if(self.builder_ex.get_object('exportPreset').get_active() == 2):
            errorm = self.builder_ex.get_object('flickrPresetWarning')
            if(errorm.run() == -9):
                continueFlag = False
            errorm.hide()

        if(continueFlag):

            stack = self.builder_ex.get_object('exportStack')
            cancel = self.builder_ex.get_object('exportCancelButton')
            spinner = self.builder_ex.get_object('exportSpinner')
            stackSwitcher = self.builder_ex.get_object('exportStackSwitcher')

            stack.set_sensitive(False)
            stackSwitcher.set_sensitive(False)
            cancel.set_sensitive(False)
            button.set_sensitive(False)

            spinner.start()

            thread = threading.Thread(target=self.exportImage, args=(self.on_exportComplete, "good intentions"))
            thread.start()


    def on_exportComplete(self):
        stack = self.builder_ex.get_object('exportStack')
        cancel = self.builder_ex.get_object('exportCancelButton')
        spinner = self.builder_ex.get_object('exportSpinner')
        button = self.builder_ex.get_object('exportExportButton')
        stackSwitcher = self.builder_ex.get_object('exportStackSwitcher')

        stack.set_sensitive(True)
        stackSwitcher.set_sensitive(True)
        cancel.set_sensitive(True)
        button.set_sensitive(True)

        spinner.stop()

        self.builder_ex.get_object('exportWindow').hide()

        GLib.idle_add(self.callback, True)


    ### APP FUNCTIONS ###

    def exportImage(self, callback, typeOfIntentions):
        # Get the image
        image = Image(filename = self.processor())
        iw, ih = image.size

        # If user enabled watermarks
        if(self.builder_ex.get_object('exportWatermarkSwitch').get_active()):
            # Load the watermark
            watermark = Image(filename = self.builder_ex.get_object('exportWatermarkFile').get_filename())

            ww, wh = watermark.size

            position = None
            padding = 150

            # Figure out where to put the watermark
            positionCombo = self.builder_ex.get_object('exportWatermarkPosition')
            positionValue = positionCombo.get_active()

            # Top Left
            if(positionValue == 0):
                position = (padding, padding)

            # Top
            if(positionValue == 1):
                position = ((iw/2)-(ww/2), padding)

            # Top Right
            if(positionValue == 2):
                position = (iw - ww - padding, padding)

            # Left Centre
            if(positionValue == 3):
                position = (padding, (ih/2)-(wh/2))

            # Centre Centre
            if(positionValue == 4):
                position = ((iw/2)-(ww/2), (ih/2)-(wh/2))

            # Centre Right
            if(positionValue == 5):
                position = (iw - ww - padding, (ih/2)-(wh/2))

            # Bottom Left
            if(positionValue == 6):
                position = (padding, ih - wh - padding)

            # Bottom Centre
            if(positionValue == 7):
                position = ((iw/2)-(ww/2), ih - wh - padding)

            # Bottom Right
            if(positionValue == 8):
                position = (iw - ww - padding, ih - wh - padding)


            # Now we know where to put the watermark, copy it in
            #image.paste(watermark, position, watermark)

            image.composite_channel('all_channels', watermark, 'overlay', position[0], position[1])

        ## Done with watermarks

        # Get desired size
        oh = int(self.builder_ex.get_object('exportHeight').get_value())
        ow = int(self.builder_ex.get_object('exportWidth').get_value())

        # Resample
        image.resize(ow, oh)

        # What format?
        ff = self.builder_ex.get_object('exportFormat').get_active()
        # Where to?
        fn = self.builder_ex.get_object('exportSave').get_filename()

        # PNG
        if(ff == 0):
            # PNG Crush?
            if(self.builder_ex.get_object('exportPngcrushEnabled').get_active()):
                # Save PNG to /tmp
                image.format = "png"
                image.save(filename = "/tmp/precrush.png")
                # Now crush it
                subprocess.call(["pngcrush", "-rem gAMA", "-rem cHRM", "-rem iCCP", "-rem sRGB" , "-m 0", "-l 9", "-fix", "-v", "-v", "/tmp/precrush.png", fn])

                # Flickr needs images < 200MB
                if(self.builder_ex.get_object('exportPreset').get_active() == 2):
                    if(os.path.getsize(fn) >= 200000000):
                        # Reduce resolution and try again
                        widthWidget = self.builder_ex.get_object('exportWidth')
                        widthWidget.set_value(widthWidget.get_value()*0.97)
                        self.exportImage(callback, typeOfIntentions)

            # Normal PNG
            else:
                image.format = "png"
                image.save(filename = fn)


        # JPEG
        if(ff == 1):
            # Save at quality
            q = int(self.builder_ex.get_object('exportJpegQuality').get_value())
            image.format = "jpg"
            image.compression_quality = q
            image.save(filename = fn)



        # TIFF
        if(ff == 2):
            # Save
            image.format = "tiff"
            image.save(filename = fn)

        GLib.idle_add(callback)










def main():
    app = GUI()
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())

