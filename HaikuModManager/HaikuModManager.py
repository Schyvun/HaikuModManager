import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from packaging import version
from tqdm import tqdm
import tkinter as tk
from tkinter import ttk
from githubToken import AuthenticationToken

class Mod(): 
    def __init__(self, name, VersionLocal = '', VersionExternal = '', url = '', needUpdateState = False, description = ''):
        self.ModName = name
        self.Description = description
        self.URL = url
        self.VersionLocal = VersionLocal
        self.VersionExternal = VersionExternal
        self.state = needUpdateState

class ModManager():
    # Game Location
    fileLocation = Path("G:\SteamLibrary\steamapps\common\Haiku the Robot\BepInEx\config")
    header = AuthenticationToken

    # List of every mod hashed by name
    ListOfMods: dict[str,Mod] = {} 
    

    def __init__(self):
        # Find every local Name,Version and save it in the ModList
        self.getLocalVersions()
        # Find every external Name,Url and save it in the ModList
        self.parseXMLFile()
        # Go through each mod in modlinks.xml, find its label on Github and compare it to local versions
        for i, (name,modItem) in enumerate(self.ListOfMods.items()):  
            url = modItem.URL
            if (not url): continue
            result = self.compareVersionWithLocalFile(name, self.ListOfMods[name].VersionExternal)
            self.ListOfMods[name].state = result

    def getLocalVersions(self):
        for ModFile in list(self.fileLocation.glob('**/*.cfg')):
            with ModFile.open() as f: 
                firstLine = f.readline()
                plugin = firstLine.split('plugin ')[-1][:-1]
                version = plugin.split(' ')[-1][1:]
                pluginName = firstLine.split('plugin ')[-1][:plugin.index(version)-2]
                if (pluginName == '[Caching]'): continue
                self.ListOfMods[pluginName] = Mod(pluginName,version)

    def parseXMLFile(self):
        # Parse the xml file to add the URL to each Mod
        tree = ET.parse('modlinks.xml')
        root = tree.getroot()
        for ModItem in root.iter('Mod'):
            # Get Name and Link from the xml file
            ModName = ModItem.find('Name').text.strip()
            ModGithubApiLink = ModItem.find('Link').text.strip()
            ModDescription = ModItem.find('Description').text.strip()

            # Access github api with the link provided
            try:
                response = requests.get(ModGithubApiLink, headers = self.header)
            except requests.exceptions.RequestException as e:
                print("Error when accesing url from Mod: ", ModName, " Error was: \n", e)
                continue
            Version = response.json()["tag_name"]
            ModLink = self.getDownloadUrl(response)
            if not ModName or not ModLink: continue
            if (self.ListOfMods.get(ModName, False)):
                self.ListOfMods[ModName].URL = ModLink
            else:
                self.ListOfMods[ModName] = Mod(ModName,url = ModLink, needUpdateState = True)
            self.ListOfMods[ModName].Description = ModDescription
            self.ListOfMods[ModName].VersionExternal = Version

    def getDownloadUrl(self, response):
        return response.json()["assets"][0]['browser_download_url']

    def compareVersionWithLocalFile(self, name, externalVersion) -> bool: # Returns true if an update is needed
        localVersion = self.ListOfMods[name].VersionLocal
        print(name, "\n   External Version: ", externalVersion, " Local Version: ", localVersion)
        # Return true if there's no local version since it can't be up to date if it's not installed
        if (not localVersion): return True
        if (version.parse(externalVersion) > version.parse(localVersion)):
            return True
        else: 
            return False

    def downloadFile(self, url):
        name = url.split("/")[-1]
        response = requests.get(url, stream = True, headers = self.header)
        with open(name, "wb") as handle:
            for data in tqdm(response.iter_content(chunk_size = 5)):
                handle.write(data)

class UI():
    # Code from Stackoverflow https://stackoverflow.com/questions/13141259/expandable-and-contracting-frame-in-tkinter
    class ToggledFrame(tk.Frame):
        def __init__(self, parent, text="", *args, **options):
            tk.Frame.__init__(self, parent, *args, **options)

            self.show = tk.IntVar()
            self.show.set(0)

            self.title_frame = ttk.Frame(self)
            self.title_frame.pack(fill="x", expand=1)

            ttk.Label(self.title_frame, text=text).pack(side="left", fill="x", expand=1)

            self.toggle_button = ttk.Checkbutton(self.title_frame, width=2, text='+', command=self.toggle,
                                                variable=self.show, style='Toolbutton')
            self.toggle_button.pack(side="left")

            self.sub_frame = tk.Frame(self, relief="sunken", borderwidth=1)

        def toggle(self):
            if bool(self.show.get()):
                self.sub_frame.pack(fill="x", expand=1)
                self.toggle_button.configure(text='-')
            else:
                self.sub_frame.forget()
                self.toggle_button.configure(text='+')


if __name__ == "__main__":
    root = tk.Tk()
    manager = ModManager()
    ui = UI()
    
    for i, (name,modItem) in enumerate(manager.ListOfMods.items()):
        # print(Mod.ModName, Mod.URL,Mod.VersionLocal,Mod.VersionExternal, Mod.state)
        if (not modItem.URL): continue
        t = ui.ToggledFrame(root, text=name, relief="raised", borderwidth=1)
        t.grid(column = 0, row = i, pady=2, padx=2)

        ttk.Label(t.sub_frame, text=modItem.Description).pack(side="left", fill="x", expand=1)

    root.mainloop()

# ui = UI()