#!/bin/bash
source virtualenvwrapper.sh
workon 'labrad'
cd /home/space-time/LabRAD/common/abstractdevices/script_scanner/
python script_scanner.py
cd /home/space-time/LabRAD/common/clients/script_scanner_gui/
python script_scanner_gui.py 