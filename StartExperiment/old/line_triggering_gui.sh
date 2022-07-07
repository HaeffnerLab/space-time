#!/bin/bash
source virtualenvwrapper.sh 
workon 'labrad'

cd /home/space-time/LabRAD/common/clients
python LINETRIGGER_CONTROL.py
