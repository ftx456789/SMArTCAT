from __future__ import print_function
import logging
l = logging.getLogger("simuvex.plugins.time")

import claripy

from simuvex.plugins.plugin import SimStatePlugin

class PluginTome(SimStatePlugin):
    """
    Plugin to keep track of asm instruction's execution progress / dependencies / etc
    DEPRECATED
    """
    def __init__(self, tome=None):
        SimStatePlugin.__init__(self)

        # info on the current asm instruction
        self.mnemonic = None                #asm instruction mnemonic
        self.instruction = None             #entire asm instruction
        self.address = None                 #instruction address
        self.registerDependencies = []      #registers and memory this instruction depends on
        self.memoryDependencies = []        #registers and memory this instruction depends on
        self.firstPutAnalyzedFlag = False   #whether the first put vex-instruction was already processed for this asm-instruction
        self.issueTime = None         #this instruction's issuing time

        if tome is not None:
            self.mnemonic = tome.mnemonic
            self.instruction = tome.instruction
            self.address = tome.address
            self.registerDependencies = tome.registerDependencies
            self.memoryDependencies = tome.memoryDependencies
            self.firstPutAnalyzedFlag = tome.firstPutAnalyzedFlag
            self.issueTime = tome.issueTime
            
    def copy(self):
        return PluginTome(tome=self)

    def merge(self, others, merge_conditions, common_ancestor=None):
		#TODO
        print("unimplemented merge of pluginTome")
        return False

    def widen(self, others):
        return False

    def clear(self):
        s = self.state
        self.__init__()
        self.state = s

PluginTome.register_default('tome', PluginTome)