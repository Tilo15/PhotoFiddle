#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# main.py
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
import os, sys, cv2, threading, subprocess, time, numpy, contrast, stack, detailer, histogram, colours, grayscale, cairo


#Comment the first line and uncomment the second before installing
#or making the tarball (alternatively, use project variables)
UI_FILE = "src/photofiddle.glade"
#UI_FILE = "/usr/local/share/photofiddle/ui/photofiddle.glade"

UI_FILE_EX = "src/photofiddle-export.glade"
#UI_FILE_EX = "/usr/local/share/photofiddle/ui/photofiddle-export.glade"

Gtk.Settings.get_default().set_property("gtk_application_prefer_dark_theme", True)


class GUI:

    version = 0.1

    previewWidth = 2000.0
    defaultPreviewWidth = 2000.0

    imageFile = None
    image = None
    origionalImage = None

    operating = False
    triggeredWhileOperating = False

    currentPB = None
    origionalPB = None

    exportFile = None
    exportWatermarkFile = None
    exportLastChanged = None

    origionalImageSize = (0, 0)

    bpp = 8


    def __init__(self):

        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI_FILE)
        self.builder.connect_signals(self)

        self.builder_ex = Gtk.Builder()
        self.builder_ex.add_from_file(UI_FILE_EX)
        self.builder_ex.connect_signals(self)

        self.populateObjArr()

        self.windowEx = self.builder_ex.get_object('exportWindow')

        exportStack = self.builder_ex.get_object('exportStack')
        exportStack.add_titled(self.builder_ex.get_object('exportWatermark'), "watermark", "Watermark")
        exportStack.add_titled(self.builder_ex.get_object('exportProfile'), "profile", "File Options")
        exportStack.add_titled(self.builder_ex.get_object('exportSaveBox'), "fileWidget", "Save As")


        window = self.builder.get_object('window')

        window.set_wmclass ("PhotoFiddle", "PhotoFiddle")
        oWindow = self.builder.get_object('openWindow')
        oWindow.set_wmclass ("PhotoFiddle", "PhotoFiddle")
        self.windowEx.set_wmclass ("PhotoFiddle", "PhotoFiddle")

        self.disableControls()

        self.windowEx.set_transient_for(window)
        self.windowEx.set_attached_to(window)

        actionStack = self.builder.get_object('actionStack')
        actionStack.add_titled(self.builder.get_object('bandcWidget'), "bandc", "Brightness Contrast")
        actionStack.add_titled(self.builder.get_object('detailerWidget'), "detailer", "Detailer")
        actionStack.add_titled(self.builder.get_object('colourWidget'), "colour", "Colours")
        actionStack.add_titled(self.builder.get_object('artisticWidget'), "artistic", "Artistic")
        #actionStack.add_titled(self.builder.get_object('hdrifyWidget'), "hdr", "HDRify")

        actionStack = self.builder.get_object('openStack')
        actionStack.add_titled(self.builder.get_object('openFile'), "open", "Open Photograph")
        actionStack.add_titled(self.builder.get_object('stackOpen'), "stack", "Focus Stack")


        window.show_all()
        window.maximize()




    ## GUI Calls

    def on_window_destroy(self, window):
        Gtk.main_quit()

    def on_aboutButton_clicked(self, sender):
        d = self.builder.get_object("aboutdialog")
        d.run()
        d.hide()

    def on_openButton_clicked(self, button):
        self.builder.get_object('openWindow').show_all()

    def on_openFileOpen_clicked(self, button):
        self.disableControls()
        self.builder.get_object('openWindow').hide()

        tabName = self.builder.get_object('openStack').get_visible_child_name()

        if(tabName == "open"):
            fileb = self.builder.get_object('openFile')
            self.showMessage(False, "Opening '" + fileb.get_filename() + "'", "Please wait while PhotoFiddle loads your photograph.", True)

            thread = threading.Thread(target=self.loadImage, args=(fileb.get_filename(), self.on_image_loaded))
            thread.start()

        if(tabName == "stack"):
            fileb = self.builder.get_object('stackChooser')
            self.showMessage(False, "Stacking Images", "Wait a moment while we perfom a focus stack.", True)

            thread = threading.Thread(target=self.focusStackImages, args=(fileb.get_filenames(), self.on_image_loaded))
            thread.start()

    def on_openFileCancel_clicked(self, button):
        self.builder.get_object('openWindow').hide()


    def on_image_loaded(self):
        self.hideMessage()
        self.builder.get_object('controlReveal').set_reveal_child(True)
        self.enableControls()


    def on_fitButton_clicked(self, button):
        height, width = self.image.shape[:2]
        preview = self.builder.get_object('previewWindow')
        lg = max(height, width)
        if(lg == width):
            vpw = preview.get_allocated_width() - 12
            self.previewWidth = float(vpw)

            ratio = float(vpw)/float(width)
            if(height*ratio >= preview.get_allocated_height()):
                vph = preview.get_allocated_height() - 12
                ratio = float(vph)/float(height)
                self.previewWidth = width*ratio


        else:
            vph = preview.get_allocated_height() - 12
            ratio = float(vph)/float(height)
            self.previewWidth = width*ratio

            if(self.previewWidth >= preview.get_allocated_width()):
                vpw = preview.get_allocated_width() - 12
                self.previewWidth = float(vpw)

        self.updatePreview()


    def on_zoomInButton_clicked(self, button):
        self.previewWidth += 200.00

        self.updatePreview()

    def on_zoomOutButton_clicked(self, button):
        self.previewWidth -= 200.00

        self.updatePreview()

    def on_origionalSizeButton_clicked(self, button):
        height, width = self.image.shape[:2]
        self.previewWidth = float(width)

        self.updatePreview()

    def on_previewOldImageButton_toggled(self, button):
        preview = self.builder.get_object('preview')
        if(self.builder.get_object('previewOldImageButton').get_active()):
            preview.set_from_pixbuf(self.origionalPB)
        else:
            preview.set_from_pixbuf(self.currentPB)


    def on_exportButton_clicked(self, button):
        wAjust = self.builder_ex.get_object('imageWidthAjustment')
        hAjust = self.builder_ex.get_object('imageHeightAjustment')

        wAjust.set_upper(self.origionalImageSize[1])
        hAjust.set_upper(self.origionalImageSize[0])

        wSpin = self.builder_ex.get_object('exportWidth')
        hSpin = self.builder_ex.get_object('exportHeight')

        wSpin.set_value(self.origionalImageSize[1])
        hSpin.set_value(self.origionalImageSize[0])

        self.windowEx.show_all()


    ## Toolbox GUI Calls

    def on_detailerSwitch_state_set(self, switch, state):
        self.builder.get_object('detailerGrid').set_sensitive(state)

    def on_bwSwitch_state_set(self, switch, state):
        self.builder.get_object('bwGrid').set_sensitive(state)

    def on_bwCombo_changed(self, combo):
        value = combo.get_active()
        self.builder.get_object('bwrs').set_sensitive(value == 3)
        self.builder.get_object('bwgs').set_sensitive(value == 3)
        self.builder.get_object('bwbs').set_sensitive(value == 3)

    def on_edgesSwitch_state_set(self, switch, state):
        self.builder.get_object('edgeGrid').set_sensitive(state)

    def on_focusSwitch_state_set(self, switch, state):
        self.builder.get_object('focusGrid').set_sensitive(state)



    def on_claheSwitch_state_set(self, switch, state):
        self.builder.get_object('hdrifySlider1').set_sensitive(state)
        self.builder.get_object('hdrifySlider2').set_sensitive(state)


    def on_tool_update(self, sender, opt = None, opt2 = None):
        if(not self.operating):
            thread = threading.Thread(target=self.updateImage)
            thread.start()
        else:
            self.triggeredWhileOperating = True

    def on_peaks_toggle(self, sender):

        reset = not sender.get_active()

        hp = self.builder.get_object("showHighPeaksButton").get_active()
        lp = self.builder.get_object("showLowPeaksButton").get_active()
        thread = threading.Thread(target=self.showPeaks, args=(lp, hp, False, reset))
        thread.start()


    def on_autoContrastButton_clicked(self, button):
        confirm = self.builder.get_object('autoContrastDialog')
        continueFlag = True
        if(confirm.run() == -9):
            continueFlag = False
        confirm.hide()
        if(continueFlag):
            v = contrast.autoContrast(self.origionalImage)
            self.builder.get_object('hc').set_value(v[0])
            self.builder.get_object('mc').set_value(v[1])
            self.builder.get_object('sc').set_value(v[2])



    def tool_reset(self, sender):
        self._set(self.defaultData, sender)



    ## Export Window Functions

    def on_exportWidth_value_changed(self, widget):
        newW = widget.get_value()
        ratio = newW/self.origionalImageSize[1]
        self.builder_ex.get_object('exportHeight').set_value(ratio*self.origionalImageSize[0])

    def on_exportHeight_value_changed(self, widget):
        newH = widget.get_value()
        ratio = newH/self.origionalImageSize[0]
        self.builder_ex.get_object('exportWidth').set_value(ratio*self.origionalImageSize[1])

    def on_exportCancelButton_clicked(self, button):
        self.windowEx.hide()

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
        stack = self.builder_ex.get_object('exportStack')

        self.exportFile = exportFile.get_filename()
        self.exportWatermarkFile = watermarkFile.get_filename()

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
                width.set_value(self.origionalImageSize[1])
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
                width.set_value(self.origionalImageSize[1])
                filetype.set_active(2)

            width.set_sensitive(False)
            height.set_sensitive(False)
            filetype.set_sensitive(False)
            pngcrush.set_sensitive(False)
            quality.set_sensitive(False)


    def on_exportFormat_changed(self, combo):
        self.builder_ex.get_object('exportPngcrushEnabled').set_sensitive(combo.get_active() == 0)
        self.builder_ex.get_object('exportPngcrushEnabled').set_active(False)
        self.builder_ex.get_object('exportJpegQuality').set_sensitive(combo.get_active() == 1)


    def on_exportFocusChanged(self, box, whatever):
        if(self.exportLastChanged != self.builder_ex.get_object('exportStack').get_visible_child_name()):
            self.exportLastChanged = self.builder_ex.get_object('exportStack').get_visible_child_name()
            thread = threading.Thread(target=self._sefWait, args=(self.exportFile, self.exportWatermarkFile))
            thread.start()

    def _sefWait(self, f1, f2):
        time.sleep(0.1)
        GLib.idle_add(self.set_exportFiles, f1, f2)

    def set_exportFiles(self, f1, f2):
        try:
            self.builder_ex.get_object('exportSave').select_filename(f1)
        except:
            pass

        try:
            self.builder_ex.get_object('exportWatermarkFile').select_filename(f2)
        except:
            pass



    def on_exportExportButton_clicked(self, button):
        self.windowEx.hide()
        self.disableControls()
        self.updateProgress(0.0, False)
        self.builder.get_object('openButton').set_sensitive(False)

        # Get data and do it
        pngcrush = self.builder_ex.get_object('exportPngcrushEnabled').get_active()
        watermarkfile = self.builder_ex.get_object('exportWatermarkFile').get_filename()
        watermark = self.builder_ex.get_object('exportWatermarkSwitch').get_active()
        height = int(self.builder_ex.get_object('exportHeight').get_value())
        width = int(self.builder_ex.get_object('exportWidth').get_value())
        fileformat = self.builder_ex.get_object('exportFormat').get_active()
        filename = self.builder_ex.get_object('exportSave').get_filename()
        jpegQ = int(self.builder_ex.get_object('exportJpegQuality').get_value())
        watermarkPosition = self.builder_ex.get_object('exportWatermarkPosition').get_active()
        selectedPreset = self.builder_ex.get_object('exportPreset').get_active()
        thread = threading.Thread(target=self.exportImage, args=(self.on_exportComplete, width, height, fileformat, filename, watermark, watermarkfile, watermarkPosition,jpegQ ,pngcrush, selectedPreset))
        thread.start()

    def on_exportComplete(self, location):
        self.enableControls()
        self.hideProgress()
        self.showMessage(True, "Export Complete!", "Your edited photograph has been exported to '" + location + "'")
        self.builder.get_object('openButton').set_sensitive(True)


    ## Helper GUI Functions

    def showMessage(self, closeable, title, message, spinner = False):
        self.builder.get_object('messageTitle').set_text(title)
        self.builder.get_object('messageBody').set_text(message)
        self.builder.get_object('infobar').set_show_close_button(closeable)
        self.builder.get_object('messageReveal').set_reveal_child(True)
        if(spinner):
            self.builder.get_object('infoSpinner').start()
        else:
            self.builder.get_object('infoSpinner').stop()

    def hideMessage(self, sender = None, response = None):
        self.builder.get_object('messageReveal').set_reveal_child(False)


    def updateProgress(self, value, barSpin = False):
        self.builder.get_object('progressReveal').set_reveal_child(True)
        self.builder.get_object('progressBar').set_fraction(value)
        if(barSpin):
            self.builder.get_object('barSpinner').start()


    def hideProgress(self):
        self.builder.get_object('progressReveal').set_reveal_child(False)
        self.builder.get_object('barSpinner').stop()


    def disableControls(self):
        self.builder.get_object('controlReveal').set_sensitive(False)
        self.builder.get_object('zoomInButton').set_sensitive(False)
        self.builder.get_object('zoomOutButton').set_sensitive(False)
        self.builder.get_object('origionalSizeButton').set_sensitive(False)
        self.builder.get_object('previewOldImageButton').set_sensitive(False)
        self.builder.get_object('fitButton').set_sensitive(False)
        self.builder.get_object('exportButton').set_sensitive(False)
        self.builder.get_object('showHighPeaksButton').set_sensitive(False)
        self.builder.get_object('showLowPeaksButton').set_sensitive(False)

    def enableControls(self):
        self.builder.get_object('controlReveal').set_sensitive(True)
        self.builder.get_object('zoomInButton').set_sensitive(True)
        self.builder.get_object('zoomOutButton').set_sensitive(True)
        self.builder.get_object('origionalSizeButton').set_sensitive(True)
        self.builder.get_object('previewOldImageButton').set_sensitive(True)
        self.builder.get_object('fitButton').set_sensitive(True)
        self.builder.get_object('exportButton').set_sensitive(True)
        self.builder.get_object('showHighPeaksButton').set_sensitive(True)
        self.builder.get_object('showLowPeaksButton').set_sensitive(True)




    ## Backend Calls


    def focusStackImages(self, files, callback):
        print files
        fl = stack.focusStack(files)
        GLib.idle_add(self.showMessage, False, "Loading Stacked Image", "Focus stack complete, loading image.", True)
        self.loadImage(fl, callback)

    def loadImage(self, path, callback):
        self.imageFile = path
        self.image = cv2.imread(path, 2 | 1) #cv2.CV_LOAD_IMAGE_ANYDEPTH
        height, width = self.image.shape[:2]
        self.previewWidth = self.defaultPreviewWidth
        self.origionalImageSize = self.image.shape[:2]
        #self.previewWidth = width
        # Make image 1000px wide for editing
        if (width > self.previewWidth):
            ratio = float(self.previewWidth)/float(width)
            nw = self.previewWidth
            nh = height*ratio
            self.image = cv2.resize(self.image, (int(nw), int(nh)))

        self.loadedImage = self.image.copy()
        self.origionalImage = self.image.copy()
        cv2.imwrite("/tmp/phf-orig.tiff", self.origionalImage)

        self.bpp = int(str(self.image.dtype).replace("uint", ""))


        splitPath = path.split("/")
        GLib.idle_add(self._setTitle, splitPath[len(splitPath)-1] + " (" + str(self.bpp) + " Bit)");
        self.loadImageData(path)
        time.sleep(2)
        self.updateImage()
        GLib.idle_add(callback)


    def _setTitle(self, title):
        self.builder.get_object('headerBar').set_subtitle(title)


    def updatePreview(self, tryN = 0):
        try:
            GLib.idle_add(self._disableOldPreviewButton)

            height, width = self.image.shape[:2]
            ratio = self.previewWidth/width
            nh = height*ratio

            out = cv2.resize(self.image, (int(self.previewWidth), int(nh)))
            self.origionalImage = cv2.resize(self.loadedImage, (int(self.previewWidth), int(nh)))
            cv2.imwrite("/tmp/phf-preview.tiff", out)

            self.currentPB = GdkPixbuf.Pixbuf.new_from_file("/tmp/phf-preview.tiff")
            self.origionalPB = GdkPixbuf.Pixbuf.new_from_file_at_scale("/tmp/phf-orig.tiff", int(self.previewWidth), int(nh), True)
            GLib.idle_add(self._showImage, self.currentPB)

        except Exception as e:
            if(tryN < 10):
                self.updatePreview(tryN + 1)
            else:
                GLib.idle_add(self.showMessage, True, "Display Error", str(e))


    def _showImage(self, pb):
        self.builder.get_object('preview').set_from_pixbuf(pb)

    def _disableOldPreviewButton(self):
        self.builder.get_object('previewOldImageButton').set_active(False)

    def updateHist(self):
        pb = histogram.drawHistFor(self.image)
        GLib.idle_add(self._showHist, pb)

    def _showHist(self, pb):
        self.builder.get_object('histogram').set_from_pixbuf(pb)

    def showPeaks(self, dark, light, fromUpdateImage = False, reset = False):

        if(reset):
            self.updateImage()

        if(dark):
            self.image[(self.image == 0).all(axis=2)] = 2**self.bpp -2
        if(light):
            self.image[(self.image == 2**self.bpp -1).all(axis=2)] = 1

        if(not fromUpdateImage):
            self.updatePreview()


    def updateImage(self):
        self.operating = True
        time.sleep(0.5)
        if(self.triggeredWhileOperating == True):
            self.triggeredWhileOperating = False
            self.updateImage()
        else:
            GLib.idle_add(self.updateProgress, 0.05, True)
            self.image = self.origionalImage.copy()
            # Do things here
            GLib.idle_add(self.updateProgress, 0.1)
            self.image = self.updateContrast(self.image)

            GLib.idle_add(self.updateProgress, 0.2)
            self.image = self.updateDetailer(self.image)

            GLib.idle_add(self.updateProgress, 0.3)
            self.image = self.updateEdges(self.image)

            GLib.idle_add(self.updateProgress, 0.4)
            self.image = self.updateColour(self.image)

            GLib.idle_add(self.updateProgress, 0.5)
            self.image = self.updateBW(self.image)


            # Done doing things


            thread = threading.Thread(target=self.updateHist)
            thread.start()

            hp = self.builder.get_object("showHighPeaksButton").get_active()
            lp = self.builder.get_object("showLowPeaksButton").get_active()
            self.showPeaks(lp, hp, True)


            if(self.triggeredWhileOperating == True):
                self.triggeredWhileOperating = False
                thread = threading.Thread(target=self.updatePreview)
                thread.start()
                GLib.idle_add(self.updateProgress, 0.0)
                self.updateImage()
            else:
                self.operating = False
                GLib.idle_add(self.updateProgress, 0.9)
                self.updatePreview()
                GLib.idle_add(self.hideProgress)
                thread = threading.Thread(target=self.saveImageData)
                thread.start()



    def updateContrast(self, image):
        hb = self.builder.get_object('hb').get_value()
        hc = self.builder.get_object('hc').get_value()
        mb = self.builder.get_object('mb').get_value()
        mc = self.builder.get_object('mc').get_value()
        sb = self.builder.get_object('sb').get_value()
        sc = self.builder.get_object('sc').get_value()

        hb += self.builder.get_object('hbc').get_value()
        hc += self.builder.get_object('hcc').get_value()
        mb += self.builder.get_object('mbc').get_value()
        mc += self.builder.get_object('mcc').get_value()
        sb += self.builder.get_object('sbc').get_value()
        sc += self.builder.get_object('scc').get_value()

        hb += self.builder.get_object('brightness').get_value()
        mb += self.builder.get_object('brightness').get_value()
        sb += self.builder.get_object('brightness').get_value()

        hc += self.builder.get_object('contrast').get_value()
        mc += self.builder.get_object('contrast').get_value()
        sc += self.builder.get_object('contrast').get_value()

        return contrast.applyContrast(image, hb, hc, mb, mc, sb, sc)


    def updateColour(self, image):
        hs = self.builder.get_object('hs').get_value()
        ms = self.builder.get_object('ms').get_value()
        ss = self.builder.get_object('ss').get_value()

        rob = self.builder.get_object('rob').get_value()
        rhb = self.builder.get_object('rhb').get_value()
        rmb = self.builder.get_object('rmb').get_value()
        rsb = self.builder.get_object('rsb').get_value()

        gob = self.builder.get_object('gob').get_value()
        ghb = self.builder.get_object('ghb').get_value()
        gmb = self.builder.get_object('gmb').get_value()
        gsb = self.builder.get_object('gsb').get_value()

        bob = self.builder.get_object('bob').get_value()
        bhb = self.builder.get_object('bhb').get_value()
        bmb = self.builder.get_object('bmb').get_value()
        bsb = self.builder.get_object('bsb').get_value()



        hue = self.builder.get_object('hue').get_value()
        saturation = self.builder.get_object('saturation').get_value()

        return colours.applyColours(image, hue, saturation, hs, ms, ss, rob, rhb, rmb, rsb, gob, ghb, gmb, gsb, bob, bhb, bmb, bsb)


    def updateDetailer(self, image):
        hb = self.builder.get_object('dhb').get_value()
        hc = self.builder.get_object('dhc').get_value()
        mb = self.builder.get_object('dmb').get_value()
        mc = self.builder.get_object('dmc').get_value()
        sb = self.builder.get_object('dsb').get_value()
        sc = self.builder.get_object('dsc').get_value()

        s = self.builder.get_object('detailerS').get_value()
        d = self.builder.get_object('detailerD').get_value()
        if(self.builder.get_object('detailerSwitch').get_active()):
            return detailer.runDetailer(image, s, d, hb, hc, mb, mc, sb, sc)
        else:
            return image



    def updateEdges(self, image):

        s = self.builder.get_object('edgeS').get_value()
        t1 = self.builder.get_object('eth1').get_value()
        t2 = self.builder.get_object('eth2').get_value()
        if(self.builder.get_object('edgesSwitch').get_active()):
            return detailer.runEdges(image, s, t1, t2)
        else:
            return image



    def updateBW(self, image):

        mode = self.builder.get_object('bwCombo').get_active()
        r = self.builder.get_object('bwr').get_value()
        g = self.builder.get_object('bwg').get_value()
        b = self.builder.get_object('bwb').get_value()
        if(self.builder.get_object('bwSwitch').get_active()):
            return grayscale.applyBW(image, mode, r, g, b)
        else:
            return image

    def updateCLAHE(self, image):
        c = self.builder.get_object('claheC').get_value()
        g = self.builder.get_object('claheG').get_value()
        if(self.builder.get_object('claheSwitch').get_active()):
            return clahe.doCLAHE(image, c, g)
        else:
            return image


    def _nl(self, data):
        return str(float(data)) + "\n"

    def saveImageData(self):
        data = "%PHF%\n"

        path = self.imageFile.split("/")
        fname = path[len(path)-1]
        data += fname + "\n"

        for obj in self.objarr:
            try:
                data += self._nl(obj.get_value())
            except:
                data += self._nl(obj.get_active())

        #Save the file
        f = open(self.imageFile + ".phf", 'w')
        f.write(data)
        f.close


    def loadImageData(self, filename):

        if(os.path.isfile(filename + ".phf")):
            f = open(filename + ".phf", 'r')
            data = f.read()
            f.close()

            success = True

            dataarr = data.split('\n')
            if(dataarr[0] == "%PHF%"):
                img = dataarr[1]
                print "Setting data for " + img
                GLib.idle_add(self._setAll, dataarr)

            else:
                GLib.idle_add(self.showMessage, True, "Couldn't load associated .PHF file", "The file is invalid or currupt", False)
                GLib.idle_add(self._setAll, self.defaultData)
        else:
            GLib.idle_add(self._setAll, self.defaultData)



    def _setAll(self, data):
        for i, obj in enumerate(self.objarr):
            if(i <= len(self.objarr)-1):
                try:
                    obj.set_value(float(data[i+2]))
                except:
                    obj.set_active(float(data[i+2]))

    def _set(self, data, item):
        for i, obj in enumerate(self.objarr):
            if(i <= len(self.objarr)-1):
                if(item == obj):
                    try:
                        obj.set_value(float(data[i+2]))
                    except:
                        obj.set_active(float(data[i+2]))

    objarr = None

    def populateObjArr(self):
        self.objarr = [self.builder.get_object('hb'), self.builder.get_object('hc'), self.builder.get_object('mb'), self.builder.get_object('mc'), self.builder.get_object('sb'), self.builder.get_object('sc'), self.builder.get_object('hbc'), self.builder.get_object('hcc'), self.builder.get_object('mbc'), self.builder.get_object('mcc'), self.builder.get_object('sbc'), self.builder.get_object('scc'), self.builder.get_object('brightness'), self.builder.get_object('contrast'), self.builder.get_object('dhb'), self.builder.get_object('dhc'), self.builder.get_object('dmb'), self.builder.get_object('dmc'), self.builder.get_object('dsb'), self.builder.get_object('dsc'), self.builder.get_object('detailerS'), self.builder.get_object('detailerD'), self.builder.get_object('detailerSwitch'), self.builder.get_object('hue'), self.builder.get_object('saturation'), self.builder.get_object('hs'), self.builder.get_object('ms'), self.builder.get_object('ss'), self.builder.get_object('rob'), self.builder.get_object('rhb'), self.builder.get_object('rmb'), self.builder.get_object('rsb'), self.builder.get_object('gob'), self.builder.get_object('ghb'), self.builder.get_object('gmb'), self.builder.get_object('gsb'), self.builder.get_object('bob'), self.builder.get_object('bhb'), self.builder.get_object('bmb'), self.builder.get_object('bsb'), self.builder.get_object('edgesSwitch'), self.builder.get_object('edgeS'), self.builder.get_object('eth1'), self.builder.get_object('eth2'), self.builder.get_object('bwSwitch'), self.builder.get_object('bwCombo'), self.builder.get_object('bwr'), self.builder.get_object('bwg'), self.builder.get_object('bwb')]


    defaultData = ["%PHF%", "defaultImage", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 30.0, 15.0, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False, 30.0, 100.0, 200.0, False, 0.0, 0.33, 0.33, 0.33]




    def exportImage(self, callback, width, height, fileformat, filename, watermark, watermarkfile, positionValue, jpegQ, pngcrush, selectedPreset):
        # Load the origional image
        self.exportProgress(0.1, "Loading full sized photograph")
        im = cv2.imread(self.imageFile, 2 | 1) #cv2.CV_LOAD_IMAGE_ANYDEPTH

        # Resize Image
        self.exportProgress(0.2, "Resizing")
        im = cv2.resize(im, (width, height))

        # Apply Changes
        # Brightness and Contrast
        self.exportProgress(0.3, "Applying Changes: Brightness and Contrast")
        im = self.updateContrast(im)

        # Detailer
        self.exportProgress(0.4, "Applying Changes: Detailer")
        im = self.updateDetailer(im)

        # Detailer
        self.exportProgress(0.5, "Applying Changes: Edges")
        im = self.updateEdges(im)

        # Colours
        self.exportProgress(0.6, "Applying Changes: Colours")
        im = self.updateColour(im)

        # Detailer
        self.exportProgress(0.7, "Applying Changes: Black and White")
        im = self.updateBW(im)


        # Watermark
        if(watermark):
            padding = 75
            position = None
            self.exportProgress(0.8, "Applying Watermark")

            wi = cv2.imread(watermarkfile, -1) #Keep alpha
            wm = numpy.zeros(shape=(im.shape[0], im.shape[1], wi.shape[2]))

            bpp = int(str(im.dtype).replace("uint", ""))
            wbpp = int(str(wi.dtype).replace("uint", ""))
            wi = (wi/float(2**wbpp))*(2**bpp)


            iw = width
            ih = height
            wh, ww = wi.shape[:2]

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


            wm[position[1]:position[1] + wh, position[0]:position[0] + ww] = wi

            mask = (wm[0:,0:,3]).astype(im.dtype)

            mask = cv2.cvtColor(mask,cv2.COLOR_GRAY2BGR)

            im = (im*(-(mask/float(2**bpp)) + 1) + (wm[0:,0:,:3]*mask/float(2**bpp))).astype(self.image.dtype)


        # Save

        self.exportProgress(0.9, "Writing end result")
        fn = filename

        # PNG
        if(fileformat == 0):
            fn = filename
            if(not filename.endswith(".png")): fn = filename + ".png"
            # PNG Crush?
            if(pngcrush):
                cv2.imwrite("/tmp/precrush.png", im, (cv2.IMWRITE_PNG_COMPRESSION, 0))
                # Crush it
                self.exportProgress(0.95, "Writing end result: pngcrush")
                subprocess.call(["pngcrush", "-rem gAMA", "-rem cHRM", "-rem iCCP", "-rem sRGB" , "-m 0", "-l 9", "-fix", "-v", "-v", "/tmp/precrush.png", fn])

                # Flickr needs images < 200MB
                if(selectedPreset == 2):
                    self.exportProgress(0.98, "Checking file is under the 200MB limit")
                    if(os.path.getsize(fn) >= 200000000):
                        self.exportProgress(0.0, "Restarting export at reduced resolution of " + str(width*0.97) + " X " + str(height*0.97))
                        time.sleep(5)
                        exportImage(callback, width*0.97, height*0.97, fileformat, filename, watermark, watermarkfile, positionValue, jpegQ, pngcrush, selectedPreset)


            else:
                cv2.imwrite(fn, im, (cv2.IMWRITE_PNG_COMPRESSION, 9))


        # JPEG
        if(fileformat == 1):
            bpp = int(str(im.dtype).replace("uint", ""))
            self.exportProgress(0.95, "Writing end result: convert to 8 bit")
            im = (im/float(2**bpp))*255
            fn = filename
            if(not filename.endswith(".jpg")): fn = filename + ".jpg"

            cv2.imwrite(fn, im, (cv2.IMWRITE_JPEG_QUALITY, jpegQ))


        # TIFF
        if(fileformat == 2):
            fn = filename
            if((not filename.endswith(".tif")) and (not filename.endswith(".tiff"))): fn = filename + ".tiff"

            cv2.imwrite(fn, im)


        GLib.idle_add(callback, fn)



    def exportProgress(self, value, text):
        GLib.idle_add(self.showMessage, False, "Exporting...", text, True)
        GLib.idle_add(self.updateProgress, value)



def main():
    app = GUI()
    Gtk.main()

if __name__ == "__main__":
	sys.exit(main())

