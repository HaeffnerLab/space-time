#!/bin/bash

source virtualenvwrapper.sh 
workon 'labrad'

# start all servers
cd /home/space-time/LabRAD/space_time/Node
python NodeClient-spacetime.py


