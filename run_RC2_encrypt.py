from __future__ import print_function
#run_RC2_encrypt
#                     void RC2_encrypt(unsigned long *d, RC2_KEY *key)

import settings
import claripy
settings.WARNING_ADDRESS = 0x50df58
settings.WARNING_MOMENT = settings.WARNING_BEFORE
settings.VERBOSE = True#False
settings.TARGET_ADDRESS = 0x50DF20
settings.TARGET_FUNCTION = "RC2_encrypt"
settings.TARGET_BINARY = "/home/roeland/Documents/opensslARM/bin/lib/libcrypto.so.1.1"

settings.dataBuf = 100000
#settings.data = claripy.BVS('data', 1024)
data = [claripy.BVS('data(0)', 8)]

settings.data = data[0]
i = 8
while(i<1024):
    Ndata = claripy.BVS('data(%d)'%i, 8)
    data.append(Ndata)
    i += 8
    settings.data = settings.data.concat(Ndata)
    
settings.keyBuf = 110000
#settings.key = claripy.BVS("key", 1024)

key = [claripy.BVS('key(0)', 8)]
i = 8
settings.key = key[0]
while(i<1024):
    Nkey = claripy.BVS('key(%d)'%i, 8)
    key.append(Nkey)
    i += 8
    settings.key = settings.key.concat(Nkey)

settings.params = [settings.dataBuf, settings.keyBuf]

settings.secret = settings.key.concat(settings.data)
from pluginTime import TIME_STRATEGY_SHORTEST_IF_NONSECRET
TIME_STRATEGY = TIME_STRATEGY_SHORTEST_IF_NONSECRET

from pipelineModel import LATENCY_STRATEGY_SHORTEST_IF_NONSECRET
settings.LATENCY_STRATEGY = LATENCY_STRATEGY_SHORTEST_IF_NONSECRET

def stateInit(startState):
    """stateInit is called before symbolic execution starts. Override it to initialize the starting state."""
    print("state initialized")
    #startState.memory.store(settings.keyBuf, settings.key, 1024)
    #startState.memory.store(settings.dataBuf, settings.data, 1024)
    i = 0;
    while(i<1024/8):
        startState.memory.store(settings.dataBuf+i, data[i], 1)
        startState.memory.store(settings.keyBuf+i, key[i], 1)
        i += 1
    return True


settings.stateInit = stateInit

import tool