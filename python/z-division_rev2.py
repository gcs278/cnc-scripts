import glob, sys
import os, time, fileinput
import re, math
import shutil
import subprocess

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
rootdir = 'C:\\Users\\Shop\\Google Drive\\GS_Custom_Woodworking'
argFileDir="C:\\Mach3\\argFiles\\"
argFileGlob=argFileDir + "python_data*.txt"
tmpdir = 'C:\\tmp\\'
audioDir = rootdir + "\\CNC_Data\\audio_clips\\"
playwave = rootdir + "\\CNC_Data\\playwave.py"
python = "C:\\Python27\\python.exe"
DEBUG=False
MAC=False
if sys.platform == "darwin":
	MAC=True
	DEBUG=True

targetFile=""
wavElevatedTop02="elevated-02-top.wav"
wavElevatedBottom02="elevated-02-bottom.wav"
wavElevatedTop05="elevated-05-top.wav"
wavElevatedBottom05="elevated-05-bottom.wav"
wavInterpolating="interpolating.wav"
wavSuccess="success.wav"

if MAC:
	rootdir = '/Users/grantspence/Google Drive/GS_Custom_Woodworking'
	tmpdir = '/tmp/gcode_tmp/'
	targetFile=rootdir+"/Square_Signs/She_is_clothed_copy.gcode"
	argFileDir="/tmp/"
	argFileGlob=argFileDir + "python_data*.txt"
	audioDir = rootdir + "/CNC_Data/audio_clips/"
	playwave = rootdir + "/CNC_Data/playwave.py"
	python = "python"

def mainLogic(zZeros, logFile):
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


	regexStr="([G|g][1|0]([X|x](\-?(\d*\.)?\d+))?([Y|y](\-?(\d*\.)?\d+))?)([Z|z](\-?(\d*\.)?\d+))?([F|f](\-?(\d*\.)?\d+))?"
	#regexZ="([G|g][1|0][X|x]\-?\d*\.\d*[Y|y]\-?\d*\.\d*[Z|z])(\-?\d*\.\d*)"
	regex=re.compile(regexStr)

	coordList=[]
	slopes=[]

	# Just example data to get started
	# zZeros=[]
	# zZeros.append((9,-0.015))
	# zZeros.append((5.5,0))
	# zZeros.append((2,-0.03))

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
	previousZ = 0
	firstZFound = False
	with open(targetFile) as file:
		for line in file:
			line_clean = line.strip()
			match = regex.match(line_clean)
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
					previousZ = z 
					firstZFound = True
				else:
					if DEBUG and firstZFound:
						print "NO Z instruction, using previousZ"
					if DEBUG and not firstZFound:
						print "NO Z instruction, and no first Z found"

					# If we have a previous Z to use, use it
					if firstZFound:
						z = previousZ
					else:
						with open(tmpTmpFileName,"a") as file:
							file.write(line_clean + "\n")
						continue
				zOffset=findNewOffset(y,slopes, zZeros)
				newZ=round(z+zOffset,4)
				newLine=str(match.group(1) + "Z" + str(newZ)) + f
				
				# Write the modified line to the file
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

#argFile="/Users/grantspence/test"
if MAC:
	log_dir=rootdir+"/logs"
else:
	log_dir=rootdir+"\\logs"

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

if MAC:
	logFilePath = log_dir + "/z-division-logs-MACDEBUG.log"	
else:
	logFilePath = log_dir + "\\z-division-logs.log"	

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
				interpolingProc = subprocess.Popen([python,playwave,audioDir + wavInterpolating])
				
				with open(logFilePath, 'a') as logFile:
					logFile.write("\n-----------------------------------------------------------------------------\n")
					logFile.write("Current Time:\t" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + "\n")
					with open(argFile) as file:
						print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
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
						logFile.write("File:\t\t\t" + targetFile + "\n")
						print targetFile
						if not os.path.exists(targetFile):
							error="The gcodefile arg file given isn't found. I'm cleaning this up"
							print error
							logFile.write(error)
						else: 
							zArgList = zArgs.split()
							yArgList = yArgs.split()
							if len(zArgList) == 3 and len(yArgList) == 3 and yCenter != 0:
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
								if zZeros[0][1] > 0.05:
									interpolingProc.kill()
									print "ERROR: The TOP of the blank is 0.06 inches higher than the middle!"
									warnProc = subprocess.Popen([python,playwave,audioDir + wavElevatedTop05])
								elif zZeros[-1][1] > 0.05:
									interpolingProc.kill()
									print "ERROR: The BOTTTOM of the blank is 0.06 inches higher than the middle!"
									warnProc = subprocess.Popen([python,playwave,audioDir + wavElevatedBottom05])
								# Warnings! Speaks
								elif zZeros[0][1] > 0.02:
									interpolingProc.kill()
									print "WARNING: The TOP of the blank is 0.02 inches higher than the middle!"
									warnProc = subprocess.Popen([python,playwave,audioDir + wavElevatedTop02])
								elif zZeros[-1][1] > 0.02:
									interpolingProc.kill()
									print "WARNING: The BOTTOM of the blank is 0.02 inches higher than the middle!"
									warnProc = subprocess.Popen([python,playwave,audioDir + wavElevatedBottom02])

								print "RUNNING"
								print "ZEROS" + str(zZeros)
								mainLogic(zZeros, logFile)
								if warnProc != None and warnProc.poll() != None:
									subprocess.Popen([python,playwave,audioDir + wavSuccess])
							else:
								interpolingProc.kill()
								print "Cannot parse " + argFile
					# Remove the temp file
					interpolingProc.kill()
					# os.remove(argFile)
					# Touch temp file to temp location so we don't modify the real one
					open(argFile + ".done", 'a').close()
					

		except OSError as e:
			print e
			open(argFile + ".done", 'a').close()
		time.sleep(1)
except KeyboardInterrupt:
    print('Exitting...')