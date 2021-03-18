import os
import shutil
import operator
import requests, uuid, json
import re
import time

apiKey = ""
location = "westus2"

def translate(input):
    endpoint = "https://api.cognitive.microsofttranslator.com"
    path = '/translate'
    constructed_url = endpoint + path
    params = {
        'api-version': '3.0',
        'from': 'ja',
        'to': 'en'
    }
    constructed_url = endpoint + path
    headers = {
        'Ocp-Apim-Subscription-Key': apiKey,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{
        'text': bigString
    }]
    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    output = json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')).splitlines()[4].strip()[9:-2]
    time.sleep(60 * (len(input) / 33000)) #azure limits free tier to 33,000 characters per minute
    return output

games = list()
if os.path.isdir("C:\\Program Files (x86)\\Iris"):
    for game in os.listdir("C:\\Program Files (x86)\\Iris"):
        print("Found game:", game)
        games.append(["Iris", game])
    
print("==================================")
print("Please select the game to translate")    
for i, game in enumerate(games, start=1):
    print(i, game)
chosenGame = int(input()) - 1 #-1 because i used start=1 above
print("==================================")

print("Finding Scene.pck...", end="")
#check if theres a scene.pck file
if os.path.isfile("C:\\Program Files (x86)\\" + games[chosenGame][0] + "\\" + games[chosenGame][1] + "\\Scene.pck") == False:
    print("ERROR: Unable to locate Scene.pck for this game")
    exit()
#okay we have our scene.pck, time to copy to working directory and extract
try:
    os.mkdir("tmpcoom")
except OSError as error:
    pass
    
src = "C:\\Program Files (x86)\\" + games[chosenGame][0] + "\\" + games[chosenGame][1] + "\\Scene.pck"
dst = "tmpcoom\\Scene.pck"
shutil.copyfile(src, dst)
print("DONE")

print("Extracting Scene.pck...", end="")
# TODO: add support for extracting text
#print("WARNING: Currently there is no support for extracting Scene.pck, please copy all .ss files to the tmpcoom directory.")
#input()
print("DONE")

print("Reading .ss files...", end="")
ssFiles = list()
for file in os.listdir("tmpcoom\\"):
    if(file[-1] == 's' and file[-2] == 's' and file[-3] == '.'):
        print(".", end="", flush=True)
        if(os.path.isfile(".\\tmpcoom\\" + file[0:-3] + ".txteng")): continue #already translated
        ssFiles.append(file[0:-3])
        if(os.path.isfile(".\\tmpcoom\\" + file[0:-3] + ".txt")): continue; #already extracted
        os.system("tools\\ssdump.exe tmpcoom\\" + file + " tmpcoom\\" + file[0:-3] + ".txt")
print("DONE")

for file in ssFiles:
    print("Translating", file + "...", end="", flush=True)
    enLines = list()
    with open("tmpcoom\\" + file + ".txt", "r", encoding="utf-8") as f:
        jpLines = f.read().splitlines()
        bigString = ""
        output = ""
        for line in jpLines:
            #filter out the non translatable text
            if(len(line) == 0): continue;
            if(len(line) < 7): 
                continue; #skip anything too short
            if(line[1] == '/'): continue; #skip comment
            strippedLine = line[7:]
            if(re.match("[_/a-zA-Z0-9\s\{\}$]+", strippedLine)): #regex magic to find translatable strings
                continue
                
            bigString = bigString + '\n' + strippedLine
            if(len(bigString) > 9000): #if we get close to the limit of azure (10,000) then split off the string and translate
                output = output + translate(bigString)
                bigString = ""
                print(".", end="", flush=True)
        output = output + translate(bigString) #fix any stragglers
        #okay now we have a huge output string
        counter = 1;
        #clean up some weird shit from the translation
        splitOutput = output.replace("\\n", "\n").replace("\\", "").replace("\"", "").splitlines()
        for line in jpLines:
            #filter out the non translatable text
            if(len(line) == 0): continue;
            if(len(line) < 7): 
                enLines.append(line) #add the short line 
                continue; #skip anything too short
            if(line[1] == '/'): continue; #skip comment
            strippedLine = line[7:]
            if(re.match("[_/a-zA-Z0-9\s\{\}$]+", strippedLine)): #regex magic to find translatable strings
                enLines.append(line)
                continue
            pre = line[:7]
            if(len(splitOutput) > 0):
                post = splitOutput[counter]
            else:
                post = "";
            enLines.append(pre + post) #re patch the english onto the original line
            counter = counter + 1
            
    f = open("tmpcoom\\" + file + ".txteng", "w", encoding="utf-8")    
    for line in enLines:
        f.write(line)
        f.write("\n")
    f.close()
    
    print("DONE")
    
#Time to repack!!

try:
    os.mkdir("outcoom")
except OSError as error:
    pass
print("Repacking .ss files...", end="")
for file in os.listdir("tmpcoom\\"):
    if(file[-1] == 's' and file[-2] == 's' and file[-3] == '.'):
        os.system("tools\\ssinsert.exe .\\tmpcoom\\" + file[:-3] + ".ss .\\tmpcoom\\" + file[:-3] + ".txteng .\\outcoom\\" + file)
        print(".", end="", flush=True)
print("DONE")

print("Cleaning up...", end="")
#os.system("rd /s /q \\tmpcoom")
print("DONE")

#fully translated ss files should now be in outcoom