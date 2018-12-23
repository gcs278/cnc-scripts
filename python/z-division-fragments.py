import glob, sys
import os, time, fileinput
import re, math
import shutil
import subprocess
import requests
from tts_watson.TtsWatson import TtsWatson
from os.path import expanduser
home = expanduser("~")
# Home on Virtual Machine
if os.path.exists("Z:\\grantspence On My Mac"):
	home = "Z:\\grantspence On My Mac"

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

# Global Variables
rootdir = home + '\\Google Drive\\GS_Custom_Woodworking'

argFileDir="C:\\Mach3\\argFiles\\"
argFileGlob=argFileDir + "z-multi*.txt"
tmpdir = 'C:\\tmp\\'
audioDir = rootdir + "\\CNC_Data\\audio_clips\\"
playwave = rootdir + "\\cnc-scripts\\python\\playwave.py"
python = "C:\\Python27\\python.exe"
DEBUG=False
MAC=False
if sys.platform == "darwin":
	MAC=True
targetFile=""
wavConnetionError="connectionError.wav"
wavInterpolating="interpolating.wav"
wavSuccess="trump_bing_bing_bong.wav"
wavError="donald-trump-wrong-sound-effect.wav"
slash = "\\"
interpolingProc = None
# validation variables
WARNING_Z=0.02
ERROR_Z=0.05
FATAL_Z=0.5

# Initialize Watson
ttsWatson = TtsWatson('990e8a8e-0727-4d98-93a8-921a27d5202d', 'sdcoWYFtMXEA', 'en-US_MichaelVoice')

# Mac specific logic
if MAC:
	rootdir = '/Users/grantspence/Google Drive/GS_Custom_Woodworking'
	tmpdir = '/tmp/gcode_tmp/'
	targetFile=rootdir+"/GCode/Square_Signs/She_is_clothed_copy.gcode"
	argFileDir="/tmp/"
	argFileGlob=argFileDir + "z-multi*.txt"
	audioDir = rootdir + "/CNC_Data/audio_clips/"
	slash = "/"
	playwave = rootdir + "/CNC_Data/playwave.py"
	python = "python"
	DEBUG=True

regexStr="([G|g][1|0]([X|x](\-?(\d*\.)?\d+))?([Y|y](\-?(\d*\.)?\d+))?)([Z|z](\-?(\d*\.)?\d+))?([F|f](\-?(\d*\.)?\d+))?([S|S](\-?\d+))?([M|m](\-?\d+))?"
gcodeRegex=re.compile(regexStr)

gcodeHeader=["T1","M1031","G17","G20","G90","G0S16000M3"]
gcodeFooter=["G0X0.0000Y0.0000", "M1030","M02"]

# Log file logic
log_dir=rootdir + slash + "logs"
if not os.path.exists(log_dir):
	os.makedirs(log_dir)

if os.path.exists("Z:\\grantspence On My Mac"):
	logFilePath = log_dir + slash + "z-division-logs-DEBUG.log"	
else:
	logFilePath = log_dir + slash + "z-division-logs.log"	
logFile = open(logFilePath, 'a')

# Function to speak messages with a voice
# handles connection errors
def handleError(message, fatal=False):
	interpolingProc.kill()
	print message
	logFile.write(message + '\n')
	message = message.replace("gcode"," gee code")

	# WRONG WRONG WRONG - Audio
	if fatal:
		subprocess.call([python,playwave,audioDir + wavError])
		subprocess.call([python,playwave,audioDir + wavError])
		subprocess.call([python,playwave,audioDir + wavError])
	try:
		# Turn off output from this command
		sys.stdout = open(os.devnull, 'w')
		sys.stderr = open(os.devnull, 'w')
		ttsWatson.play(message)
		sys.stdout = sys.__stdout__
		sys.stderr = sys.__stderr__
	except requests.exceptions.ConnectionError as e:
		sys.stderr = sys.__stderr__
		sys.stdout = sys.__stdout__
		subprocess.Popen([python,playwave,audioDir + wavConnetionError])
		print "ERROR: Could not connect to the Watson API! No internet connection!"

def mainLogic(zZeros):
	fileBaseName=os.path.splitext(os.path.basename(targetFile))[0]
	tmpFile=fileBaseName+"_TEMPORARY_COPY.gcode"
	tmpTmpFile=fileBaseName+"_WORKING.gcode"
	tmpFileName=tmpdir+tmpFile
	tmpTmpFileName=tmpdir+tmpTmpFile

	if not os.path.exists(tmpdir):
		os.makedirs(tmpdir)

	if os.path.exists(tmpFileName):
		os.remove(tmpFileName)

	if os.path.exists(tmpTmpFileName):
		os.remove(tmpTmpFileName)

	coordList=[]
	slopes=[]

	prev_yLoc=0
	prev_zZero=0
	for yLoc, zZero in zZeros:
		if prev_yLoc != 0 or prev_zZero != 0:
			if yLoc >= yCenter:
				slope=findSlope(prev_yLoc,prev_zZero,yLoc,zZero)
			else:
				slope=-findSlope(prev_yLoc,prev_zZero,yLoc,zZero)
			slopes.append((prev_yLoc,slope))
		prev_yLoc = yLoc
		prev_zZero = zZero

	# Add this fake one inthere for last slope to be calculated
	# Otherwise for loop stops short
	# TODO fix this
	slopes.append((0,1))
	logFile.write("Slopes:\t\t\t" + str(slopes) + "\n")
	# Test function
	#for x in xrange(100):
		#print findNewOffset(x*0.1,slopes, zZeros)


	# Touch temp file to temp location so we don't modify the real one
	with open(tmpTmpFileName, 'a'):
		os.utime(tmpTmpFileName, None)

	previousY = 0
	with open(targetFile) as file:
		for line in file:
			line_clean = line.strip()
			match = gcodeRegex.match(line_clean)
			if match:
				if DEBUG:
					print "--------------------------------"
					print "OLD GCODE: " + str(line_clean)

				#x = float(match.group(1)) # Don't need X yet
				######### Y SECTION ###########

				y = 0
				if match.group(6):
					y = float(match.group(6))
				#DEBUG = True if y > 8.8 and y < 9.8 else False
				if y == 0 and previousY != 0:
					# We just have Z instruction and no X or Y, so use last Y
					if DEBUG:
						print "NO Y instruction, using previous"
					y = previousY
				elif y == 0 and previousY == 0:
					if DEBUG:
						print "NO Y instruction, NO last Y, skipping"
					# if we just have Z, no Y values, we don't do anything
					with open(tmpTmpFileName,"a") as file:
						file.write(line_clean + "\n")
					continue
				previousY = y

				if DEBUG:
					print "Y Value: " + bcolors.FAIL + str(y)+ bcolors.ENDC

				####### F Section ############
				f = ""
				if match.group(11):
					f = str(match.group(11))

				######## Z SECTION ############
				if match.group(9):
					z = float(match.group(9))
				else:
					if DEBUG:
						print "NO Z instruction, skipping"
					with open(tmpTmpFileName,"a") as file:
						file.write(line_clean + "\n")
					continue
				zOffset=findNewOffset(y,slopes, zZeros)
				newZ=round(z+zOffset,4)
				newLine=str(match.group(1) + "Z" + str(newZ)) + f
				
				# Write the modified line to the fil
				with open(tmpTmpFileName,"a") as file:
					file.write(newLine + "\n")

				if DEBUG:
					print "Z Value: " + str(z)
					print "Offset: " + str(zOffset) 
					print "New Z: " + str(newZ)
					print "NEW GCODE: " + str(newLine)
					print "ZEROS: " + str(zZeros)
					print "SLOPES: " + str(slopes)
			else:
				# We didn't match, so unmodified line
				with open(tmpTmpFileName,"a") as file:
					file.write(line_clean + "\n")
	print "FINSIHED ZEROING"
	
	# Copy the WORKING copy to the ACTUAL temp copy
	shutil.copyfile(tmpTmpFileName, tmpFileName)
	return tmpFileName

def findSlope(x1, y1, x2, y2):
	m = (y2-y1)/(x2-x1)
	return m

def findNewOffset(y, slopes, zeros):
	mySlope=0
	prev_yLoc=0
	prev_slope=0

	# Max and Min
	maxY=max(zeros)[0]
	minY=min(zeros)[0]

	# If greater than max, just use max value
	if y > maxY:
		for yLoc, zero in zeros:
			if maxY == yLoc:
				return zeros[0][1]

	# If less than min, just use min value
	if y < minY:
		for yLoc, zero in zeros:
			if minY == yLoc:
				return zeros[-1][1]

	# This logic to find the relevant slope
	for yLoc, slope in slopes:
		if prev_yLoc != 0 and prev_slope != 0:
			if y <= prev_yLoc and y > yLoc:
				mySlope = prev_slope
		prev_yLoc = yLoc
		prev_slope = slope
	# y=mx+b
	if y > yCenter:
		newOffset = mySlope*(y-yCenter)
	else:
		newOffset = mySlope*(yCenter-y)
	return newOffset

# Function that take our standard regex match and applies the provided offset
# to build a new gcode string
def gcodeBuilder(match, xJigOffset=0, yJigOffset=0, zOffset=0):
	######### X Section - Apply jig X offset ############
	xArg = ""
	if match.group(3):
		x = float(match.group(3))
		newX = x+xJigOffset
		xArg = "X" + "{0:.4f}".format(newX)

	######### Y Section - Apply jig Y offset ############
	yArg = ""
	if match.group(6):
		y = float(match.group(6))
		newY = y + yJigOffset
		yArg = "Y" + "{0:.4f}".format(newY)

	######### Z Section - Apply double jig Z offset ############
	zArg = ""
	if match.group(9):
		z = float(match.group(9))
		newZ=z+zOffset
		zArg = "Z" + "{0:.4f}".format(newZ)

	######### F Section ############
	fArg = ""
	if match.group(11):
		fArg = str(match.group(11))
	
	# Print new adjusted new gcode
	gArg = str(match.group(0)[:2]) # Get's either G0 or G1
	newGcode = gArg + xArg + yArg + zArg + fArg
	return newGcode

# Function combines fragmentated multi z process files into a single gcode
def combineFragments(realZindex, fragmentsDir, jigFragments, jigs):
	timestr = time.strftime("%Y%m%d-%H%M%S")
	parentName = os.path.splitext(os.path.basename(fragmentsDir))[0]
	fragmentsDirTmp=fragmentsDir + slash + "fragments-" + timestr

	# Clean up fragments-* old directories
	for fragTmpToDelete in glob.glob(fragmentsDir + slash + "fragments-*"):
		try:
			# This is stupid, but Google Drive puts Icon/r files in my folders,
			# so they can't be deleted on windows, unless I use DOS
			if not MAC:
				command='rmdir "'+ fragTmpToDelete + '" /S /Q '
				subprocess.call(command, shell=True)
			else:
				shutil.rmtree(fragTmpToDelete, ignore_errors=True) 
		except OSError as e:
			print "ERROR: Can't remove " + fragTmpToDelete
			print e

	os.mkdir(fragmentsDirTmp)
	combinedFragmentsFile=fragmentsDir + slash + parentName + "_COMPILEDFRAGMENTS_"+timestr+".gcode"

	# Clean up compiledfragments files, we won't need to use them again
	for compFragFilesOld in glob.glob(fragmentsDir + slash + "*_COMPILEDFRAGMENTS_*"):
		try:
			os.remove(compFragFilesOld)
		except OSError as e:
			print "ERROR: Can't remove " + compFragFilesOld
			print e

	# Open the combo file that includes EVERYthing compiled
	with open(combinedFragmentsFile,"a") as outFile:
		# Write our standard gcode header
		for gcode in gcodeHeader:
			outFile.write(gcode + '\n')

		# For each of jigs, write a new balanced gcode
		jigCount = 0
		for jig in jigs:
			# For each jig, get all of the fragments
			for fragment in jigFragments[jigCount][1]:
				fileName = fragment[0]
				fragmentZ = float(fragment[1])
				xJigOffset = float(jig[0])
				yJigOffset = float(jig[1])
				# Offset that should be applied to Z
				zOffset = fragmentZ - realZindex
				fragmentFile = fragmentsDir + slash + fileName
				if DEBUG:
					print("Fragment:\t" + fileName)
					print("RealZIndex:\t" + str(realZindex))
					print("My Z:\t\t" + str(fragmentZ))
					print("zOffset:\t"+ str(zOffset))
					print("xJigOffset:\t" + str(xJigOffset))
					print("yJigOffset:\t" + str(yJigOffset))

				# First open the fragment piece file for reading
				with open(fragmentFile) as file:
					# Then write also a new individual fragment file (for debuging or fixing errors)
					with open(fragmentsDirTmp + slash + "J" + str(jigCount) + "-" + fileName,"a") as individualFragmentFile:
						# Write our standard gcode header to individual fragmentn
						for gcode in gcodeHeader:
							individualFragmentFile.write(gcode + '\n')

						# Read each GCODE command
						for line in file:
							line_clean = line.strip()

							if line_clean == "G91":
								messagebox.showerror("Warning!","G91 is present in " + n + " I didn't write the app with that in mind.")

							if not any(line_clean in s for s in gcodeHeader) and not any(line_clean in s for s in gcodeFooter):
								match = gcodeRegex.match(line_clean)

								# Get X and Y ONLY for knowing if they both 0 to not print
								if match.group(6) and match.group(3):
									y = float(match.group(6))
									x = float(match.group(3))
									if x == 0.00 and y == 0.00:
										continue

								newGcode = gcodeBuilder(match,xJigOffset,yJigOffset,zOffset)
								outFile.write(newGcode + "\n")
								individualFragmentFile.write(newGcode + "\n")

						# Write our standard gcode footer on the INDIVIDUAL FILES
						for gcode in gcodeFooter:
							individualFragmentFile.write(gcode + '\n')
			jigCount += 1

		# Write our standard gcode footer on the COMBO file
		for gcode in gcodeFooter:
			outFile.write(gcode + '\n')
	return combinedFragmentsFile

def doubleJigSimpleZ(doubleJigXoff, doubleJigYoff, realZindex, secondZindex, targetFile):
	fileBaseName=os.path.splitext(os.path.basename(targetFile))[0]
	tmpFile=fileBaseName+"_X2_TEMPORARY_COPY.gcode"
	tmpFileName=tmpdir+tmpFile

	# Clean up
	if not os.path.exists(tmpdir):
		os.makedirs(tmpdir)
	if os.path.exists(tmpFileName):
		os.remove(tmpFileName)

	# First go through and basically copy
	with open(targetFile) as file:
		for line in file:
			line_clean = line.strip()
			match = gcodeRegex.match(line_clean)

			# Don't print gcode footer of lines yet
			if any(line_clean in s for s in gcodeFooter):
				continue

			with open(tmpFileName,"a") as file:
				file.write(line_clean + "\n")

	zOffset = secondZindex - realZindex 

	if DEBUG:
		print "Double Jig Simple Z"
		print "Z Offset" + str(zOffset)

	# Second add the second jig file, with the offset
	with open(targetFile) as file:
		for line in file:
			line_clean = line.strip()
			match = gcodeRegex.match(line_clean)

			newLine=line_clean
			# Don't print any gcode header lines
			if any(line_clean in s for s in gcodeHeader):
				continue

			# if we don't match, just print it
			if match:
				# Don't print any S16000 lines
				if match.group(15):
					continue

				newLine = gcodeBuilder(match,doubleJigXoff,doubleJigYoff,zOffset)

			with open(tmpFileName,"a") as file:
				file.write(newLine + "\n")
	return tmpFileName

try:
	while True:
		try:
			fileExists=False #os.path.exists(argFile)
			files = list(glob.glob(argFileGlob))
			for file in files:
				if not os.path.exists(file+".done"):
					fileExists=True
					argFile=file
			
			if fileExists:
				if DEBUG:
					print("Processing ArgFile: " + argFile)
				interpolingProc = subprocess.Popen([python,playwave,audioDir + wavInterpolating])
				
				logFile.write("\n-----------------------------------------------------------------------------\n")
				logFile.write("Current Time:\t" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + "\n")
				with open(argFile) as file:
					multiType = file.readline().strip()
					print multiType
					logFile.write("Z Program Type: " + multiType + "\n")
					if multiType == "THREEPOINT":
						zArgs = file.readline() # int int int \r\n
						logFile.write("ZArgs:\t\t\t" + zArgs)
						yArgs = file.readline() # int int int \r\n
						logFile.write("YArgs:\t\t\t" + yArgs)
						yCenter = float(file.readline()) # int int int \r\n
						logFile.write("YCenter:\t\t" + str(yCenter) + "\n")
						targetFile = os.path.expanduser(file.readline()).strip() # string
						# Replace for my vm environment to work
						targetFile = targetFile.replace("Z:\\\\","\\\\vmware-host\\")
						targetFile = targetFile.replace("z:\\\\","\\\\vmware-host\\")
						print targetFile
						logFile.write("File:\t\t\t" + targetFile + "\n")
						compiledFile = None
						if not os.path.exists(targetFile):
							error="The gcodefile arg file given isn't found. I'm cleaning this up"
							handleError(error)
						else: 
							zArgList = zArgs.split()
							yArgList = yArgs.split()
							if len(yArgList) < 3 or float(yArgList[0]) == 0.00 or float(yArgList[1]) == 0.00 or float(yArgList[2]) == 0.00:
								error='ERROR: Either yArgs are nothing or there is a zero in the Yargs and should never be a zero'
								print error
								logFile.write(error + "\n")
								interpolingProc.kill()
							elif len(zArgList) < 3:
								error='ERROR: zargs are nothing or missing'
								print error
								logFile.write(error+ "\n")
								interpolingProc.kill()
							elif len(zArgList) == 3 and len(yArgList) == 3 and yCenter != 0:
								# Extract values from the temp file
								zZerosTmp=[]
								for i,zAbs in enumerate(zArgList):
									zZerosTmp.append(float(zAbs))

								zZeros = []
								zZeros.append((float(yArgList[0]),zZerosTmp[0]-zZerosTmp[1]))
								zZeros.append((yCenter,0))
								zZeros.append((float(yArgList[2]),zZerosTmp[2]-zZerosTmp[1]))
								logFile.write("zZeros:\t\t\t" + str(zZeros) + "\n")

								# Error:
								warnProc = None
								if zZeros[0][1] > ERROR_Z:
									warningMessage="ERROR: The TOP of the blank is " + str(ERROR_Z) + " inches higher than the middle! Do not continue. This is very bad."
									handleError(warningMessage)
								elif zZeros[-1][1] > ERROR_Z:
									warningMessage="ERROR: The BOTTTOM of the blank is " + str(ERROR_Z)+ " inches higher than the middle! Do not continue. This is very bad."
									handleError(warningMessage)
								# Warnings! handleErrors
								elif zZeros[0][1] > WARNING_Z:
									warningMessage="WARNING: The TOP of the blank is " + str(WARNING_Z) + " inches higher than the middle!"
									handleError(warningMessage)
								elif zZeros[-1][1] > WARNING_Z:
									warningMessage="WARNING: The BOTTOM of the blank is " + str(WARNING_Z) + " inches higher than the middle!"
									handleError(warningMessage)

								print "RUNNING"
								print "ZEROS" + str(zZeros)
								compiledFile = mainLogic(zZeros)
								subprocess.Popen([python,playwave,audioDir + wavSuccess])
							else:
								interpolingProc.kill()
								print "Cannot parse " + argFile

						# Write the done file with the name of the file we are delivering
						with open(argFile + ".done", 'a') as doneFile:
							if not compiledFile is None:
								doneFile.write(compiledFile  + "\n")
								doneFile.write(os.path.splitext(os.path.basename(compiledFile))[0])
						# Success message
						if not compiledFile is None:
							handleError("Successfully compiled gcode. The largest Z differential is " + str("{0:.3f}".format(max(zZeros[0][1], zZeros[-1][1], zZeros[0][1], zZeros[-1][1]))))

					elif multiType == "FRAGMENTED":
						fragments = []
						realZindex = None
						xJigOffset = None
						yJigOffset = None
						jigs = [] # Represents x and y offsets of a jig
						jigFragments = []
						fragmentsDir = file.readline().strip()
						compiledFile = None

						for line in file:
							print(line)
							logFile.write(line + '\n')
							line_clean = line.strip().split(' ')
							if line_clean[0] == "RealIndex":
								if realZindex is not None:
									handleError("FATAL ERROR FATAL ERROR: More than one Real Index presented.", True)
								realZindex = float(line_clean[1])
							elif line_clean[0].endswith(".gcode"):
								fragments.append((line_clean[0], float(line_clean[1])))
							elif line_clean[0] == "xJigOffset":
								# Once we hit xJigOffset again, we should save our .gcode offsets
								if len(jigs) > 0:
									jigFragments.append((len(jigs)-1,fragments))
									fragments=[]
								xJigOffset = float(line_clean[1])
							elif line_clean[0] == "yJigOffset":
								yJigOffset = float(line_clean[1])
								jigs.append((xJigOffset, yJigOffset))

						# Store the final fragments
						jigFragments.append((len(jigs)-1, fragments))


						########### Validation ################
						if DEBUG:
							print("FragmentsDir: " + fragmentsDir)
							print("Fragments: ")
							print(fragments)
						if any(0 in fragment for fragment in fragments) or realZindex is 0:
							handleError("FATAL ERROR FATAL ERROR: fragments or real z index is equal to ZERO! ", True)
						elif xJigOffset is None or yJigOffset is None:
							handleError("FATAL ERROR FATAL ERROR: Couldn't get jig offsets from arguments file!", True)
						elif len(jigs) != len(jigFragments):
							handleError("FATAL ERROR FATAL ERROR: Number of jigs doesn't match jig fragments", True)
							continue
						elif realZindex is None:
							handleError("FATAL ERROR FATAL ERROR: Couldn't get real z index from arguments file!", True)
						elif fragmentsDir is None:
							handleError("FATAL ERROR FATAL ERROR: Couldn't parse fragments dir from arguments file!", True)
						elif not os.path.isdir(fragmentsDir):
							handleError("FATAL ERROR FATAL ERROR: The given fragments dir doesn't exist: " + fragmentsDir, True)
						elif not fragments:
							handleError("FATAL ERROR FATAL ERROR: Couldn't parse fragments values from agruments file", True)
						else:
							compiledFile = combineFragments(realZindex, fragmentsDir, jigFragments, jigs)

						# Compare every value with the real index
						largestZdiff = 0.00
						largestZdiffFile = ""
						for fragments in jigFragments:
							for fragment in fragments[1]:
								zDiff = abs(realZindex - fragment[1])
								# Store the largest value
								if zDiff > largestZdiff:
									largestZdiff = zDiff
									largestZdiffFile = fragment[0]

						if largestZdiff > FATAL_Z:
							warningMessage="FATAL ERROR FATAL ERROR: fragment: "+ largestZdiffFile + " has a z differential larger than " + str(FATAL_Z) + " ! Do not continue. This is very bad."
							handleError(warningMessage, True)
						elif largestZdiff> ERROR_Z:
							warningMessage="ERROR ERROR: fragment: "+ largestZdiffFile + " has a z differential larger than " + str(ERROR_Z) + " !"
							handleError(warningMessage)
						elif largestZdiff > WARNING_Z:
							warningMessage="WARNING WARNING: fragment: "+ largestZdiffFile + " has a z differential larger than " + str(WARNING_Z) + " !"
							handleError(warningMessage)

						# Write the done file with the name of the file we are delivering
						with open(argFile + ".done", 'a') as doneFile:
							if not compiledFile is None:
								doneFile.write(compiledFile + "\n")
								# Base name
								doneFile.write(os.path.splitext(os.path.basename(compiledFile))[0])
								subprocess.Popen([python,playwave,audioDir + wavSuccess])

						# Success message
						if not compiledFile is None:
							handleError("Successfully compiled gcode. The largest Z differential is " + str("{0:.3f}".format(largestZdiff)))
					
					elif multiType == "DOUBLEJIG_SINGLE":
						# X and Y offsets for double jig
						doubleJigXoff = float(file.readline())
						doubleJigYoff = float(file.readline())

						realZindex = float(file.readline())
						realZindexLog = "Real Z Index:\t\t\t" + str(realZindex)
						print realZindexLog
						logFile.write(realZindexLog + '\n')
						secondZindex = float(file.readline())
						secondZindexLog = "Second Z Index:\t\t\t" + str(secondZindex)
						print secondZindexLog
						logFile.write(secondZindexLog + '\n')
						targetFile = os.path.expanduser(file.readline()).strip() # string
						# Replace for my vm environment to work
						targetFile = targetFile.replace("Z:\\\\","\\\\vmware-host\\")
						targetFile = targetFile.replace("z:\\\\","\\\\vmware-host\\")
						logFile.write("File:\t\t\t" + targetFile + "\n")

						compiledFile = doubleJigSimpleZ(doubleJigXoff, doubleJigYoff, realZindex, secondZindex, targetFile)

						with open(argFile + ".done", 'a') as doneFile:
							if not compiledFile is None:
								doneFile.write(compiledFile + "\n")
								# Base name
								doneFile.write(os.path.splitext(os.path.basename(compiledFile))[0])

						# Success message
						if not compiledFile is None:
							handleError("Successfully compiled gcode. The Z differential is " + str("{0:.3f}".format(realZindex - secondZindex)))
					else:	
						error = "ERROR: Unrecognized multi type: " + multiType
						print error
						# Write the done file with the name of the file we are delivering
						with open(argFile + ".done", 'a') as doneFile:
							if not compiledFile is None:
								doneFile.write(error + "\n")
								# Base name
								doneFile.write(os.path.splitext(os.path.basename(compiledFile))[0])
				# Remove the temp file
				interpolingProc.kill()
				logFile.flush()
				# os.remove(argFile)
				# Touch temp file to temp location so we don't modify the real one

		except OSError as e:
			print e
			open(argFile + ".done", 'a').close()

		time.sleep(1)
except KeyboardInterrupt:
	print('Exitting...')
	logFile.close()