import requests;
import xml.etree.ElementTree as ET;
from pathlib import Path;
from packaging import version;
from tqdm import tqdm;
import tkinter as tk;

class Mod():
    class state():
        def __init__(self):
            self.canUpdate = False
            self.isUpdated = False
            
    def __init__(self, name, url, version):
        self.ModName = name
        self.ModLink = url
        self.Version = version
        self.currentState = self.state()

class ModManager():
    # Game Location
    fileLocation = Path("G:\SteamLibrary\steamapps\common\Haiku the Robot\BepInEx\config")

    # Get the path of every ever installed mod
    ListOfInstalledMods = list(fileLocation.glob('**/*.cfg'));
    # Extract the Name,Version of these files into this Dict
    DictOfLocalModsAndVersions = {}
    # Extract the Name,Url from modlinks.xml into this Dict
    DictOfExternalModsAndVersions = {}
    headers = { 'Authorization': 'token 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'}

    def __init__(self):
        # Find every local Name,Version and save it in the dictionary
        self.getLocalVersions()
        # Find every external Name,Url and save it in the dictionary
        self.parseXMLFile()
        # Go through each mod in modlinks.xml, find its label on Github and compare it to local versions
        for i, (name,url) in enumerate(self.DictOfExternalModsAndVersions.items()):
            response = requests.get(url, headers = self.headers)
            result = self.compareVersionWithLocalFile(name, self.getVersionOfUrl(response))
            if (result == -1): print("Error in accessing Mod: ", name, " Url:", url)
            if (result == 0): print("No new version needed \n")
            if (result == 1):
                print("New version needed, downloading!")
                # self.downloadFile(self.getDownloadUrl(response))

    def getLocalVersions(self):
        for ModFile in self.ListOfInstalledMods:
            with ModFile.open() as f: 
                firstLine = f.readline()
                plugin = firstLine.split('plugin ')[-1][:-1]
                version = plugin.split(' ')[-1][1:]
                pluginName = firstLine.split('plugin ')[-1][:plugin.index(version)-2]
                self.DictOfLocalModsAndVersions[pluginName] = version
        self.DictOfLocalModsAndVersions.pop('[Caching]', None)

    def parseXMLFile(self):
        tree = ET.parse('modlinks.xml')
        root = tree.getroot()
        for Mod in root.iter('Mod'):
            ModName = Mod.find('Name').text.strip()
            ModLink = Mod.find('Link').text.strip()
            if not ModName or not ModLink: continue
            self.DictOfExternalModsAndVersions[ModName] = ModLink

    def getVersionOfUrl(self, response):
        return response.json()["tag_name"]

    def getDownloadUrl(self, response):
        return response.json()["assets"][0]['browser_download_url']

    def compareVersionWithLocalFile(self, name, externalVersion) -> int: # Return 1 if new Version is needed, 0 if not, -1 if error
        print(name, "\n   External Version: ", externalVersion, " Local Version: ", self.DictOfLocalModsAndVersions[name])
        if (self.DictOfLocalModsAndVersions.get(name,False)):
            if (version.parse(externalVersion) > version.parse(self.DictOfLocalModsAndVersions[name])):
                return 1
            else: 
                return 0
        return -1

    def downloadFile(self, url):
        name = url.split("/")[-1]
        response = requests.get(url, stream = True, headers = self.headers)
        with open(name, "wb") as handle:
            for data in tqdm(response.iter_content(chunk_size = 5)):
                handle.write(data)

manager = ModManager()
            