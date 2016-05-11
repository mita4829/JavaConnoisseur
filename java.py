"""Copyright (c) 2016 Michael Tang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
    
"""

import sys

NORMAL = "\x1B[0m"
RED = "\x1B[31m"
MAGENTA = "\x1B[35m"
YELLOW = "\x1B[33m"
GREEN = "\x1B[32m"
CYAN = "\x1B[36m"

#Parse function to extract JS file as a string
def parse():
    try:
        argv = sys.argv[1]
        with open(argv,"r") as ins:
            master = ""
            for line in ins:
                master = master + line
    except:
        print(YELLOW+"No JS file given"+NORMAL)
        sys.exit()
    return master

#Function takes in the whole JS file as one string. It returns the string back without and comments in the form of // and /* */
def noComment(string):
    singleLine = 0
    multiLine = 0
    multiLineEnd = 0
    while((string.find("//",singleLine)) != -1):
        low = string.find("//",singleLine)
        high = string.find("\n",low)
        string = spacer(string,low,high)
        singleLine = high
    
    while((string.find("/*",multiLine)) != -1):
        multiLine = string.find("/*",multiLine)
        multiLineEnd = string.find("*/",multiLine)
        string = spacer(string,multiLine,multiLineEnd+2)
        multiLine = multiLineEnd

    return string

#Helper function for noComment(string), takes the string, low, and high, indexes and removes string[low:high]
def spacer(string,low,high):
    lowerhalf = string[:low]
    upperHalf = string[high:]
    string = lowerhalf+upperHalf
    return string

#Detect use of semi-colons at the end of statements
def semiColon(string):
    semi = 0
    clear = 1
    statement = CYAN+"Semi-Colon check: "+NORMAL
    print(statement,end='')
    #check the char behind \n and see if it's a semi-colon. Exception when char behind \n is { }
    while((string.find("\n",semi)) != -1):
        i = string.find("\n",semi)
        if((string[i-1] != ';') and (string[i-1] != '{' and string[i-1] != '}') and (string[i-1] != '\n') and i != 0 and (string[i-1] != ' ')):
            if(clear):
                print(RED + "Failed"+NORMAL)
                clear = 0
                print(YELLOW+"Missing semi-colon for line: "+NORMAL)
            print(YELLOW+"->"+string[i-15:i]+RED+"; <-- ?\n"+NORMAL)
        #special case function when there are whitespace between \n and ;
        elif(string[i-1] == ' '):
            clear = specialCaseColon(string,i)
        semi = i+1
    if(clear):
        print(GREEN+"Passed!"+NORMAL)

def specialCaseColon(string,index):
    i = index-1
    while((string[i] == ' ' or string[i] == '\n') and (i != 0)):
        i = i - 1
    if(string[i] != ';'):
        print(YELLOW+"Missing semi-colon for line: "+NORMAL)
        print(YELLOW+"->"+string[i-15:i]+RED+"; <-- ?\n"+NORMAL)
        return 0
    return 1

#Detect proper bracket open and closures
def bracket(string):
    bracket = []
    count = 0
    high = 0
    last = 0
    print(CYAN+"Bracket check: "+NORMAL,end='')
    #Append { } to a list
    for i in range(0,len(string)):
        if(string[i] == '{' or string[i] == '}'):
            bracket.append((string[i],string[i-15:i+1]))
    #Loop through list and count { and }. if { = i++ , else } = i--. If i != 0, there exist missing brackets in the JS
    for i in range(0,len(bracket)):
        if(bracket[i][0] == '{'):
            count = count + 1
            if(high < count):
                high = count
                last = i
        elif(bracket[i][0] == '}'):
            count = count - 1
    #Display detail of missing bracket below
    if(count == 0):
        print(GREEN+"Passed!"+NORMAL)
    else:
        print(RED+"Failed"+NORMAL)
        print(YELLOW+"Missing bracket for: ")
        if(bracket[last][0] == '{'):
            print(bracket[last][1] + RED +" } <-- \n"+NORMAL)
        else:
            print(bracket[last][1] + RED +" { <-- \n"+NORMAL)

#Capture all declared variables in JS by hooking onto keyword 'var'
def variableCollector(master):
    variables = []
    loc = 0
    while((master.find("var ",loc)) != -1):
        i = master.find("var ",loc)
        e = master.find("=",i)
        var = (master[i+4:e-1],e)
        variables.append(var)
        loc = e
    return variables

#Loop through variable list and see for each variable declared, is it used at least once. If not, throw a warning and recommend using consts.
def constant(string,variables):
    print(CYAN+"Static variables: ",end='')
    clean = 1
    for i in range(0,len(variables)):
        if(not(string.find(variables[i][0],variables[i][1]) != -1)):
            print(YELLOW+"Warning")
            print("Variable "+MAGENTA+variables[i][0]+YELLOW+" was never used. Perhaps set it to a constant?\n"+NORMAL)
            clean = 0
    if(clean):
        print(GREEN+"Passed!"+NORMAL)

#See if dynamic variables are freed. Though JS automatically does this, nulling the variables helps in lower languages to prevent UAF
def dynamic(string,variables):
    mallocVars = []
    print(CYAN+"Dynamic variables: "+NORMAL,end='')
    for i in range(0,len(variables)):
        substring = string[variables[i][1]:string.find("\n",variables[i][1])]
        if(substring.find("new ") != -1):
            mallocVars.append(variables[i][0])

    for i in range(0,len(mallocVars)):
        if((string.find(str(mallocVars[i])+" = null") != -1) or (string.find(str(mallocVars[i])+"=null") != -1)):
            mallocVars[i] = "freed"
    clear = 1
    for i in range(0,len(mallocVars)):
        if(mallocVars[i] != "freed"):
            clear = 0
            print(YELLOW+"Warning")
            print("Recommend nulling variable "+MAGENTA+mallocVars[i]+YELLOW+" after use\n"+NORMAL)
    if(clear):
        print(GREEN+"Passed!"+NORMAL)


#Driver
def main():
    variables = []
    master = parse()
    master = noComment(master)
    variables = variableCollector(master)
    
    semiColon(master)
    bracket(master)
    constant(master,variables)
    dynamic(master,variables)


main()