"""
Checks if all detected plugins are in a single category.
"""

import binascii
import json
import os
import pickle
import sys
import xml.etree.ElementTree as ET

from JUCEWrapper import PluginScanner

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

class TagsetError(Exception):
    """
    Raised in the event that a tagset can't be parsed.
    """
    pass

class CachedPlugin:
    """
    Stores the details for a single plugin.
    """
    def __init__(self, name, manufacturer, identifier):
        self._name = name
        self._manufacturer = manufacturer
        self._identifier = identifier

    def getName(self):
        return self._name

    def getManufacturer(self):
        return self._manufacturer

    def getIdentifier(self):
        return self._identifier

def postNotification(title, content):
    os.system(f"osascript -e 'display notification \"{content}\" with title \"{title}\"'")

def suppressStream(stream):
    orig_stream_fileno = stream.fileno()
    orig_stream_dup = os.dup(orig_stream_fileno)
    devnull = open(os.devnull, 'w')
    os.dup2(devnull.fileno(), orig_stream_fileno)


def codeToHex(code):
    """
    Converts a type code to its hex representation.
    """
    return binascii.hexlify(bytes(code, encoding="utf-8")).decode("utf-8")


def buildTagSetFileName(identifier):
    """
    Converts somthing like 'AudioUnit:Effects/aufx,clu2,SNSH'
    to something like 61756678-73686674-534e5348.tagset
    """

    typeCodes = identifier.split("/")[1].split(",")

    return codeToHex(typeCodes[0]) + "-" + codeToHex(typeCodes[1]) + "-" + codeToHex(typeCodes[2]) + ".tagset"


def getCategoriesFromTagset(tagsetPath):
    """
    Assumes the only dict tag is the one we are interested in.

    Raises TagsetError if any exceptions are raised when parsing.
    """
    try:

        tree = ET.parse(tagsetPath)
        root = tree.getroot()

        dictTag = root.find("dict")

        categories = []

        subDictTag = dictTag.find("dict")

        categoryTags = subDictTag.findall("key")

        categories = [categoryTag.text for categoryTag in categoryTags]

    except Exception as e:
        raise TagsetError(str(e))

    return categories


# Check if a cache file exists
CACHE_FILENAME = os.path.join(ROOT_DIR, "cache.p")
plugins = []

if os.path.isfile(CACHE_FILENAME):
    print("Found cache file")

    # Load from the cache file
    plugins = pickle.load(open(CACHE_FILENAME, "rb"))

    print(f"Loaded {len(plugins)} plugins from cache")
else:
    print("No cache file found")

    # Scan the plugins
    scanner = PluginScanner()

    print(f"Scanned {scanner.getNumPlugins()} plugins")

    # Create an array of CachedPlugins so we can write it to the cache file
    for pluginIndex in range(scanner.getNumPlugins()):
        plugin = CachedPlugin(scanner.getName(pluginIndex),
                              scanner.getManufacturer(pluginIndex),
                              scanner.getFileOrIdentifier(pluginIndex))

        plugins.append(plugin)

    # Write the cache file
    pickle.dump(plugins, open(CACHE_FILENAME, "wb"))


# Go through each plugin, check if it appear in the tagset
databasePath = "/Users/<USERNAME>/Music/Audio Music Apps/Databases/Tags"
warningCount = 0

# Load ignore.json
with open(os.path.join(ROOT_DIR, "ignore.json")) as ignoreFile:
    ignoreList = json.load(ignoreFile)

with open(os.path.join(ROOT_DIR, "log.txt"), "w") as logFile:

    for plugin in plugins:

        # Check if this plugin should be ignored
        if f"{plugin.getManufacturer()}-{plugin.getName()}" not in ignoreList:

            # Work out the tagset file name for this plugin
            tagsetFileName = buildTagSetFileName(plugin.getIdentifier())
            tagsetFilePath = os.path.join(databasePath, tagsetFileName)

            logPrefix = f"\n{plugin.getManufacturer()} - {plugin.getName()} ({tagsetFileName}) : "

            try:
                # Check the plugin has a tagset
                if os.path.isfile(tagsetFilePath):

                    # Get the categories in the tagset
                    categories = getCategoriesFromTagset(tagsetFilePath)

                    if len(categories) == 0:
                        logFile.write(logPrefix + "has no categories")
                        warningCount += 1
                    elif len(categories) > 1:
                        logFile.write(logPrefix + f"is in: {categories}")
                        warningCount += 1
                else:
                    logFile.write(logPrefix + "has no tagset")
                    warningCount += 1

            except TagsetError as e:
                logFile.write(logPrefix + f"failed to parse tagset ({e})")
                warningCount += 1

            except Exception as e:
                logFile.write(logPrefix + f"failed to process ({e})")
                warningCount += 1

postNotification(title="AU Checker",
                 content=f"{warningCount} warnings, {len(plugins)} plugins scanned")

# Redirect stdout and stderr otherwise JUCE will produce tons of output on exit
suppressStream(sys.stdout)
suppressStream(sys.stderr)
