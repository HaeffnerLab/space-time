import labrad
import sys
import time
import datetime

now = datetime.datetime.now()
date = now.strftime("%Y%m%d")
TIME = now.strftime('%H%M%S')
cxn = labrad.connect('192.168.169.30')
dmmtemp = cxn.keithley_2110_dmm
dmmpress = cxn.keithley_2100_dmm
dmmtemp.select_device('cct_camera GPIB Bus - USB0::0x05E6::0x2110::1408025')
dmmpress.select_device('cct_camera GPIB Bus - USB0::0x05E6::0x2100::1243106')

while 1:
    f = open(date + 'spacetime_openanglevalve', 'a')
    now = datetime.datetime.now()
    date = now.strftime("%Y%m%d")
    TIME = now.strftime('%H%M%S')
    temp = dmmtemp.get_temp()
    f.write( str(temp) + ' ' + str(dmmpress.get_dc_volts()) + ' ' + date + '_' + TIME + '\n')
    f.close()
    time.sleep(1.)

