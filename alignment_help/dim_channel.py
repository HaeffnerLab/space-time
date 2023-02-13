CHANNEL = '729vert'

import labrad
import time
from labrad.units import WithUnit as U

cxn = labrad.connect()
while True:
    amp = cxn.pulser.amplitude(CHANNEL)['dBm']
    for i in range(20):
        amp -= 1
        cxn.pulser.amplitude(CHANNEL, U(amp, 'dBm'))
        time.sleep(0.05)
    for i in range(20):
        amp += 1
        cxn.pulser.amplitude(CHANNEL, U(amp, 'dBm'))
        time.sleep(0.05)