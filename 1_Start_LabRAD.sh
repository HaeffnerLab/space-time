#!/bin/bash
source virtualenvwrapper.sh
workon labrad
labon=$(ps aux | grep LabRAD-v1.1.3.exe | wc -l)
if [ $labon = 2 ]
    then
    echo $labon
    exit 
fi
wine /home/space-time/LabRAD/common/LabRAD-v1.1.3.exe &
