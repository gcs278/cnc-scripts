# This script analyzes the parts of a cut job and creates a zinfo file
# Zinfo file is a custom formated file that contains where the machine should take index points
# This is part of the 2nd generation multi-zindex feature
import glob, sys
import re, math
import os, time, fileinput
from shutil import copyfile
import filecmp

def natural_sort(l): 
	convert = lambda text: int(text) if text.isdigit() else text.lower() 
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(l, key = alphanum_key)

#rootdir = 'C:\\Users\\Grant\\Google Drive\\GS_Custom_Woodworking'
rootdir = '/Users/grantspence/Google Drive/GS_Custom_Woodworking'
#rootdir = '\\\\vmware-host\\Shared Folders\\grantspence On My Mac\\Google Drive\\GS_Custom_Woodworking'
#archiveDir = rootdir + '\\GCode_Archive'
archiveDir = rootdir + '/GCode_Archive'
DEBUG=False

fileExtention=".gcode" 
regexStr="([G|g][1|0]([X|x](\-?(\d*\.)?\d+))?([Y|y](\-?(\d*\.)?\d+))?)([Z|z](\-?(\d*\.)?\d+))?([F|f](\-?(\d*\.)?\d+))?"
regex=re.compile(regexStr)

def getCenterPoint(gcodePath):
	xMax=None
	yMax=None
	xMin=None
	yMin=None
	firstTimeX=True
	firstTimeY=True
	with open(gcodePath) as file:
		for line in file:
			line_clean = line.strip()
			gcodeMatch = regex.match(line_clean)
			if gcodeMatch:
				# X
				if gcodeMatch.group(3):
					x = float(gcodeMatch.group(3))
					# Filter out X0Y0
					if x != 0.00:
						if firstTimeX:
							xMax=x
							xMin=x
							firstTimeX = False
						else:
							if x > xMax:
								xMax = x
							if x < xMin:
								xMin = x
				# Y
				if gcodeMatch.group(6):
					y = float(gcodeMatch.group(6))
					# Filter out X0Y0
					if x != 0.00:
						if firstTimeY:
							yMax=y
							yMin=y
							firstTimeY=False
						else:
							if y > yMax:
								yMax = y
							if y < yMin:
								yMin = y

	centerX = ((xMax - xMin) / 2) + xMin
	centerY = ((yMax - yMin) / 2) + yMin
	if DEBUG:
		print("xMax " + str(xMax))
		print("xMin " + str(xMin))
		print("yMax " + str(yMax))
		print("yMin " + str(yMin))
		print("CENTER X " + str(centerX))
		print("CENTER Y " + str(centerY))
	return (centerX,centerY)

for subdir, dirs, files in os.walk(rootdir):
	for file in files:
		if file.endswith(fileExtention):
			filePath = os.path.join(subdir, file)
			# See if the dir that contains the fragments (gcode parts) exits
			fileNoExtension=os.path.basename(os.path.splitext(filePath)[0])
			fragmentDir=subdir+ "/"+fileNoExtension
			if os.path.exists(fragmentDir):
				realZinfoFile=fragmentDir+"/"+fileNoExtension+".zinfo"
				workingZinfoFile=realZinfoFile+".tmp"
				if os.path.exists(workingZinfoFile):
					os.remove(workingZinfoFile)

				centers=[]
				# Get all the center points
				files=natural_sort(os.listdir(fragmentDir))
				# print files
				for fragmentFile in natural_sort(os.listdir(fragmentDir)):
					if fragmentFile.endswith(".gcode") and "COMPILED" not in fragmentFile and "000" not in fragmentFile:
						centerPoint = getCenterPoint(fragmentDir+"/"+fragmentFile)
						centers.append((fragmentFile, centerPoint))

				# Check that we actually have a file
				if not centers:
					print "ERROR: Can't make zinfo file cause no Gcode Files in " + fragmentDir
					exit()

				for center in centers:
					# Write the zinfo file
					with open(workingZinfoFile,"a") as file:
						file.write(center[0] + "\n")
						file.write(str(center[1][0]) + "\n")
						file.write(str(center[1][1]) + "\n")
				try:
					if os.path.exists(realZinfoFile):
						# if it already exists, compare and only recreate if 
						if not filecmp.cmp(workingZinfoFile, realZinfoFile):
							print "RE-Creating zinfo file for " + fragmentDir
							copyfile(workingZinfoFile, realZinfoFile)
					else:
						print "Creating zinfo file for " + fragmentDir
						copyfile(workingZinfoFile, realZinfoFile)
					os.remove(workingZinfoFile)
				except OSError as e:
					print "ERROR: Couldn't copy " + workingZinfoFile + " to " + realZinfoFile
					# file.write(str(centerPoint[0]) + " " + str(centerPoint[1]) + " " + fragmentFile + "\n")
			