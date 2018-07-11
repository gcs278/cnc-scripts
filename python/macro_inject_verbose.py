# This file injects the Macros for text message alerts into all gcode
# As well as logging functions
import glob, sys
import os, time, fileinput
from verboseGcode import makeGcodeVerbose
from shutil import copyfile

rootdir = '/Users/grantspence/Google Drive/GS_Custom_Woodworking'
#rootdir = '\\\\vmware-host\\Shared Folders\\grantspence On My Mac\\Google Drive\\GS_Custom_Woodworking'
#archiveDir = rootdir + '\\GCode_Archive'
archiveDir = rootdir + '/GCode_Archive'

fileExtention=".gcode" 

if len(sys.argv) == 2 and sys.argv[1] == '--revert':
	print("Reverting changes...")
	fileCount=0
	for subdir, dirs, files in os.walk(rootdir):
		for file in files:
			if file.endswith(fileExtention):
				fileCount+=1
				# print(os.path.join(subdir, file)
				filePath = os.path.join(subdir, file)
				f = open(filePath,"r+")
				d = f.readlines()
				f.seek(0)
				for i in d:
					# Remove lines with our macros
					if "M1030" not in i and "M1031" not in i:
						f.write(i)
				f.truncate()
				f.close()

	print("Reverted " + str(fileCount) +  " files")
else:
	timestr = time.strftime("%I:%M %PM on %B %d")
	print("Running configuration...it's "+timestr)
	fileCount=0
	for subdir, dirs, files in os.walk(rootdir):
		for file in files:
			if file.endswith(fileExtention):
				fileCount+=1
				# print(os.path.join(subdir, file)
				filePath = os.path.join(subdir, file)
				
				# If the file has a space in the name, rename it
				if ' ' in file:
					newFileName=file.replace(' ','_')
					newFilePath = os.path.join(subdir, newFileName)
					print "Renaming " + file + " to " + newFileName
					os.rename(filePath, newFilePath)
					filePath=newFilePath
					file = newFileName

				backupFile = archiveDir + "/" + file + ".bak"
				timestr = time.strftime("%Y-%m")
				if not os.path.isfile(backupFile):
					print("Backing up " + file)
					copyfile(filePath,backupFile)

				# Count number of lines
				with open(filePath,"r") as f:
					num_lines=0
					for i, l in enumerate(f):
						num_lines += 1
				line_number=num_lines

				gcodeAlreadyConfigured=True
				with open(filePath, "r") as f:
					line_count=1
					for line in f:
						if line_count == 1 and line.strip() != "T1" :
							print("ERROR: First line in " + filePath + " is not T1")
							break
						elif line_count == 2 and line.strip() != "M1031":
							print("Configuring M1031 Macro in beginning on " + file)
							# Open again since we have the pointer moved up
							with open(filePath, "r") as fCopy:
								contents = fCopy.readlines()
								contents.insert(1, 'M1031\n')
							# Open with writing
							with open(filePath, "w") as fw:
								contents = "".join(contents)
								fw.write(contents)
							line_count+=1 # Cause we just added a line, we aren't iterating over it
							line_number+=1 # Cause we just added a line
							gcodeAlreadyConfigured=False
						elif line_count == (line_number-1) and line.strip() != 'M1030':
							# Count number of lines
							print("Configuring M1030 Macro at end on " + file)
							# Open again since we have the pointer moved up
							with open(filePath, "r") as fCopy:
								contents = fCopy.readlines()
								contents.insert(line_number-1, 'M1030\n')
							# Open with writing
							with open(filePath, "w") as fw:
								contents = "".join(contents)
								fw.write(contents)
							gcodeAlreadyConfigured=False
							break
						line_count += 1
				if not gcodeAlreadyConfigured:
					print "Making " + file + " verbose"
					makeGcodeVerbose(filePath)

	print("Verified: " + str(fileCount) + " files")
