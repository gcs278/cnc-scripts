# This file injects the Macros for text message alerts into all gcode
# As well as logging functions
import glob, sys
import os, time, fileinput
from verboseGcode import makeGcodeVerbose
from shutil import copyfile

#rootdir = 'C:\\Users\\Grant\\Google Drive\\GS_Custom_Woodworking'
rootdir = '/Users/grantspence/Google Drive'
#rootdir = '\\\\vmware-host\\Shared Folders\\grantspence On My Mac\\Google Drive\\GS_Custom_Woodworking'
#archiveDir = rootdir + '\\GCode_Archive'
archiveDir = rootdir + '/GCode_Archive'

fileExtention=".gcode" 

gcodeHeader=["T1","M1031","G17","G20","G90","G0S16000M3"]
gcodeFooter=["G0X0.0000Y0.0000", "M1030","M02"]

def desk_sign_compile(gcodeFile):
    fileBaseName=os.path.splitext(os.path.basename(gcodeFile))[0]
    workingFile=fileBaseName+"_WORKING-DESK.gcode"
    workingFilePath=tmpdir+workingFile

    # Todo: Make common
    regexStr="^(([G|g][1|0])([X|x](\-?(\d*\.)?\d+))?([Y|y](\-?(\d*\.)?\d+))?)([Z|z](\-?(\d*\.)?\d+))?([F|f](\-?(\d*\.)?\d+))?$"
    regex=re.compile(regexStr)

    # Touch temp file to temp location so we don't modify the real one
    with open(workingFilePath, 'a'):
        os.utime(workingFilePath, None)

    # The lowest Y value that the GCode cuts at.
    # We will use this to "center" the piece
    yMinGcodeCut = None
    yMaxGcodeCut = None
    saw_blade_kerf = 0.12
    blank_height = 9.5

    with open(gcodeFile) as file:
        for line in file:
            line_clean = line.strip()
            match = regex.match(line_clean)
            if match:
                y = float(match.group(7)) if match.group(7) else None
                z = float(match.group(10)) if match.group(10) else None

                # If z less than 0, then we are cutting
                if z < 0:
                    # Store a new lowest value
                    if y < yMinGcodeCut or yMinGcodeCut is None:
                        yMinGcodeCut = y
                    
                    # Store a new highest value
                    if y > yMaxGcodeCut or yMaxGcodeCut is None:
                        yMaxGcodeCut = y

    with open(workingFilePath,"a") as newfile:
        # TODO: Make this common 
        for gcode in gcodeHeader:
            newfile.write(gcode + '\n')

        # current_y_max = 
        # while
    

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
    #timestr = time.strftime("%I:%M %PM on %B %d")
    timestr = time.strftime("%I:%M %p on %B %d")
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
                #if not os.path.isfile(backupFile):
                    #print("Backing up " + file)
                    #copyfile(filePath,backupFile)

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
                    #print "Skipping making " + file + " verbose..."
                    #print "Making " + file + " verbose"
                    makeGcodeVerbose(filePath)
                    if os.path.basename(os.path.dirname(filePath)) == "Desk_Signs":
                        print("Running desk sign compilation")
                        # desk_sign_compile(filePath)

    print("Verified: " + str(fileCount) + " files")
