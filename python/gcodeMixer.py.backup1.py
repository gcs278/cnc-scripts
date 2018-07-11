import tkinter as tk
# from tkinter import Tk, font
import sys
import os
import re
from tkinter import messagebox
import time
from functools import partial

rootdir = 'C:\\Users\\Shop\\Google Drive\\GS_Custom_Woodworking'
squareDir = rootdir + '\\Square_Signs\\'
circleDir = rootdir + '\\Circle_Signs\\'
slash = "\\"

tmpdir = 'C:\\tmp\\'
DEBUG=True
MAC=False
if sys.platform == "darwin":
    MAC=True

if MAC:
    rootdir = '/Users/grantspence/Google Drive/GS_Custom_Woodworking'
    tmpdir = '/tmp/gcode_tmp/'
    squareDir = rootdir + '/Square_Signs'
    circleDir = rootdir + '/Circle_Signs'
    slash = "/"

gcodeHeader=["T1","M1031","G17","G20","G90"]
gcodeFooter=["M1030","M02"]

gcodeRegexStr="([G|g][1|0]([X|x](\-?(\d*\.)?\d+))?([Y|y](\-?(\d*\.)?\d+))?)([Z|z](\-?(\d*\.)?\d+))?([F|f](\-?(\d*\.)?\d+))?"
#regexZ="([G|g][1|0][X|x]\-?\d*\.\d*[Y|y]\-?\d*\.\d*[Z|z])(\-?\d*\.\d*)"
gcodeRegex=re.compile(gcodeRegexStr)

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s.decode('utf-8')) ]

class MainApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_main()
        self.checkboxes=[]
        self.zValues=[]
        self.zLabels=[]

        # self.pack_propagate(0)
        # tk.geometry("500x500")

    def create_main(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.w = tk.Label(self, text="CNC GCode Compiler",font=("Helvetica", 36))
        self.w.pack()
        # self.c = tk.Checkbutton(self, text="Expand", variable=0)
        # self.c.pack()

        # list dirs in square dir
        for file in sorted(os.listdir(squareDir)):
            filename = os.fsdecode(file)
            fullPath = squareDir + slash + filename
            if os.path.isdir(fullPath):
                dirName=os.path.basename(filename)
                self.obx = tk.Button(master=self, text=filename, command= partial(self.selectDesign,fullPath,dirName))
                self.obx.pack(side="top")

        for file in sorted(os.listdir(circleDir)):
            filename = os.fsdecode(file)
            fullPath = circleDir + slash + filename
            if os.path.isdir(fullPath):
                dirName=os.path.basename(filename)
                self.obx = tk.Button(master=self, text=filename, command= partial(self.selectDesign,fullPath,dirName))
                self.obx.pack(side="top")

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        self.quit.pack(side="bottom")

    def create_cutscreen(self,gcodeDir, title):
        tk.Button(master=self, text='Back', command= lambda: self.create_main()).pack(side='top', anchor='w')

        self.w = tk.Label(self, text=title,font=("Helvetica", 36))
        self.w.pack()

        tk.Button(master=self, text='Select All', command= lambda: self.select_all()).pack(side='top', anchor='center')

        # Loop  through files in given dir and create check boxes
        directory = os.fsencode(gcodeDir)
        self.checkboxes=[]
        self.zValues=[]
        for file in sorted(os.listdir(directory), key=alphanum_key):
            filename = os.fsdecode(file)
            if filename.endswith(".gcode") and "_COMPILED_" not in filename and "000" not in filename:
                fm = tk.Frame(self)
                chkVar = tk.IntVar() 
                chkVar.set(0)
                zVar = tk.DoubleVar()
                zVar.set(' 0.000')
                self.zValues.append((zVar,filename))
                self.checkboxes.append((chkVar,filename))
                zLabel = tk.Label(fm,text=" 0.00",  textvariable=zVar,font=("Courier", 14))
                self.zLabels.append((zLabel,filename))
                zLabel.pack(side="left", fill="x")
                tk.Checkbutton(fm, text=filename, variable=chkVar).pack(side="left")

                tk.Button(fm, text="+0.01", bg="blue",command= partial(self.changeZindexValue,0.01,filename)).pack(side="right")
                tk.Button(fm, text="+0.005", bg="blue",command= partial(self.changeZindexValue,0.005,filename)).pack(side="right")
                tk.Button(fm, text="-0.005", bg="green",command= partial(self.changeZindexValue,-0.005,filename)).pack(side="right")
                tk.Button(fm, text="-0.01", bg="green",command= partial(self.changeZindexValue,-0.01,filename)).pack(side="right")
                fm.pack(fill="both",expand="yes",side="top")

        tk.Button(master=self, text='Generate GCode', command= lambda: self.generateGcode(gcodeDir, title)).pack(side='top', anchor='center')

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        self.quit.pack(side="bottom")

    def selectDesign(self, gcodeDir, title):
        if not os.path.exists(gcodeDir):
            messagebox.showerror("Dir not found", "The dir " + gcodeDir + " was not found on the system.")
            return

        for widget in self.winfo_children():
            widget.destroy()

        self.create_cutscreen(gcodeDir, title)

    def select_all(self): # Corrected
        for item in self.checkboxes:
            v , n = item
            if v.get():
                v.set(0)
            else:
                v.set(1)

    def changeZindexValue(self, valueChange, filename):
        for zValue in self.zValues:
           v , n = zValue
           if n == filename:
                oldValue=float(v.get())
                newValue=round(oldValue+float(valueChange),3)
                if newValue == 0:
                    v.set(' 0.000')
                else:
                    v.set(format(round(oldValue+float(valueChange),3), '+.3f'))
                for zLabel in self.zLabels:
                    j , k = zLabel
                    if k == filename:
                        if newValue > 0:
                            j.config(fg="green")
                        elif newValue < 0:
                            j.config(fg="red")
                        else:
                            j.config(fg="black")

    def cleanUpGcodeDir(self,gcodeDir):
        # Delete all COMPILED files in this folder
        directory = os.fsencode(gcodeDir)
        for file in sorted(os.listdir(directory), key=alphanum_key):
            fileName = os.fsdecode(file)
            if fileName.endswith(".gcode") and "_COMPILED_" in fileName:
                os.remove(gcodeDir + slash + fileName)

    def generateGcode(self, gcodeDir, title):
        # Create a temporary file that will merge all of these together
        timestr = time.strftime("%Y%m%d-%H%M%S")
        outFileDir=gcodeDir
        self.cleanUpGcodeDir(outFileDir)

        outFileName=outFileDir + slash + title + "_COMPILED_" + timestr + ".gcode"
        selected=False
        with open(outFileName,"a") as outFile:
            # Write our standard gcode header
            for gcode in gcodeHeader:
                outFile.write(gcode + '\n')

            # Combine all the files
            for item in self.checkboxes:
                v , n = item

                # If it is checked
                if v.get() == 1:
                    selected=True

                    # get the offset we want to apply
                    zFound=False
                    for zValuePair in self.zValues:
                        zValue , zFileName = zValuePair
                        if zFileName == n:
                            zOffset=float(zValue.get())
                            zFound=True

                    if not zFound:
                        messagebox.showerror("Error","Could not find zOffset for " + n)

                    with open(gcodeDir+slash+n) as sourceFile:
                        for line in sourceFile:
                            if line.rstrip() == "G91":
                                messagebox.showerror("Warning!","G91 is present in " + n + " I didn't write the app with that in mind.")
                            # Make sure these commands are NOT in our header and footer
                            if not any(line.rstrip() in s for s in gcodeHeader) and not any(line.rstrip() in s for s in gcodeFooter):
                                line_clean = line.strip()
                                match = gcodeRegex.match(line_clean)

                                # If we have a Z instruction
                                if match.group(9):
                                    z = float(match.group(9))
                                    newZ = round(z + zOffset,4)
                                    ####### F Section ############
                                    f = ""
                                    if match.group(11):
                                        f = str(match.group(11))

                                    # Build the new line (F comes after Z sometimes)
                                    newLine=str(match.group(1) + "Z" + str(newZ)) + f
                                    outFile.write(newLine + "\n")
                                else:
                                    # Else just copy the line
                                    outFile.write(line)

            # Write our standard gcode footer
            for gcode in gcodeFooter:
                outFile.write(gcode + '\n')


        if selected == False:
            messagebox.showerror("Error","No gcode files selected")
            return
        tk.Label(self, text="GCode Compiled!",font=("Helvetica", 18), fg="red").pack(side="top")
        tk.Label(self, text=outFileName.replace(rootdir, ""),font=("Helvetica", 10), fg="red").pack(side="top")



root = tk.Tk()
# root.pack_propagate(0)
# root.geometry("700x500")
app = MainApp(master=root)
root.update()
# now root.geometry() returns valid size/placement
root.minsize("500", "500")
app.mainloop()