#!/bin/bash
source virtualenvwrapper.sh 
workon 'labrad'
cd /home/space-time/LabRAD/space_time/Node
python NodeClient-spacetime.py
cd /home/space-time/LabRAD/common/abstractdevices/script_scanner
python script_scanner.py
