"""
### BEGIN NODE INFO
[info]
name = WikiServer
version = 1.0
description = 
instancename = WikiServer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import os
from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

class WikiServer(LabradServer):
    """
    WikiServer for pushing data to wiki
    """
    name = 'WikiServer'

    @setting(21, 'Update Wiki')
    def update_wiki(self, c):
        savedir = '/home/space-time/'
        data = 'Home.md'
        yield os.system("cp " + savedir + data + " /home/space-time/TestWiki2/wiki/" + data)
        yield os.system("bash /home/space-time/TestWiki2/updatewiki.sh")


if __name__ == "__main__":
    from labrad import util
    util.runServer(WikiServer())
