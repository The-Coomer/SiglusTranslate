import os
import shutil
import operator
import requests, uuid, json
import re

apiKey = ""
location = "westus2"

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

print("Reading .ss files", end="")
ssFiles = list()
for file in os.listdir("tmpcoom\\"):
    if(file[-1] == 's' and file[-2] == 's' and file[-3] == '.'):
        ssFiles.append(file[0:-3])
        os.system("tools\\ssdump.exe tmpcoom\\" + file + " tmpcoom\\" + file[0:-3] + ".txt")
        print(".", end="", flush=True)
print("DONE")

for file in ssFiles:
    print("Translating", file, end="")
    enLines = list()
    with open("tmpcoom\\" + file + ".txt", "r", encoding="utf-8") as f:
        jpLines = f.read().splitlines()
        counter = 0
        for line in jpLines:
            #filter out the non translatable text
            if(len(line) == 0): continue;
            if(len(line) < 7): 
                enLines.append(line) #add the short line 
                continue; #skip anything too short
            if(line[1] == '/'): continue; #skip comment
            print(line)
            strippedLine = line[7:]
            if(re.match("^[_/a-zA-Z0-9\s\{\}]+$", strippedLine)): #regex magic to find translatable strings
                enLines.append(line)
                continue
            
            #send the remaining string to azure cloud
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
                'text': strippedLine
            }]
            request = requests.post(constructed_url, params=params, headers=headers, json=body)
            response = request.json()
            output = json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')).splitlines()[4].strip()[9:-2]
            #write line to enLines
            
            enLines.append(line[:7] + output)
            counter = counter + 1
            if operator.mod(100 * counter / len(jpLines), 1) == 0:
                print(".", end="", flush=True)
            
    f = open("tmpcoom\\" + file + ".txt", "w", encoding="utf-8")    
    for line in enLines:
        f.write(line)
        f.write("\n")
    f.close()
    
    print("DONE")
