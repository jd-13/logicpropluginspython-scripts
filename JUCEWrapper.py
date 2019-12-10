"""
Python wrapper for the JUCE based dll.
"""

from ctypes import cdll, c_char_p, c_void_p, c_int
import os
import sys

class SuppressStream():

    def __init__(self, stream=sys.stderr):
        self.orig_stream_fileno = stream.fileno()

    def __enter__(self):
        self.orig_stream_dup = os.dup(self.orig_stream_fileno)
        self.devnull = open(os.devnull, 'w')
        os.dup2(self.devnull.fileno(), self.orig_stream_fileno)

    def __exit__(self, type, value, traceback):
        os.close(self.orig_stream_fileno)
        os.dup2(self.orig_stream_dup, self.orig_stream_fileno)
        os.close(self.orig_stream_dup)
        self.devnull.close()


class PluginScanner:
    def __init__(self):
        SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
        LIB_PATH = os.path.join(SCRIPT_DIR, "JUCEBinding/Builds/MacOSX/build/Debug/JUCEBinding.dylib")

        self.lib = cdll.LoadLibrary(LIB_PATH)
        self.lib.PluginScanner_new.argtypes = []
        self.lib.PluginScanner_new.restype = c_void_p

        with SuppressStream():
            with SuppressStream(sys.stdout):
                self.obj = self.lib.PluginScanner_new()

    def getFileOrIdentifier(self, index):
        self.lib.PluginScanner_getFileOrIdentifier.argtypes = [c_void_p, c_int]
        self.lib.PluginScanner_getFileOrIdentifier.restype = c_char_p

        with SuppressStream():
            with SuppressStream(sys.stdout):
                retVal = self.lib.PluginScanner_getFileOrIdentifier(self.obj, index).decode("utf-8")

        return retVal

    def getManufacturer(self, index):
        self.lib.PluginScanner_getManufacturer.argtypes = [c_void_p, c_int]
        self.lib.PluginScanner_getManufacturer.restype = c_char_p

        with SuppressStream():
            with SuppressStream(sys.stdout):
                retVal = self.lib.PluginScanner_getManufacturer(self.obj, index).decode("utf-8")

        return retVal

    def getName(self, index):
        self.lib.PluginScanner_getName.argtypes = [c_void_p, c_int]
        self.lib.PluginScanner_getName.restype = c_char_p

        with SuppressStream():
            with SuppressStream(sys.stdout):
                retVal = self.lib.PluginScanner_getName(self.obj, index).decode("utf-8")

        return retVal

    def getNumPlugins(self):
        self.lib.PluginScanner_getNumPlugins.argtypes = [c_void_p]
        self.lib.PluginScanner_getNumPlugins.restype = c_int

        with SuppressStream():
            with SuppressStream(sys.stdout):
                retVal = self.lib.PluginScanner_getNumPlugins(self.obj)

        return retVal
