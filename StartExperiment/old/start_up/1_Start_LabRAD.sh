#!/bin/bash

/home/space-time/LabRAD/scalabrad-0.7.2/bin/labrad --tls-required=false &
/home/space-time/LabRAD/scalabrad-web-server-1.1.0/bin/labrad-web &

source virtualenvwrapper.sh

workon 'labrad'

python -m labrad.node --tls=off &

#source virtualenvwrapper.sh
#workon labrad
#labon=$(ps aux | grep LabRAD-v1.1.3.exe | wc -l)
#if [ $labon = 2 ]
#    then
#    echo $labon
#    exit 
#fi
#wine /home/space-time/LabRAD/common/LabRAD-v1.1.3.exe &
 