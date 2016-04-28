import numpy as np
import matplotlib.pyplot as plt

one_ion = [58,128,377,442]
two_ions = [54,170,369,443]
three_ions = [55,150,167,368,368,369,446]
four_ions = [51,144,161,364,367,384,446]
five_ions = [49,99,136,157,359,367,389,444]
six_ions = [47,96,128,359,371,390,442]
seven_ions = [43,91,120,358,372,394,440]
eight_ions= [46,128,381,438]
nine_ions = [41,119]
ten_ions = [39]
eleven_ions = []
twelve_ions = [25,80,391,440]

Freqs = [one_ion,two_ions,three_ions,four_ions,five_ions,six_ions,seven_ions,eight_ions,nine_ions,ten_ions,eleven_ions,twelve_ions]

plt.figure()
xdata=[]
ydata=[]
for i in range(0,len(Freqs)):
    color = (i+1)/len(Freqs)
    x = (i+1)*np.ones_like(Freqs[i])
    y=Freqs[i]
    if y != []:
        xdata.append(x[0])
        ydata.append(y[0])

plt.plot(xdata,ydata)
plt.title('Fundamental Axial Frequencies vs. Ion Number')
plt.xlabel('# of Ions in the Ring')
plt.ylabel('Frequency (kHz)')
plt.axis([0,13,0,60])


plt.figure()

fields2 = [-0.011,-0.012,-0.013,-0.015,-0.017,-0.020,-0.023,-0.026,-0.029,-0.032,-0.035,-0.038,-0.041,-0.044,-0.047,-0.05,-0.053,-0.056,-0.059,-0.062]
fields2off = (fields2) + np.ones_like(fields2)*0.01
F2 = [22,26,31,40,48,58,65,74,82,88,94,100,105,110,115,119,124,128,132,136]
plt.plot(fields2off,F2)
plt.title('Fundamental Axial Frequencies vs. Stray Field for 4 ions')
plt.xlabel('Stray Field')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

fields4 = [-0.012,-0.014,-0.016,-0.018,-0.020,-0.022,-0.024,-0.026,-0.028,-0.030,-0.032,-0.034,-0.036,-0.038,-0.040,-0.042,-0.044,-0.046,-0.048,-0.050,-0.052,-0.054,-0.056,-0.058,-0.060,-0.062,-0.064,-0.070,-0.075,-0.080,-0.085,-0.095,-0.105]
fields4off = (fields4) + np.ones_like(fields4)*0.008
F4 = [29,38,44,51,57,63,68,73,78,82,86,90,94,98,101,105,108,111,114,117,120,122,125,128,130,133,135,142,148,153,158,167,176]
plt.plot(fields4off,F4)
plt.title('Fundamental Axial Frequencies vs. Stray Field for 4 ions')
plt.xlabel('Stray Field')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

fields6 = [-0.014,-0.016,-0.018,-0.020,-0.022,-0.024,-0.026,-0.028,-0.030,-0.032,-0.034,-0.036,-0.038,-0.040,-0.042,-0.045,-0.048,-0.051,-0.054,-0.057,-0.06]
fields6off = (fields6) + np.ones_like(fields6)*0.009
F6 = [31,39,45,52,58,63,68,73,78,82,86,90,94,97,101,105,110,115,119,123,127]
plt.plot(fields6off,F6)
plt.title('Fundamental Axial Frequencies vs. Stray Field for 6 ions')
plt.xlabel('Stray Field')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

fields7 = [-.016,-.019,-.022,-.025,-.028,-0.031,-.034,-.037,-.040,-.043,-.046,-.049,-.052,-0.055,-.058,-.061,-.064,-0.067,-0.070,-0.073,-0.076]
fields7off = (fields7) + np.ones_like(fields7)*0.009
F7 = [36,46,55,64,71,78,84,90,95,100,105,110,115,119,123,127,131,135,139,142,145]
plt.plot(fields7off,F7)
plt.title('Fundamental Axial Frequencies vs. Stray Field for 11 ions')
plt.xlabel('Stray Field')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

fields8 = [-.014,-.016,-.018,-.020,-.022,-.024,-.026,-.028,-0.03,-.032,-.034,-.037,-.04,-.043,-.046,-.049,-.052,-0.055,-.058,-.061,-.064,-.067]
fields8off = (fields8) + np.ones_like(fields8)*0.009
F8 = [21,33,41,47,53,59,65,69,74,78,82,86,94,99,104,109,114,118,122,126,130,134]
plt.plot(fields8off,F8)
plt.title('Fundamental Axial Frequencies vs. Stray Field for 11 ions')
plt.xlabel('Stray Field')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

fields9 = [-.016,-.020,-.023,-.026,-.029,-.032,-.035,-.038,-.041,-.044,-.047,-.050,-.053]
fields9off = (fields9) + np.ones_like(fields9)*0.009
F9 = [34,44,54,62,69,77,82,89,94,99,104,109,113]
plt.plot(fields9off,F9)
plt.title('Fundamental Axial Frequencies vs. Stray Field for 11 ions')
plt.xlabel('Stray Field')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

fields10 = [-.018,-.021,-.024,-.027,-.030,-.033,-.036,-.039]
fields10off = (fields10) + np.ones_like(fields10)*0.009
F10 = [27,44,54,63,70,76,83,89]
plt.plot(fields10off,F10)
plt.title('Fundamental Axial Frequencies vs. Stray Field for 11 ions')
plt.xlabel('Stray Field')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

fields11 = [-.017,-.018,-.021,-.024,-.027,-.032,-.033]
fields11off = (fields11) + np.ones_like(fields11)*0.009
F11 = [16,20,41,51,60,72,75]
plt.plot(fields11off,F11)
plt.title('Fundamental Axial Frequencies vs. Pinning Field')
plt.xlabel('Pinning Field (V/mm)')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-0.120,0,200])

plt.figure()

fields10 = [-16,-17,-18,-19,-20,-22,-24,-26,-28,-30,-32,-34,-36]
fields10off = (fields10) + np.ones_like(fields10)*9
fields10off= fields10off * (2/3.7)
F10low = [18.2,25.3,35.9,38.2,42.9,49.7,55.4,61.1,66.0,70.9,75.6,79.1,83.4]
F10high= [20.7,26.4,36.7,41.2,44.5,51.8,55.7,63.2,68.1,72.8,77.2,81.1,85.2]
F10 = np.add(F10high,F10low)/2
plt.plot(fields10off,F10)
plt.title('Fundamental Axial Frequencies vs. Pinning Field')
plt.xlabel('Pinning Field (mV/mm)')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-120,0,200])

fields4 = [-9,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,-21,-23,-25,-27,-29,-31,-33,-35,-37,-39,-43,-47,-51,-55,-59,-64,-69,-74,-79,-89,-99]
fields4off = (fields4) + np.ones_like(fields4)*9
fields4off= fields4off * (2/3.7)
F4low = [7.4,16,21,26.4,31.1,35.1,39.1,42.8,46.4,49.9,52.9,59.1,64.7,70.1,74.6,79.4,83.5,87.9,92.0,95.7,98.9,105.9,112.4,118.2,123.8,128.9,135.3,141.1,146.7,151.9,161.7,170.8]
F4high= [7.9,18,23.4,28.7,32.9,36.8,40.7,44.3,47.6,50.9,54.1,60.1,65.6,70.0,75.6,80.3,84.6,88.8,93.0,96.4,100.0,106.9,113.3,119.1,124.6,129.8,135.9,141.7,147.3,152.5,162.3,171.3]
F4 = np.add(F4high,F4low)/2
plt.plot(fields4off,F4)
plt.title('Fundamental Axial Frequencies vs. Pinning Field')
plt.xlabel('Pinning Field (mV/mm)')
plt.ylabel('Frequency (kHz)')
plt.axis([0,-40,0,120])


plt.show()
