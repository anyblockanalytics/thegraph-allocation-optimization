from src.webapp.overview import streamlitEntry
import pyutilib.subprocess.GlobalData

if __name__ == '__main__':

    pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False
    streamlitEntry()