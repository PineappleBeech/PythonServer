import requests
import os

def main():
    version_manifest = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest.json').json()
    latest_version = version_manifest['latest']['release']
    for i in range(1, len(version_manifest['versions'])):
        if version_manifest['versions'][i]['id'] == latest_version:
            latest_version_index = i
            break
    version_json = requests.get(version_manifest['versions'][latest_version_index]['url']).json()
    with open("server.jar", "wb") as f:
        f.write(requests.get(version_json['downloads']['server']['url']).content)

    #runs the commmand to run the data generator
    os.system(r"%JAVA_HOME%\bin\java.exe -DbundlerMainClass=net.minecraft.data.Main -jar server.jar --all")

if __name__ == "__main__":
    main()