import glob, sys
import os, time, fileinput
from os.path import expanduser
import re
from shutil import copyfile

home = expanduser("~")
# Home on Virtual Machine
if os.path.exists("Z:\\grantspence On My Mac"):
    home = "Z:\\grantspence On My Mac"

# Global Variables
rootdir = home + '\\Google Drive\\GS_Custom_Woodworking'
vb_file_glob = rootdir + '\\cnc-scripts\\vbscript\\' + "*.vbs"

mach3_macro_dirs = "C:\\Mach3\\macros\\"

DEBUG=False
MAC=False
if sys.platform == "darwin":
    MAC=True

# Mac specific logic
if MAC:
    rootdir = '/Users/grantspence/Google Drive/GS_Custom_Woodworking'
    tmpdir = '/tmp/gcode_tmp/'
    DEBUG=True
    vb_file_glob = rootdir + '/cnc-scripts/vbscript/' + "*.vbs"


regexStr="(.*)_(M\d+)\.vbs?"
vbscript_regex = re.compile(regexStr)

if not os.path.isdir(mach3_macro_dirs):
    print("ERROR: " + str(mach3_macro_dirs) + " is not found. Is mach3 installed here?")
    sys.exit(1)

for vbfile in glob.glob(vb_file_glob):
    match = vbscript_regex.match(vbfile.strip())
    if match and match.group(2):
        # print(vbfile)
        # print(match.group(2))
        print(os.listdir(mach3_macro_dirs))
        for dir in os.listdir(mach3_macro_dirs):
            fulldir = mach3_macro_dirs + "\\" + dir
            if os.path.isdir(fulldir):
                dest = "\\" + match.group(2)
                target = fulldir + "\\" + dest + ".m1s"
                print("Copying " + str(vbfile) + " to " + str(target ))
                # os.remove(target)
                copyfile(vbfile, target)

