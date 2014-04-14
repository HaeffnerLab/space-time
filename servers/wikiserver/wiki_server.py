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
import sys
import labrad
from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from pylab import *

class WikiServer(LabradServer):
    """
    WikiServer for pushing data to wiki
    """
    name = 'WikiServer'
    
    @inlineCallbacks
    def initServer(self):
        yield self.client.registry.cd(['','Servers', 'wikiserver'])
        self.maindir = yield self.client.registry.get('wikipath')
        self.maindir = self.maindir[0] + '/'

    @setting(21, 'Update Wiki', sourcefile='s', destinationfile='s', returns='')
    def update_wiki(self, c, sourcefile, destinationfile):
        yield os.system("cp " + self.datadir + sourcefile + " " + self.maindir + self.wikidir + destinationfile)
        yield os.chdir(self.maindir)
        print os.getcwd()
        yield os.system("bash updatewiki.sh")
        
    @setting(22, 'Add wiki directory', wikidir='s',returns='')    
    def set_wiki_dir(self, c, wikidir):
        self.wikidir = wikidir + '/'
     
    @setting(23, 'Add data directory', datadir='s',returns='')    
    def set_data_dir(self, c, datadir):
        self.datadir = datadir + '/'
        
    @setting(24, 'Plot data for wiki', data)
    def plot_wiki(self, c):
        self.plot = plotdataforwiki(data)
        show()

if __name__ == "__main__":
    from labrad import util
    util.runServer(WikiServer())
