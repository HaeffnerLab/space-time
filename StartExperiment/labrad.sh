#!/bin/bash

~/LabRAD/scalabrad/scalabrad-0.7.2/bin/labrad --tls-required=false &

~/LabRAD/scalabrad/scalabrad-web-server-1.1.0/bin/labrad-web &

source ~/virtual-envs/labrad-env/bin/activate
python -m labrad.node

