
#system variables for CrateTest.py

# Path to directory with all required scripts (including CrateTest.py)
# CrateTest.py should be run from this directory
SCRIPT_DIR = "/nfshome0/zmao/CrateTest"

# Path to AMC13Tool.exe
AMC_TOOL= "/opt/xdaq/bin/AMC13Tool.exe"

# Path to uHTRtool.exe
HTR_TOOL= "/opt/xdaq/bin/uHTRtool.exe" 

# Path to directory ttt_pychips
# In this directory, there should be another directory scripts (not to be confused with the SCRIPT_DIR pathed aboved) which contains TTT scripts such as random_100kHz_rules which can be used to send triggers from the TTT to the AMC13 
TTT_DIR = "/nfshome0/zmao/ttt_pychips"

# Serial number for AMC13 to be used in test (decimal)
AMC_SERIAL = 45

# Slot numbers for uHTRs to be used in test
# (1 based, i.e. AMC slot number visible on crate)
UHTR_SLOT = [4]



# Added by Zaixing for for more general usage
UTCA_CRATE = 28
