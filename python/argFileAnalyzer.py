#!/usr/bin/env python3
import sys,os,glob
import ntpath
import collections
from decimal import Decimal
import time

# The amount of variance we can accept between Z's
OFFSET=0.005 

if len(sys.argv) < 2:
    print("ERROR: Pass a directory of arg files")
    exit(1)

argDir=sys.argv[1]
if not os.path.isdir(argDir):
    print("ERROR: %s is not a directory" % argDir)
    exit(1)

GcodeObject = collections.namedtuple('GcodeStats','name executions offenders')
gcodeStats = []

results_path = "C:\\Users\\Shop\\Google Drive\\GS_Custom_Woodworking\\argFileAnalyzer"

MAC=False
slash = "\\"
if sys.platform == "darwin":
    MAC=True
    results_path = "/tmp/argFileAnalyzer"
    slash = "/"
    
timestr = time.strftime("%Y%m%d-%H%M%S")
if not os.path.isdir(results_path): os.mkdir(results_path)
tmpFileName = results_path + slash + "argFileAnalyzer_"+timestr+".txt"


# Touch temp file to temp location so we don't modify the real one
with open(tmpFileName, 'a') as results_file:
    os.utime(tmpFileName, None)
    results_file.write("Date:\t\t\t%s" % timestr + "\n")
    results_file.write("Parameter Offset:\t%s" % OFFSET + "\n\n")

    count=0
    for file in list(glob.glob(argDir + "/*.txt")):
        with open(file) as f:
            zType = f.readline()
            if 'FRAGMENTED' in zType:
                fileName = ntpath.basename(f.readline()).strip()

                # Read next three lines
                f.readline() # Realindex
                f.readline() # xJigOffset
                f.readline() # yJigOffset

                zIndexs = []
                jig_number = 0
                zIndexs.append([])
                # Build indexs
                for line in f:
                    if 'xJigOffset' in line:
                        jig_number=+1
                        zIndexs.append([])
                    elif not 'yJigOffset' in line:
                        zIndexs[jig_number].append(line.split())

                # Search for offenders, ONLY FOR THIS JOB
                offenders=[] 
                for jig in zIndexs:
                    count += 1
                    # if fileName != "OBX_Standard-Legends":
                    #     continue
                    foundGcodeStatIndex = [i for i, gcodeStat in enumerate(gcodeStats) if gcodeStat.name == fileName]
                    foundGcodeStat = False
                    if foundGcodeStatIndex:
                        foundGcodeStatIndex = foundGcodeStatIndex[0]
                        foundGcodeStat = True
                        
                    for zIndex in jig:
                        print(f"Source: {zIndex}")
                        for zIndexSearch in jig:
                            # If not the same file
                            if zIndex[0] != zIndexSearch[0]:
                                print(f"     Testing: {zIndexSearch}")
                                diff = abs(float(zIndex[1]) - float(zIndexSearch[1]))
                                if diff < OFFSET:
                                    print("OFFENDER! %s %s" % (zIndex[0],zIndexSearch[0]))
                                    nameList = sorted([zIndex[0],zIndexSearch[0]])
                                    found = [offender for offender in offenders if offender[0] == nameList[0] and offender[1] == nameList[1]]
                                    # If we have already found it, that probably means it the reverse of what we found,
                                    # Don't add it in
                                    if not found:
                                        # (First GCode, Second GCode, Offend Count)
                                        print("Adding Offender")
                                        offenders.append((nameList[0], nameList[1], 1))

                    # If we have the stats for this gcode, then we have to merge
                    if foundGcodeStat:
                        # Update the number of executions in the object
                        numOfExecutions = gcodeStats[foundGcodeStatIndex].executions + 1
                        gcodeStats[foundGcodeStatIndex] = gcodeStats[foundGcodeStatIndex]._replace(executions=numOfExecutions)

                        oldOffenders = gcodeStats[foundGcodeStatIndex].offenders
                        # Merge offender arrays (take new offenders and combine with previous offenders)
                        for offender in offenders:
                            foundOffenderIndex = [i for i, oldOffender in enumerate(oldOffenders) if oldOffender[0] == offender[0] and oldOffender[1] == offender[1]]
                            if foundOffenderIndex:
                                # Increment offender
                                foundOffender = oldOffenders[foundOffenderIndex[0]]
                                newOffender = (foundOffender[0],foundOffender[1],foundOffender[2] + 1)

                                # Replace the old offender with the new
                                oldOffenders[foundOffenderIndex[0]] = newOffender
                            else:
                                # Else we have a new offender
                                oldOffenders.append(offender)
                        gcodeStats[foundGcodeStatIndex] = gcodeStats[foundGcodeStatIndex]._replace(offenders=oldOffenders)
                    else:
                        # We don't have stats, so just create the entry
                        gcodeStat = GcodeObject(name=fileName, executions=1, offenders=offenders)
                        gcodeStats.append(gcodeStat)

    # Print out results
    for gcodeStat in gcodeStats:
            results_file.write("GCode: %s Executions: %s " % (gcodeStat.name, str(gcodeStat.executions)) + "\n")
            offenders = sorted(gcodeStat.offenders, key=lambda x: x[2], reverse=True)
            for offender in offenders:
                # offender[2] == gcodeStat.executions says EVERYTIME we ran, this was an offender
                if offender[2] > 1: # and offender[2] == gcodeStat.executions:
                    percent_accurate = round(( offender[2] / gcodeStat.executions ) * 100)
                    results_file.write(f"   Offenders: {offender[0]} and {offender[1]}\n")
                    results_file.write(f"       Frequency: {offender[2]}\n")
                    results_file.write(f"       Percent Accurate: {percent_accurate}\n")

    results_file.write("Total Execution Count %s" % count + "\n")

print("Total Execution Count %s" % count)
print("Results were written to %s" % tmpFileName)
if count == 0:
    print("ERROR: Dir %s has no .done arg files" % argDir)
    exit(1)