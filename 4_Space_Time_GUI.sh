#!/bin/bash
source virtualenvwrapper.sh
workon 'labrad'
PYTHONPATH=/home/space-time/LabRAD
echo $PYTHONPATH
cd /home/space-time/LabRAD/space-time/clients/
python Space_Time_GUI.py

