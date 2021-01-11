# TODO: Confirm working double jig with old transformation.
# TODO: Confirm VBS Script working
import glob, sys
import os, time, fileinput
import re, math
import shutil
import subprocess
import requests
from enum import Enum
# from tts_watson.TtsWatson import TtsWatson
from collections import namedtuple
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

# Axis Enum
Axis = Enum('Axis', 'x y z')
# Point Data Structure
Point = namedtuple('Point', 'x y z')
# Jig Data Structure
Jig = namedtuple('Jig', 'x_offset y_offset')
# Slope Data Structure for Multi Z
SlopeArea = namedtuple('SlopeArea', 'slope min max')

# Global Variables
rootdir = home + '\\Google Drive\\GS_Custom_Woodworking'

argFileDir="C:\\Mach3\\argFiles\\"
argFileGlob=argFileDir + "z-multi*.txt"
tmpdir = 'C:\\tmp\\'
tmpMultiCompiledDir = "multi_compiled"
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
# ttsWatson = TtsWatson('990e8a8e-0727-4d98-93a8-921a27d5202d', 'sdcoWYFtMXEA', 'en-US_MichaelVoice')

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
    print(message)
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
        # ttsWatson.play(message)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    except requests.exceptions.ConnectionError as e:
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__
        subprocess.Popen([python,playwave,audioDir + wavConnetionError])
        print("ERROR: Could not connect to the Watson API! No internet connection!")

# Convert an array of 2 points's Z Values to be relative to a center point
def convert_to_relative_z(points, anchor_point):
    relative_points = []
    for point in points:
        # Subtract the anchor point's Z Value
        new_z = point.z - anchor_point.z
        new_point = Point(point.x, point.y, new_z)
        relative_points.append(new_point)

    return relative_points

def fivepointMulti(x_points, y_points, center_points, jigs, srcGcodeFile):
    # Put the generated files in the same area, just put it in the 
    fileBaseName = os.path.splitext(os.path.basename(srcGcodeFile))[0]
    parentName = os.path.dirname(srcGcodeFile)
    tmpDirPath = parentName + slash + tmpMultiCompiledDir
    timestr = time.strftime("%Y%m%d-%H%M%S")
    if not os.path.isdir(tmpDirPath): os.mkdir(tmpDirPath)
    tmpFileName = tmpDirPath + slash + fileBaseName + "_COMPILEDMULTI_"+timestr+".gcode"

    # Clean up compile multi files, we won't need to use them again
    for compFragFilesOld in glob.glob(tmpDirPath + slash + "*_COMPILEDMULTI_*"):
        try:
            os.remove(compFragFilesOld)
        except OSError as e:
            print("ERROR: Can't remove " + compFragFilesOld)
            print(e)

    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    if os.path.exists(tmpFileName):
        os.remove(tmpFileName)

    # This is where our machine is really indexed at (always first Jig's zMid)
    realIndex = center_points[0].z

    # Write standard gcodeHeader
    with open(tmpFileName,"a") as newfile:
        for gcode in gcodeHeader:
            newfile.write(gcode + '\n')
            
        jigCount = 0
        for jig in jigs:
            xJigOffset = float(jig.x_offset)
            yJigOffset = float(jig.y_offset)
            # Sort to be consistent no matter the argument order
            x_points_jig = sorted(x_points[jigCount], key=lambda pt: pt.x)
            y_points_jig = sorted(y_points[jigCount], key=lambda pt: pt.y)

            center_point = center_points[jigCount]

            # Reconstruct incoming arrays to be relative to the centerpoints
            x_points_relative = convert_to_relative_z(x_points_jig, center_point)
            y_points_relative = convert_to_relative_z(y_points_jig, center_point)
            center_point_relative = Point(center_points[jigCount].x, center_points[jigCount].y, 0) 

            logFile.write("x_points_relative:\t\t\t" + str(x_points_relative) + "\n")
            logFile.write("y_points_relative:\t\t\t" + str(y_points_relative) + "\n")

            zJigOffset = center_point.z - realIndex

            if DEBUG: print("x_points_relative:\t" + str(x_points_relative))
            if DEBUG: print("y_points_relative:\t" + str(y_points_relative))

            # Determine the slopes for the points
            slopes_areas_x = generate_slopes(x_points_relative, center_point_relative, Axis.x)
            slopes_areas_y = generate_slopes(y_points_relative, center_point_relative, Axis.y)


            logFile.write("slopes_areas_x:\t\t\t" + str(slopes_areas_x) + "\n")
            logFile.write("slopes_areas_y:\t\t\t" + str(slopes_areas_y) + "\n")

            if DEBUG: print("slopes_areas_x:\t" + str(slopes_areas_x))
            if DEBUG: print("slopes_areas_y:\t" + str(slopes_areas_y))

            # Touch temp file to temp location so we don't modify the real one
            os.utime(tmpFileName, None)

            previousX = None
            previousY = None
            with open(srcGcodeFile) as file:
                for line in file:
                    line_clean = line.strip()
                    match = gcodeRegex.match(line_clean)
                    if match:
                        if DEBUG:
                            print("--------------------------------")
                            print("OLD GCODE: " + str(line_clean))

                        x = None
                        # Get X Value
                        if match.group(3):
                            x = float(match.group(3))

                        y = None
                        # Get Y Value
                        if match.group(6):
                            y = float(match.group(6))

                        if y is None and previousY is not None:
                            # We just have Z instruction and no X or Y, so use last Y
                            # In theory, verbose GCODE should never let this happen anymore (old code)
                            # But there could be the case where we don't verbose the gcode
                            if DEBUG: print("NO Y instruction, using previous offset")
                            y = previousY
                        elif y is None and previousY is None:
                            if DEBUG: print("NO Y instruction, NO last Y, not applying offset")
                        
                        # Set the previousY value
                        previousX = x
                        previousY = y

                        if DEBUG: print("X Value: " + bcolors.FAIL + str(x)+ bcolors.ENDC)
                        if DEBUG: print("Y Value: " + bcolors.FAIL + str(y)+ bcolors.ENDC)

                        # If we don't have a X and Y yet, then just don't calculate it
                        zOffset = 0 # Default
                        if y is not None and x is not None:
                            # Don't forget to add in zJigOffset
                            point = Point(x, y, z)
                            zOffset = findNewOffset(point, slopes_areas_x, slopes_areas_y, center_point_relative) + zJigOffset

                        # If Z is already positive, it means the that the machine is not cutting, but 
                        # just moving around. Don't mess with these values
                        if match.group(9):
                            z = float(match.group(9))
                            if z > 0.1:
                                zOffset = 0

                        newGcode = gcodeBuilder(match, xJigOffset, yJigOffset, zOffset)
                        
                        # Write the modified line to the file
                        if newGcode is not None:
                            newfile.write(newGcode + "\n")

                        if DEBUG:
                            # print "Z Value: " + str(z)
                            print("Z Offset TOTAL: " + str(round(zOffset,2)))
                            # print "New Z: " + str(newZ)
                            print("xJigOffset: " + str(xJigOffset))
                            print("yJigOffset: " + str(yJigOffset))
                            print("zJigOffset: " + str(zJigOffset))
                            print("NEW GCODE: " + str(newGcode))
                            # print "ZEROS: " + str(zZeros)
                            # print "SLOPES: " + str(slopes)
                            print("JIG: " + str(jigCount))

            jigCount+=1
            # handleError("JIG " + str(jigCount) + ": The largest Z differential is " + str("{0:.3f}".format(max(zZeros[0][1], zZeros[-1][1], zZeros[0][1], zZeros[-1][1]))))

        # Write our standard gcode footer on the COMBO file
        for gcode in gcodeFooter:
            newfile.write(gcode + '\n')     

    print("FINSIHED ZEROING")
    
    return tmpFileName

# This function generates the slope areas
# Slope areas consist of boundaries of where slopes apply
def generate_slopes(points, center_point, axis):
        
    slope_areas = []
    for point in points:
        # Determine what axis we want to generate slope areas for
        if axis == Axis.x:
            point_xy = point.x
            center_point_xy = center_point.x
        elif axis == Axis.y:
            point_xy = point.y
            center_point_xy = center_point.y

        # Calculate the slope of the points
        slope = findSlope(point_xy, point.z, center_point_xy, center_point.z)

        # Negate due to references shifting on center
        if (axis == Axis.x and point.x < center_point.x) or (axis == Axis.y and point.y < center_point.y):
            slope = -slope

        # Get mins/maxs for slope area boundaries
        print("Generate Slopes: " + str(point) + " " + str(center_point))
        point_min = min(point_xy,center_point_xy)
        point_max = max(point_xy,center_point_xy)
        slope_area = SlopeArea(slope, point_min, point_max)
        slope_areas.append(slope_area)

    return slope_areas

def findSlope(x1, y1, x2, y2):
    try:
        m = (y2-y1)/(x2-x1)
    except ZeroDivisionError:
        m = 0
    return m

# Finds the slope given a point, slope area, and an axis
def find_slope_in_areas(point, slope_areas, axis):
    if axis == Axis.x:
        point_xy = point.x
    elif axis == Axis.y:
        point_xy = point.y

    # Try to find if the point is in between any areas
    slope = None
    for slope_area in slope_areas:
        if slope_area.min <= point_xy <= slope_area.max: 
            slope = slope_area.slope
    
    # If it isn't in between two areas, then use min/max
    if slope is None:
        min_slope_area = min(slope_areas, key = lambda i: i.min)
        max_slope_area = max(slope_areas, key = lambda i: i.max)
        if point_xy < min_slope_area.min: slope = min_slope_area.slope
        if point_xy > max_slope_area.max: slope = max_slope_area.slope

    return slope

def findNewOffset(point, x_slope_areas, y_slope_areas, center_point):
    # Calculate the Z Offset produced by X Slope Areas
    x_slope = find_slope_in_areas(point, x_slope_areas, Axis.x)
    y_slope = find_slope_in_areas(point, y_slope_areas, Axis.y)

    # y = mx + b (aka z = m[x|y] + b)
    # Solving for 
    z_offset_for_x = x_slope * abs(point.x - center_point.x)
    z_offset_for_y = y_slope * abs(point.y - center_point.y)
    total_z_offset = z_offset_for_x + z_offset_for_y

    if DEBUG:
        print(f"Z Offset For X: {round(z_offset_for_x,2)}")
        print(f"Z Offset For Y: {round(z_offset_for_y,2)}")
    return total_z_offset

# Function that take our standard regex match and applies the provided offset
# to build a new gcode string
# Rejects headers and footers (assumed you do that elsewhere)
def gcodeBuilder(match, xJigOffset=0, yJigOffset=0, zOffset=0):
    # Make sure this isn't a header or footer
    if not match or any(match.group(0) in s for s in gcodeHeader) or any(match.group(0) in s for s in gcodeFooter):
        if DEBUG: print("Skipping Gcode: " + str(match.group(0)))
        return None

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
            print("ERROR: Can't remove " + fragTmpToDelete)
            print(e)

    os.mkdir(fragmentsDirTmp)
    combinedFragmentsFile=fragmentsDir + slash + parentName + "_COMPILEDFRAGMENTS_"+timestr+".gcode"

    # Clean up compiledfragments files, we won't need to use them again
    for compFragFilesOld in glob.glob(fragmentsDir + slash + "*_COMPILEDFRAGMENTS_*"):
        try:
            os.remove(compFragFilesOld)
        except OSError as e:
            print("ERROR: Can't remove " + compFragFilesOld)
            print(e)

    # Open the combo file that includes EVERYthing compiled
    with open(combinedFragmentsFile,"a") as outFile:
        # Write our standard gcode header
        for gcode in gcodeHeader:
            outFile.write(gcode + '\n')

        # For each of jigs, write a new balanced gcode
        jigCount = 0
        for jig in jigs:
            # For each jig, get all of the fragments
            for fragment in jigFragments[jigCount]:
                fileName = fragment[0]
                fragmentZ = float(fragment[1])
                xJigOffset = float(jig.x_offset)
                yJigOffset = float(jig.y_offset)
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

                            # if line_clean == "G91":
                                # messagebox.showerror("Warning!","G91 is present in " + n + " I didn't write the app with that in mind.")
                            match = gcodeRegex.match(line_clean)

                            # Get X and Y ONLY for knowing if they both 0 to not print
                            if match and match.group(6) and match.group(3):
                                y = float(match.group(6))
                                x = float(match.group(3))
                                if x == 0.00 and y == 0.00:
                                    continue

                            newGcode = gcodeBuilder(match, xJigOffset, yJigOffset, zOffset)
                            if newGcode is not None:
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
        print("Double Jig Simple Z")
        print("Z Offset" + str(zOffset))

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
                    print(multiType)
                    logFile.write("Z Program Type: " + multiType + "\n")
                    compiledFile = None

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
                        print(targetFile)
                        logFile.write("File:\t\t\t" + targetFile + "\n")
                        if not os.path.exists(targetFile):
                            error="The gcodefile arg file given isn't found. I'm cleaning this up"
                            handleError(error)
                        else: 
                            zArgList = zArgs.split()
                            yArgList = yArgs.split()
                            if len(yArgList) < 3 or float(yArgList[0]) == 0.00 or float(yArgList[1]) == 0.00 or float(yArgList[2]) == 0.00:
                                error='ERROR: Either yArgs are nothing or there is a zero in the Yargs and should never be a zero'
                                print(error)
                                logFile.write(error + "\n")
                                interpolingProc.kill()
                            elif len(zArgList) < 3:
                                error='ERROR: zargs are nothing or missing'
                                print(error)
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

                                print("RUNNING")
                                print("ZEROS" + str(zZeros))
                                compiledFile = threepointSingle(zZeros)
                                subprocess.Popen([python,playwave,audioDir + wavSuccess])
                            else:
                                interpolingProc.kill()
                                print("Cannot parse " + argFile)

                        # Write the done file with the name of the file we are delivering
                        with open(argFile + ".done", 'a') as doneFile:
                            if not compiledFile is None:
                                doneFile.write(compiledFile  + "\n")
                                doneFile.write(os.path.splitext(os.path.basename(compiledFile))[0])
                        # Success message
                        if not compiledFile is None:
                            handleError("Successfully compiled gcode. The largest Z differential is " + str("{0:.3f}".format(max(zZeros[0][1], zZeros[-1][1], zZeros[0][1], zZeros[-1][1]))))

                    elif multiType == "FRAGMENTED" or multiType == "FIVEPOINT_MULTI":
                        fragments = []
                        realZindex = None
                        xJigOffset = None
                        yJigOffset = None
                        jigs = [] # Represents x and y offsets of a jig
                        jigFragments = []
                        gcodePath = file.readline().strip()
                        compiledFile = None
                        isError = False
                        # FivePoint Multi Only
                        x_multi_points = [[]] # 2D Multi Points, multiple per jig
                        y_multi_points = [[]]
                        center_multi_points = [] # Center Points are 1D - Never two centers

                        for line in file:
                            print(line.rstrip())
                            logFile.write(line + '\n')
                            line_clean = line.strip().split(' ')
                            if line_clean[0] == "RealIndex":
                                if realZindex is not None:
                                    handleError("FATAL ERROR FATAL ERROR: More than one Real Index presented.", True)
                                    isError = True
                                realZindex = float(line_clean[1])
                            elif line_clean[0].endswith(".gcode"):
                                # Add Fragments for FRAGMENTED style
                                z = float(line_clean[1])
                                if z == 0.00:
                                    handleError("FATAL ERROR FATAL ERROR: A fragment measured with a value of 0!", True)
                                    isError = True
                                fragments.append((line_clean[0], z))
                            elif line_clean[0] == "YPOINT" or line_clean[0] == "XPOINT" or line_clean[0] == "CENTERPOINT":
                                # Get XYZ array (x,y,z) and turn it into a Point using argument unpacking
                                xyz = Point(*[float(i) for i in line_clean[1].split(',')])
                                
                                if xyz.z == 0.00:
                                    handleError("FATAL ERROR FATAL ERROR: A point measured with a Z value of 0!", True)
                                    isError = True
                                if xyz.x == 0.00 or xyz.y == 0.00:
                                    handleError("FATAL ERROR FATAL ERROR: A x or y multi point can't be zero!", True)
                                    isError = True

                                if line_clean[0] == "YPOINT":
                                    y_multi_points[len(jigs)-1].append(xyz)
                                elif line_clean[0] == "XPOINT":
                                    x_multi_points[len(jigs)-1].append(xyz)
                                elif line_clean[0] == "CENTERPOINT":
                                    center_multi_points.append(xyz)
                            elif line_clean[0] == "xJigOffset":
                                # Once we hit xJigOffset again, we should save our .gcode offsets
                                if len(jigs) > 0:
                                    jigFragments.append(fragments)
                                    fragments=[]
                                    x_multi_points.append([])
                                    y_multi_points.append([])

                                xJigOffset = float(line_clean[1])
                            elif line_clean[0] == "yJigOffset":
                                yJigOffset = float(line_clean[1])
                                jigs.append(Jig(xJigOffset, yJigOffset))

                        # Store the final fragments
                        jigFragments.append(fragments)

                        ########### Validation ################
                        if DEBUG:
                            print("gcodePath: " + gcodePath)
                            if multiType == "FRAGMENTED":
                                print("Fragments: ")
                                for jigFragment in jigFragments:
                                    print("Jig:\t\t\t" + str(jigFragment))
                            elif multiType == "FIVEPOINT_MULTI":
                                print("x_multi_points:\t\t" + str(x_multi_points))
                                print("y_multi_points:\t\t" + str(y_multi_points))
                                print("center_multi_points:\t" + str(center_multi_points))
                            
                        # Specific Errors
                        if multiType == "FRAGMENTED":
                            # Fragmented Only Errors
                            if any(0 in fragment for fragment in fragments):
                                handleError("FATAL ERROR FATAL ERROR: One of the fragment/point measurements is equal to ZERO! ", True)
                                isError = True
                            elif len(jigs) != len(jigFragments):
                                # Why?
                                handleError("FATAL ERROR FATAL ERROR: Number of jigs doesn't match jig fragments", True)
                                isError = True
                            elif not os.path.isdir(gcodePath):
                                handleError("FATAL ERROR FATAL ERROR: The given fragments dir doesn't exist: " + gcodePath, True)
                                isError = True
                            elif realZindex is None:
                                handleError("FATAL ERROR FATAL ERROR: Couldn't get real z index from arguments file!", True)
                                isError = True
                            elif realZindex is 0:
                                handleError("FATAL ERROR FATAL ERROR: real z index is equal to ZERO! ", True)
                                isError = True
                            elif not fragments:
                                handleError("FATAL ERROR FATAL ERROR: Couldn't parse fragments values from agruments file", True)
                                isError = True
                        elif multiType == "FIVEPOINT_MULTI":
                            if not os.path.isfile(gcodePath):
                                handleError("FATAL ERROR FATAL ERROR: The given gcode file path doesn't exist: " + gcodePath, True)
                                isError = True
                            elif len(center_multi_points) != len(jigs):
                                handleError("FATAL ERROR FATAL ERROR: Missing y center for threepoint multi program", True)
                                isError = True

                        # Common Errors
                        if xJigOffset is None or yJigOffset is None:
                            handleError("FATAL ERROR FATAL ERROR: Couldn't get jig offsets from arguments file!", True)
                            isError = True
                        elif gcodePath is None:
                            handleError("FATAL ERROR FATAL ERROR: Couldn't parse fragments dir from arguments file!", True)
                            isError = True
                        
                        # If no errors, attempt to compile the gcode
                        if not isError:
                            if multiType == "FRAGMENTED":
                                compiledFile = combineFragments(realZindex, gcodePath, jigFragments, jigs)
                                                                # Compare every value with the real index
                                largestZdiff = 0.00
                                largestZdiffFile = ""
                                for fragments in jigFragments:
                                    for fragment in fragments:
                                        zDiff = abs(realZindex - fragment[1])
                                        # Store the largest value
                                        if zDiff > largestZdiff:
                                            largestZdiff = zDiff
                                            largestZdiffFile = fragment[0]

                                if largestZdiff > FATAL_Z:
                                    warningMessage="FATAL ERROR FATAL ERROR: fragment: "+ largestZdiffFile + " has a z differential larger than " + str(FATAL_Z) + " ! Do not continue. This is very bad."
                                    handleError(warningMessage, True)
                                elif largestZdiff > ERROR_Z:
                                    warningMessage="ERROR ERROR: fragment: "+ largestZdiffFile + " has a z differential larger than " + str(ERROR_Z) + " !"
                                    handleError(warningMessage)
                                elif largestZdiff > WARNING_Z:
                                    warningMessage="WARNING WARNING: fragment: "+ largestZdiffFile + " has a z differential larger than " + str(WARNING_Z) + " !"
                                    handleError(warningMessage)

                                # Success message
                                if not compiledFile is None:
                                    handleError("Successfully compiled gcode. The largest Z differential is " + str("{0:.3f}".format(largestZdiff)))

                            elif multiType == "FIVEPOINT_MULTI":
                                compiledFile = fivepointMulti(x_multi_points, y_multi_points, center_multi_points, jigs, gcodePath)

                                # Success message
                                if not compiledFile is None:
                                    handleError("Successfully compiled multi point gcode.")

                        # Write the done file with the name of the file we are delivering
                        with open(argFile + ".done", 'a') as doneFile:
                            if not compiledFile is None:
                                doneFile.write(compiledFile + "\n")
                                # Base name
                                doneFile.write(os.path.splitext(os.path.basename(compiledFile))[0])
                                subprocess.Popen([python,playwave,audioDir + wavSuccess])
                    
                    elif multiType == "DOUBLEJIG_SINGLE":
                        # X and Y offsets for double jig
                        doubleJigXoff = float(file.readline())
                        doubleJigYoff = float(file.readline())

                        realZindex = float(file.readline())
                        realZindexLog = "Real Z Index:\t\t\t" + str(realZindex)
                        print(realZindexLog)
                        logFile.write(realZindexLog + '\n')
                        secondZindex = float(file.readline())
                        secondZindexLog = "Second Z Index:\t\t\t" + str(secondZindex)
                        print(secondZindexLog)
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
                        print(error)
                        # Write the done file with the name of the file we are delivering
                        with open(argFile + ".done", 'a') as doneFile:
                            doneFile.write(error + "\n")

                            if compiledFile:
                                # Base name
                                doneFile.write(os.path.splitext(os.path.basename(compiledFile))[0])
                # Remove the temp file
                interpolingProc.kill()
                logFile.flush()
                # os.remove(argFile)
                # Touch temp file to temp location so we don't modify the real one

        except OSError as e:
            print(e)
            open(argFile + ".done", 'a').close()

        time.sleep(1)
except KeyboardInterrupt:
    print('Exitting...')
    logFile.close()