#!/bin/bash



/home/space-time/LabRAD/scalabrad-0.7.2/bin/labrad --tls-required=false &

~/LabRAD/scalabrad-web-server-1.1.0/bin/labrad-web &

source virtualenvwrapper.sh 
workon 'labrad'

# start node server
python -m labrad.node

