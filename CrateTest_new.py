#! /usr/bin/env python

#Script to setup and run crate test using uHTRTool, AMC13Tool, and TTTtool
#assume tools have been setup and made

from optparse import OptionParser
import systemVars as sv
import os as os
import time as time
import subprocess as subprocess
import shlex as shlex
import logging

######################
# Set up logger
######################
# logger is ready for use, but messages not being used

logger = logging.getLogger('CrateTest')
hdlr = logging.FileHandler('/var/tmp/CrateTest.log')
formatter = logging.Formatter('[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

######################
# Parse Options
######################

parser = OptionParser()
parser.add_option("-v", "--verbose",
                  action="store_true",dest="verbose", default=False,
                  help="print outputs -- does not yet do anything ")
parser.add_option("-n","--serial", dest="sn",
                  help="AMC13 Serial Number",
                  default=0, metavar="<n>", type=int)
parser.add_option("-b", "--batchsize", dest="tot_evt_dump",
                  help="Total number of events in SDRAM before dumping (# of events per batch)",
                  default=100, metavar="<n>", type=int)
parser.add_option("-e","--maxevt", dest="max_evt",
                  help="Total number of events dumped before ending program",
                  default=200, metavar="<n>", type=int)
# Possible implementation of sending the list of uHTR slots that will be used
# Python 2.7 uses argparse (optarse is deprecated), which can support nargs='*', arbitrary number of arguments
# would not be supported in older versions of python which could cause error, skipping for now
# For now, uHTR slots have to be defined in systemVars.py 

#parser.add_option("-s", "--slot", dest="uhtr_slots",
#                  help="List of uHTR slot numbers (1 based)",
#                  default=2, metavar="<n>", type=int)
(options, args) = parser.parse_args()


# Setup useful directories
# Need to be change to environmental variables or command line inputs
#ttt_dir = "/home/dzou/src/ttt_pychips"
#script_dir = "/home/dzou/src/11_9_9/hcal/hcalUpgrade/amc13/scripts"
#amc_tool= "/home/dzou/src/11_9_9/hcal/hcalUpgrade/amc13/bin/linux/x86_64_slc5/AMC13Tool.exe"
#htr_tool= "/home/dzou/src/11_9_9/hcal/hcalUHTR/bin/linux/x86_64_slc5/uHTRtool.exe" #linux/x86_64_slc5 change depend on comp
ttt_dir = sv.TTT_DIR
script_dir = sv.SCRIPT_DIR
amc_tool = sv.AMC_TOOL
htr_tool = sv.HTR_TOOL

#create neccessary directories
if not os.path.exists("%s/dev" %(script_dir)):
    os.system("mkdir %s/dev" %(script_dir) )
if not os.path.exists("%s/results" %(script_dir)):
    os.system("mkdir %s/results" %(script_dir) )

#Serial number of AMC13
if (options.sn):
    amcSerial = options.sn
else:
    amcSerial = sv.AMC_SERIAL
    #print "NOTE: Using default amc13 serial number from systemVars.py"
    
# Setup AMC slot of uHTRs in crate (1 base i.e. number seen on crate)
uhtr_crate_num = sv.UHTR_SLOT
utca_crate_num = sv.UTCA_CRATE

# Setup environmental variables for TTT
# Need to change to support both .sh and .csh
# Add to initialization in beginning of script
t_env_command = "source %s/environ.sh" % (ttt_dir)
os.system(t_env_command)


################################
# Set up uHTR
###############################

# Need to check if daqpath already enable
# atm, if the daqpath is already enabled, running the script (default) will disable daq path

# Check if DAQ Path is already enabled
# This method is a bit round about and may be done differently in the future

#DAQ_enabled = []

#for i in range(len(uhtr_crate_num)):
#    print "i is %d " % (i)
#    DAQ_enabled.append(0)

for i in uhtr_crate_num:
    # Check if DAQ Path is already enabled
    # This method is roundabout and may be done differently

    # open uHTRtool and save status to daqcheck.txt
    DAQ_enabled = False
    daq_check_command =  "%s -u 192.168.%d.%d -s %s/checkDAQ.uhtr > %s/dev/daqcheck.txt" % (htr_tool,utca_crate_num,i*4, script_dir, script_dir)
    os.system(daq_check_command)
    # open daqcheck.txt and check to see if DAQ Path is enabled
    #f = open('daqcheck.txt', 'r')
    #for line in f:
    #    print line
    grep_command = "grep 'DAQ Path' %s/dev/daqcheck.txt " %(script_dir)
    p_grep = subprocess.Popen(grep_command,shell=True, stdout=subprocess.PIPE)
    check_whole = p_grep.communicate()[0]
    check_list = shlex.split(check_whole)
    #print "check whole: %s" % (check_whole)
    #print "check[3] : %s" % (check_list[3])
    if (len(check_list)>2):
        if (check_list[3]=='ENABLED'):
            #print "check that is Enabled"
            DAQ_enabled = True
        elif (check_list[3]=='DISABLED'):
            DAQ_enabled = False
            #print "DAQ is disabled"
        else:
            print "Problem while checking DAQ Path status"
            quit()
    else:
        print "No line with 'DAQ Path' found in DAQ Path status or line was shorter than expected \n Please check daqcheck.txt"
        quit()

    # Enable DAQ Path if not enabled
    if (DAQ_enabled==False):
        print "Enabling DAQ Path for uHTR in slot AMC %d" % (i)
        u_daq_command = "%s -u 192.168.%d.%d -s %s/enableDAQPath.uhtr > %s/dev/null" % (htr_tool,utca_crate_num,i*4, script_dir, script_dir)
        os.system(u_daq_command)
    else:
        print "DAQ Path for uHTR in slot AMC %d already enabled" % (i)
        #logger.warning('DAQ Path already enabled')
        #logger.error('Here is an error test')
        logger.info("DAQ Path for uHTR in slot AMC %d already enabled" % (i))

    # Enable Send Local Trigger
    #u_trig_command ="%s -u 192.168.115.%d -s %s/sendTrigs.uhtr" % (htr_tool, i*4,  script_dir)
    #os.system(u_trig_command)

###############################
# Prep AMC13 for event saving (perhaps start continuous dump)
###############################

# Make sure to stop any triggers before preparing the AMC13
 
t_trig_stop = "%s/scripts/stop_trigs > %s/dev/null" % (ttt_dir, script_dir)
os.system(t_trig_stop)
# Create script to run AMC13Tool to enable link to uHTR's and turn on prescaling
amcPrepFile = open("%s/dev/prepAMC.txt" %(script_dir), "w")
amcPrepFile.write("rg\n");
amcPrepFile.write("rc\n");
amcPrepFile.write("i ");
for i in range(len(uhtr_crate_num)):
    amcPrepFile.write("%d" % (uhtr_crate_num[i]-1) );
    if (i < len(uhtr_crate_num)-1):
        amcPrepFile.write(",");
amcPrepFile.write(" b\n");
amcPrepFile.write("mm e\n");
amcPrepFile.write("sps 13\n"); # Will change to use prescale variable
amcPrepFile.write("q\n");
amcPrepFile.close()
# Run script on 
amc13_prep = "%s -u -n %d -x %s/dev/prepAMC.txt > %s/dev/null" % (amc_tool,amcSerial, script_dir, script_dir)
#amc13_prep = "%s -u -n %d -x %s/rateAMC_every.txt" % (amc_tool,amcSerial,script_dir) 
os.system(amc13_prep)
amc13_status = "%s -u -n %d -x %s/amcStatus.txt > %s/dev/initialStatus.txt" % (amc_tool,amcSerial,script_dir, script_dir)
os.system(amc13_status)

#######################################################################
# Loop until large number of events (~10^6) are dump (for overnight runs)
########################################################################
batch_no = 1
totalEventsDumped = 0
batchSize = options.tot_evt_dump
if (options.tot_evt_dump > options.max_evt):
    batchSize = options.max_evt

while (totalEventsDumped < options.max_evt):
    
    print "Batch Num: %d" % (batch_no)
    
    # Send Trigs from TTT

    # 100kHz random
    t_trig_start = "%s/scripts/random_100kHz_rules > %s/dev/null" % (ttt_dir, script_dir)
    os.system(t_trig_start)

    # 10 trigs
    # t_trig_start = "%s/scripts/10_l1as" % (ttt_dir)
    # os.system(t_trig_start)

    # Check AMC13Tool Status continuously until sufficient events
    # Currently reading status to file and then reading from file. Perhaps should add/use a command in AMC13Tool to stop taking events once threshold is met
    # Due to delay in reading number of events to stopping triggers, more events are built than requested by tot_evt_dump

    evt_count = 0
    print "Counting Events..."
    while (evt_count < batchSize):
        check_evt_command = "%s -u -n %d -x %s/amcStatus.txt > %s/dev/evtStatus.txt" % (amc_tool,amcSerial,script_dir, script_dir)
        os.system(check_evt_command)
        find_evt_count = "grep 'Unread SDRAM Evts' %s/dev/evtStatus.txt" %(script_dir)
        p_evt = subprocess.Popen(find_evt_count,shell=True, stdout=subprocess.PIPE)
        evt_whole = p_evt.communicate()[0]
        evt_list = shlex.split(evt_whole)
        print "evt whole: %s" % (evt_whole)
        print "evt[4] : %s" % (evt_list[4])
        if (len(evt_list)>4):
            evt_count = int(evt_list[4],16)
            print "Events Saved: %d" % (evt_count)
        time.sleep(1)
    print "Minimum number of events saved, stopping triggers and dumping..."
    t_trig_stop = "%s/scripts/stop_trigs > %s/dev/null" % (ttt_dir, script_dir)
    os.system(t_trig_stop)

    # Dump events to file (this or start continuous dump early and stop it here)

    dumpScript = open("%s/results/dumpFile.txt" %(script_dir), "w")
    dumpScript.write("st\n");
    dumpScript.write("df %s/results/dump%d.dat\n" % (script_dir,batch_no));
    dumpScript.write("q\n");
    dumpScript.close()
  
    dump_evt_command = "%s -u -n %d -x %s/results/dumpFile.txt > %s/results/endStatus%d.txt" % (amc_tool,amcSerial,script_dir, script_dir,batch_no)
    os.system(dump_evt_command)

    find_evt_final_count = "grep 'Unread SDRAM Evts' %s/results/endStatus%d.txt " % (script_dir,batch_no)
    pf_evt = subprocess.Popen(find_evt_final_count,shell=True, stdout=subprocess.PIPE)
    evt_f_whole = pf_evt.communicate()[0]
    evt_f_list = shlex.split(evt_f_whole)
    if (len(evt_f_list) > 4):
        evt_f_count = int(evt_f_list[4],16)
        print "%d events dumped to dump%d.dat with status saved to endStatus%d.txt" % (evt_f_count,batch_no,batch_no)
    else:
        print "Problem with Saved events in SDRAM before dumping"
        quit()

    # Check dumped events (w/ dumpFED?)
    # Not implemented yet
  


    # Increment counters
    batch_no += 1
    totalEventsDumped += evt_f_count
    print "TotEvt: %d" %(totalEventsDumped)
    
print "Total Evts Reached"
