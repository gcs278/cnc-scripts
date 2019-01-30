#!/usr/bin/env python
import sys,os,glob
import ntpath
import collections
from decimal import Decimal

# The amount of variance we can accept between Z's
OFFSET=0.002

if len(sys.argv) < 2:
	print("ERROR: Pass a directory of arg files")
	exit(1)

argDir=sys.argv[1]
if not os.path.isdir(argDir):
	print("ERROR: %s is not a directory" % argDir)
	exit(1)

GcodeObject = collections.namedtuple('GcodeStats','name executions offenders')
gcodeStats = []

count=0
for file in list(glob.glob(argDir + "/*.txt")):
	with open(file) as f:
		zType = f.readline()
		if 'FRAGMENTED' in zType:
			count+=1
			fileName = ntpath.basename(f.readline()).strip()
			foundGcodeStatIndex = [i for i, gcodeStat in enumerate(gcodeStats) if gcodeStat.name == fileName]
			foundGcodeStat = False
			if foundGcodeStatIndex:
				foundGcodeStatIndex = foundGcodeStatIndex[0]
				foundGcodeStat = True

			# Read next three lines
			f.readline() # Realindex
			f.readline() # xJigOffset
			f.readline() # yJigOffset

			zIndexs = []
			secondJig = False
			zIndexsSecond = []
			# Build indexs
			for line in f:
				zIndexs.append(line.split())
				if 'yJigOffset' in line:
					break
			if secondJig:
				f.readline()
				for line in f:
					zIndexsSecond.append(line.split())

			# Search for offenders, ONLY FOR THIS JOB
			offenders=[] 
			for zIndex in zIndexs:
				for zIndexSearch in zIndexs:
					diff = abs(float(zIndex[1]) - float(zIndexSearch[1]))
					if diff < OFFSET and zIndex[0] != zIndexSearch[0]:
						# print("OFFENDER! %s %s" % (zIndex[0],zIndexSearch[0]))
						nameList = sorted([zIndex[0],zIndexSearch[0]])
						found = [offender for offender in offenders if offender[0] == nameList[0] and offender[1] == nameList[1]]
						if not found:
							# (First GCode, Second GCode, Offend Count)
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
		print("GCode: %s Executions: %s " % (gcodeStat.name, str(gcodeStat.executions)) )
		offenders = sorted(gcodeStat.offenders, key=lambda x: x[2], reverse=True)
		for offender in offenders:
			# offender[2] == gcodeStat.executions says EVERYTIME we ran, this was an offender
			if offender[2] > 1 and offender[2] == gcodeStat.executions:
				print("   Offenders: %s and %s Frequency: %d" % (offender[0],offender[1],offender[2]))

print("Total Execution Count %s" % count)
if count == 0:
	print("ERROR: Dir %s has no .done arg files" % argDir)
	exit(1)