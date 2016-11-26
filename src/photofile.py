#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-
#
# photofile.py
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
from gi.repository import Gtk
import ast


def log(message):
	print "[PHOTOFILE.PY] " + message


def saveFile(imagepath, builder):
	data = "%PHF-RF%\n"

	path = imagepath.split("/")
	fname = path[len(path)-1]
	data += fname + "\n"

	saveDict = {}

	components = getComponents()

	for component in components:
		obj = builder.get_object(component)
		objdata = None
		try:
			objdata = obj.get_value()
		except:
			objdata = obj.get_active()

		saveDict[component] = objdata

	data += str(saveDict)

	#Save the file
	f = open(imagepath + ".phf", 'w')
	f.write(data)
	f.close()


def loadFile(filename, builder):
	applyDefaults(builder)

	f = open(filename)
	data = f.read()
	f.close()
	
	dataLines = data.split("\n")
	
	if(dataLines[0] == "%PHF-RF%"):
		log("Revised Format")
		dictData = ast.literal_eval(dataLines[2])
		applyDict(dictData, builder)

		return dataLines[1]

	elif(dataLines[0] == "%PHF%"):
		log("Legacy File")
		legacyLoad(builder, filename)
		return dataLines[1]

	else:
		return None



def applyDict(dictData, builder):

	for key in dictData:
		try:
			obj = builder.get_object(key)
			try:
				obj.set_value(dictData[key])
			except:
				obj.set_active(dictData[key])
		
		except:
			log("Unable to set key '%s'" % key)


defaults = {'hb': 0.0, 'hc': 0.0, 'mb': 0.0, 'mc': 0.0, 'sb': 0.0, 'sc': 0.0, 'hbc': 0.0, 'hcc': 0.0, 'mbc': 0.0, 'mcc': 0.0, 'sbc': 0.0, 'scc': 0.0, 'brightness': 0.0, 'contrast': 0.0, 'dhb': 0.0, 'dhc': 0.0, 'dmb': 0.0, 'dmc': 0.0, 'dsb': 0.0, 'dsc': 0.0, 'detailerS': 30.0, 'detailerD': 15.0, 'detailerSwitch': False, 'hue': 0.0, 'saturation': 0.0, 'hs': 0.0, 'ms': 0.0, 'ss': 0.0, 'rob': 0.0, 'rhb': 0.0, 'rmb': 0.0, 'rsb': 0.0, 'gob': 0.0, 'ghb': 0.0, 'gmb': 0.0, 'gsb': 0.0, 'bob': 0.0, 'bhb': 0.0, 'bmb': 0.0, 'bsb': 0.0, 'edgesSwitch': False, 'edgeS': 30.0, 'eth1': 100.0, 'eth2': 200.0, 'bwSwitch': False, 'bwCombo': 0.0, 'bwr': 0.33, 'bwg': 0.33, 'bwb': 0.33, 'hbl': 0.5, 'mbl': 0.5, 'sbl': 0.5, 'chbl': 0.5, 'cmbl': 0.5, 'csbl': 0.5, 'tonemapSwitch': False, 'tms': 90, 'tmb': 10, 'tmcs': 75, 'tmtp': False}


def getComponents():
	return list(defaults.keys())

def applyDefaults(builder):
	log("Applying Defaults")
	applyDict(defaults, builder)


def resetObject(obj, builder):
	name = findName(obj, builder)
	
	try:
		obj.set_value(defaults[name])
	except:
		obj.set_active(defaults[name])


def findName(obj, builder):
	for key in defaults:
		if(builder.get_object(key) == obj):
			return key

	return None
		





### LEGACY SUPPORT ###


def legacyLoad(builder, filename):

	f = open(filename, 'r')
	data = f.read()
	f.close()

	dataarr = data.split('\n')
	if(dataarr[0] == "%PHF%"):
		img = dataarr[1]
		_setAll(builder, dataarr)

	else:
		_setAll(builder, defaultLegacyData)



def _setAll(builder, data):
	objarr = getObjArr(builder)
	for i, obj in enumerate(objarr):
		if(i <= len(objarr)-1):
			try:
				obj.set_value(float(data[i+2]))
			except:
				obj.set_active(float(data[i+2]))


objarr = None

def getObjArr(builder):
	return [builder.get_object('hb'), builder.get_object('hc'), builder.get_object('mb'), builder.get_object('mc'), builder.get_object('sb'), builder.get_object('sc'), builder.get_object('hbc'), builder.get_object('hcc'), builder.get_object('mbc'), builder.get_object('mcc'), builder.get_object('sbc'), builder.get_object('scc'), builder.get_object('brightness'), builder.get_object('contrast'), builder.get_object('dhb'), builder.get_object('dhc'), builder.get_object('dmb'), builder.get_object('dmc'), builder.get_object('dsb'), builder.get_object('dsc'), builder.get_object('detailerS'), builder.get_object('detailerD'), builder.get_object('detailerSwitch'), builder.get_object('hue'), builder.get_object('saturation'), builder.get_object('hs'), builder.get_object('ms'), builder.get_object('ss'), builder.get_object('rob'), builder.get_object('rhb'), builder.get_object('rmb'), builder.get_object('rsb'), builder.get_object('gob'), builder.get_object('ghb'), builder.get_object('gmb'), builder.get_object('gsb'), builder.get_object('bob'), builder.get_object('bhb'), builder.get_object('bmb'), builder.get_object('bsb'), builder.get_object('edgesSwitch'), builder.get_object('edgeS'), builder.get_object('eth1'), builder.get_object('eth2'), builder.get_object('bwSwitch'), builder.get_object('bwCombo'), builder.get_object('bwr'), builder.get_object('bwg'), builder.get_object('bwb'), builder.get_object('hbl'), builder.get_object('mbl'), builder.get_object('sbl'), builder.get_object('chbl'), builder.get_object('cmbl'), builder.get_object('csbl'), builder.get_object('tonemapSwitch'), builder.get_object('tms'), builder.get_object('tmb'), builder.get_object('tmcs'), builder.get_object('tmtp')]


defaultLegacyData = [None, None, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 30.0, 15.0, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False, 30.0, 100.0, 200.0, False, 0.0, 0.33, 0.33, 0.33, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, False, 90, 10, 75, False]



