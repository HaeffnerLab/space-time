CHANNEL = '729vert'

import labrad
import time

cxn = labrad.connect()
while True:
    cxn.pulser.output(CHANNEL, True)
    time.sleep(0.2)
    cxn.pulser.output(CHANNEL, False)
    time.sleep(0.2)