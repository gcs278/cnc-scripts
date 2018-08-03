
items = ("Start Depth","Change bits to 90 Degrees", "Change bits to 60 Degrees", "Save all toolpaths")
task = select("Select what task you want to perform", options = items)


if task == items[0]:
    sDepth = input("Input a start depth:")

# Function to click each toolpath and modify it
def modifyToolpaths(top):
    if not exists(Pattern("1531967477473.png").similar(0.97).targetOffset(23,-1)):
        return
    for x in findAll(Pattern("1531967477473.png").similar(0.97).targetOffset(23,-1)):
        doubleClick(x)
        if task == items[0]:
            click(Pattern("1531966919660.png").targetOffset(75,-2))
            type("a",KEY_CTRL)
            type(sDepth)
        elif task == items[1]:
            click(Pattern("1532050408082.png").targetOffset(99,17))
            click("1532050450743.png")
            click("1532050564687.png")
        elif task == items[2]:
            click(Pattern("1532050408082.png").targetOffset(99,17))
            click("1532050609212.png")
            click("1532050564687.png")
        click("1531967356502.png")
        if(exists("1532044569814.png")):
            click(Pattern("1532044581737.png").similar(0.71))
        if top:
            click(Pattern("1532048577277.png").targetOffset(17,39))
        else:
            click(Pattern("1532048853154.png").targetOffset(6,-32))
        hover(x)
        mouseMove(-33,-3)
        mouseDown(Button.LEFT)
        mouseUp(Button.LEFT)

if(exists("1531967086580.png")):
        click("1531967095102.png")
        
if(exists("1532044569814.png")):
    click(Pattern("1532044581737.png").similar(0.71))

if(exists("1532139576641.png")):
    click("1532139584617.png")

# Go to the top
click(Pattern("1532048577277.png").targetOffset(17,39))

if task != items[3]: 
    modifyToolpaths(True)

    # Go to the bottom
    click(Pattern("1532048853154.png").targetOffset(6,-32))

    modifyToolpaths(False)
elif task == items[3]:
    click("1532051295960.png")
    hover(Pattern("1532048577277.png").targetOffset(17,39))
    mouseDown(Button.LEFT)
    sleep(2)
    mouseUp(Button.LEFT)

    if exists(Pattern("1532051379042.png").exact()):
        click(Pattern("1532051388422.png").targetOffset(-93,-2))
    first=True
    loop=True
    while(loop):
        if exists(Pattern("1531967477473.png").similar(0.97).targetOffset(23,-1)):
            for x in findAll(Pattern("1531967477473.png").similar(0.97).targetOffset(23,-1)):
                click(x)
                click("1532139888228.png")
                if first:
                   popup("Please select the folder you'd like these to save to...then click ok")
                   first=False  
                click("1532565073660.png")
                if exists("1532565230934.png"):
                        click("1532565250002.png")
                # Uncheck the check box
                hover(x)
                mouseMove(-33,-3)
                mouseDown(Button.LEFT)
                mouseUp(Button.LEFT)
        if exists(Pattern("1532568951939.png").exact()):
            loop=False 
            break
        
        # Click 7 times and look for more
        click(Pattern("1532564767758.png").targetOffset(5,-25))
        click(Pattern("1532564767758.png").targetOffset(5,-25))
        click(Pattern("1532564767758.png").targetOffset(5,-25))
        click(Pattern("1532564767758.png").targetOffset(5,-25))
        click(Pattern("1532564767758.png").targetOffset(5,-25))
        click(Pattern("1532564767758.png").targetOffset(5,-25))
            
            
    
    
