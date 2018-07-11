##############################################################################
# 4/16/18
# Grant Spence
# BayCoast Designs All Rights Reserved
# This script makes a given gcode more verbose
#    More verbose means: 1. No implied X,Y,or Z, every gcode has X Y Z values
#                        2. Fill long runs on X Y Z using desiredResolution
#    This script benefits our z-multi processes
#    Arguments: Any number of files that will be modified inline
##############################################################################
import glob, sys
import os, time, fileinput
import re, math
import shutil

# Global Variables
rootdir = 'C:\\Users\\Shop\\Google Drive\\GS_Custom_Woodworking'
tmpdir = 'C:\\tmp\\'
DEBUG=False
MAC=False

if sys.platform == "darwin":
	MAC=True

if MAC:
	rootdir = '/Users/grantspence/Google Drive/GS_Custom_Woodworking'
	tmpdir = '/tmp/gcode_tmp/'
	# DEBUG=True

# How we backup the file being operated on
bakFileExtension = ".nonverbose.bak"

# Modify this to change the "resolution" aka distance between gcodes
desiredResolution = 0.1

def makeGcodeVerbose(gcodeFile):
	with open(logFilePath, 'a') as logFile:
		logFile.write("\n-----------------------------------------------------------------------------\n")
		logFile.write("Current Time:\t" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + "\n")
	# Make a back up if it doesn't exist 
	# if not os.path.exists(gcodeFile + bakFileExtension):
	# 	shutil.copyfile(gcodeFile, gcodeFile + bakFileExtension)

	fileBaseName=os.path.splitext(os.path.basename(gcodeFile))[0]
	workingFile=fileBaseName+"_WORKING-VERBOSE.gcode"
	workingFilePath=tmpdir+workingFile

	if not os.path.exists(tmpdir):
	    os.makedirs(tmpdir)

	if os.path.exists(workingFilePath):
		os.remove(workingFilePath)

	regexStr="^(([G|g][1|0])([X|x](\-?(\d*\.)?\d+))?([Y|y](\-?(\d*\.)?\d+))?)([Z|z](\-?(\d*\.)?\d+))?([F|f](\-?(\d*\.)?\d+))?$"
	regex=re.compile(regexStr)

	# Touch temp file to temp location so we don't modify the real one
	with open(workingFilePath, 'a'):
		os.utime(workingFilePath, None)

	previousX = None
	previousY = None
	previousZ = None
	previousLine = None
	with open(gcodeFile) as file:
		for line in file:
			line_clean = line.strip()
			match = regex.match(line_clean)
			if match:
				if DEBUG:
					print "---------------------------------"
				########### Think of this in Steps ###########################################
				### Step 1: Make Gcode explicit
				###        i.e. G0X1.235Z0.124 should become G0X1.234Y4.245Z0.124 using previous value
				### Step 2: See if the gcode has been reduced
				###        i.e. previous G0X10.000 and now G0X1.000, insert G0X9.00 G0X8.00 (depending on resolution)

				resolutionX = None
				resolutionY = None
				resolutionZ = None
				################ Step #1 ####################
				################### X ###################
				x = float(match.group(4)) if match.group(4) else None

				# If both are None, then we don't have a Y currently, and never had, so must skip
				if x is None and previousX is None:
					if DEBUG:
						print "NO X instruction, NO last X"
				# If current y is None, but we have a previous y, then subsitute the previous y
				elif x is None and previousX is not None:
					# We just have X or Z instruction and no Y, so use last Y
					if DEBUG:
						print "NO X instruction this time, using previous X value"
					x = previousX
				elif x is not None and previousX is not None:
					resolutionX = x - previousX
				
				################### Y ###################
				y = float(match.group(7)) if match.group(7) else None

				# If both are None, then we don't have a Y currently, and never had, so must skip
				if y is None and previousY is None:
					if DEBUG:
						print "NO Y instruction, NO last Y"
				# If current y is None, but we have a previous y, then subsitute the previous y
				elif y is None and previousY is not None:
					# We just have X or Z instruction and no Y, so use last Y
					if DEBUG:
						print "NO Y instruction this time, using previous y value"
					y = previousY
				elif y is not None and previousY is not None:
					resolutionY = y - previousY

				################### Z ###################
				z = float(match.group(10)) if match.group(10) else None

				# If both are None, then we don't have a Y currently, and never had, so must skip
				if z is None and previousZ is None:
					if DEBUG:
						print "NO Z instruction, NO last Z"
				# If current y is None, but we have a previous y, then subsitute the previous y
				elif z is None and previousZ is not None:
					# We just have X or Z instruction and no Y, so use last Y
					if DEBUG:
						print "NO Z instruction this time, using previous Z value"
					z = previousZ
				elif z is not None and previousZ is not None:
					resolutionZ = z - previousZ

				####### F Section ############
				f = float(match.group(13)) if match.group(13) else None

				####### G0/G1 Section (whole thing, not just number) #########
				gArg = str(match.group(2))

				############### Now Build the gCode ###########################
				xArg = "X" + "{0:.4f}".format(x) if x is not None else ""
				yArg = "Y" + "{0:.4f}".format(y) if y is not None else ""
				zArg = "Z" + "{0:.4f}".format(z) if z is not None else ""
				fArg = "F" + "{0:.1f}".format(f) if f is not None else ""
				newLine = gArg + xArg + yArg + zArg + fArg

				# Check if we have a resolution problem
				if ( (resolutionX is not None and resolutionX > desiredResolution) or \
					(resolutionY is not None and resolutionY > desiredResolution) or \
					(resolutionZ is not None and resolutionZ > desiredResolution) ) \
					and z < 0.10:

					# The furthest away value X Y or Z
					maxDifference = max(resolutionX, resolutionY, resolutionZ)
					# insertsNeeded is the minimum amount of "rounds" or inserts needed to achieve desired resolution
					# Other axis that have smaller distances, will have higher resolutions
					insertsNeeded = int(math.ceil(maxDifference / desiredResolution) )

					# The resolutions we efficently get, should be under the desired resolution
					effectiveResolution = float(maxDifference / insertsNeeded)
					if DEBUG:
						print "!!!!!!!!!!!!!!!! RESOLUTION INTERPOLATION !!!!!!!!!!!!!!!!"
						print "ResolutionX:\t" + str(resolutionX)
						print "ResolutionY:\t" + str(resolutionY)
						print "ResolutionZ:\t" + str(resolutionZ)
						print "Inserts Needed\t" + str(insertsNeeded)
						print "Effective resolution: " + str(effectiveResolution)
					#y: 9 - 1 = 8
					#8 / .5 = 16

					#x: 3 - 1 = 2
					insertX = x
					insertY = y
					insertZ = z
					stepX = (resolutionX / insertsNeeded) if resolutionX is not None else None
					stepY = (resolutionY / insertsNeeded) if resolutionY is not None else None
					stepZ = (resolutionZ / insertsNeeded) if resolutionZ is not None else None
					# if DEBUG:
					# 	print "StepX:\t" + str(stepX)
					# 	print "StepY:\t" + str(stepY)
					# 	print "StepZ:\t" + str(stepZ)

					insertLines=[]
					for i in range(0,insertsNeeded):
						if resolutionX is not None:
							# stepX is the amount we should step back
							insertX = insertX - stepX
						if resolutionY is not None:
							# stepX is the amount we should step back
							insertY = insertY - stepY
						if resolutionZ is not None:
							# stepX is the amount we should step back
							insertZ = insertZ - stepZ

						# Create the new arguments, if no inserts need on the axis, use the original args
						insertCleanX = "{0:.4f}".format(insertX)
						insertCleanY = "{0:.4f}".format(insertY)
						insertCleanZ = "{0:.4f}".format(insertZ)

						xInsertArg = "X" + insertCleanX if insertX is not None else xArg
						yInsertArg = "Y" + insertCleanY if insertY is not None else yArg
						zInsertArg = "Z" + insertCleanZ if insertZ is not None else zArg
						newInsertLine = gArg + xInsertArg + yInsertArg + zInsertArg + fArg

						# insert in the begining, that way it is pre-sorted for us
						insertLines.insert(0,newInsertLine)

					if float(insertCleanX) != previousX or float(insertCleanY) != previousY or float(insertCleanZ) != previousZ:
						print "LOGIC ERROR: Resolution Interpolation didn't perform walk back successfully"
						print "Previous Line:\t" + previousLine
						for insertLine in insertLines:
							print "INSERTING:\t" + insertLine
						print "Current Line:\t" + newLine
						quit()

					if DEBUG:
						print "Previous Line:\t" + previousLine
						for insertLine in insertLines:
							print "INSERTING:\t" + insertLine
						print "Current Line:\t" + newLine

					# Insert the newly created lines into the file BEFORE we write our current line
					# Skip first line, cause that is equal to our previous line
					for insertLine in insertLines[1:]:
						with open(workingFilePath,"a") as file:
							file.write(insertLine + "\n")

				# Write the modified line to the file
				with open(workingFilePath,"a") as file:
					file.write(newLine + "\n")

				if DEBUG:
					print "OLD GCODE: " + str(line_clean)
					print "NEW GCODE: " + str(newLine)

				previousX = x
				previousY = y
				previousZ = z
				previousLine = newLine
			else:
				# We didn't match, so unmodified line
				with open(workingFilePath,"a") as file:
					file.write(line_clean + "\n")
	
	# Copy the WORKING copy to the ACTUAL copy
	try:
		shutil.copyfile(workingFilePath, gcodeFile)
		print "Made " + gcodeFile + " verbose"
	except OSError as e:
		print "ERROR: Couldn't copy " + workingFilePath + " to " + gcodeFile
		print "ERROR: You are going to to have to copy it yourself"

if MAC:
	log_dir=rootdir+"/logs"
else:
	log_dir=rootdir+"\\logs"

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

if MAC:
	logFilePath = log_dir + "/y-split-logs-MACDEBUG.log"	
else:
	logFilePath = log_dir + "\\y-split-logs.log"	

# First check arguments
for gcodeFile in sys.argv[1:]:
	if not os.path.exists(gcodeFile):
		print "ERROR: Argument " + gcodeFile + " does not exist"
		sys.exit(1)
	elif not gcodeFile.endswith('.gcode'):
		print "ERROR: Argument " + gcodeFile + " doesn't have extension .gcode"
		sys.exit(1)

for gcodeFile in sys.argv[1:]:
	makeGcodeVerbose(gcodeFile)