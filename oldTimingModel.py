from __future__ import print_function
import claripy
solver = claripy.Solver()

# the branchPredictionSwitch is used to model timing differences caused by branchPredictionFails.
# note these may be hard to exploit, so by setting the switch to 0 the time caused by branch prediction fails is always set to 1.
# by not setting the switch statement maximum timing differences can be computed.
# we only do this if the branch prediction depends on a secret value by further analyzing this in the calling timeExecution.SimIRStmt_Time
#   if the time depends only on a public value we average the value (is this the best prediction strategy? minimum time is probably better in loops)
#this is hacked as a BVS 1 bit number, because booleans don't really want to work with us
branchPredictionSwitch = claripy.BVS("branchPredictionSwitch",1)

#similar to branchPredictionSwitch but for cache miss based attacks
cacheMissSwitch = claripy.BVS("cacheMissSwitch",1)

unmodeledInstructions = set()

#TODO: return the symbol on which the timing depends along with the timing.
#currently return just timing, change that to a tuple ? alternatively: add an extra function
class TimingModel(object):
    """
    The TimingModel contains function which describe timing behavior for instructions.
    should call static timing() for timing info
    
    functions return a tuple of (time, *dependence)
    time is either an int or a symbolic expression.
    *dependence is a list of variables on which the timing depends, or None
    """
    
    #we use a generic timing depending on the instruction type.
    #0: default, standard instruction
    #1: branch (depending on secret or nah?)
    #2: memory load (not necessarily depending on secret)
    #3: floating point instruction
    class InstType(object):
        DEFAULT = 0
        BRANCH = 1  #conditional branches only? TODO: what to do with branches to dynamic addresses
        MEMOP = 2
        FLOATOP = 3
        instructions = {
        "ble": BRANCH, "bgt": BRANCH, "beq": BRANCH,
        "ldr": MEMOP, "str": MEMOP}
    
    @staticmethod
    def timing(simStmt):
        """
        generic function to return timing for any instruction
        """
        if TimingModel.__dict__.__contains__(simStmt.stmt.instruction):
            #there is a specific function for the given instruction
            return TimingModel.__dict__[simStmt.stmt.instruction](simStmt)
        else:
            #determine instruction type
        
            
            #NOTE: take into account conditional execution as well?
            
            InstType = TimingModel.InstType
            
            if InstType.instructions.__contains__(simStmt.stmt.instruction):
                timingType = InstType.instructions[simStmt.stmt.instruction]
            else:
                timingType = InstType.DEFAULT
                
                
            if timingType == InstType.DEFAULT:
                unmodeledInstructions.add(simStmt.stmt.instruction)
                return (2, None)
            elif timingType == InstType.BRANCH:
                #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! conditional branch !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                #print "depends on", simStmt.stmt.keyStatement
                #debugging code to access the stmt from the editor:
                #global keyStmt
                #keyStmt = simStmt.stmt.keyStatement
                #print "offset: ", simStmt.stmt.keyStatement.offset
                #print "AKA: ", simStmt.stmt.keyStatement.arch.translate_register_name(simStmt.stmt.keyStatement.offset, simStmt.stmt.keyStatement.data.result_size/8)
                data = "%s" % simStmt.stmt.keyStatement.expressions[0]
                #print "depends on data: ", data
                if data[:1] == 't':
                    dependence = simStmt.state.scratch.tmp_expr(simStmt.stmt.keyStatement.expressions[0].tmp)
                    #print "concrete: ", concrete
                    #print "^^^ conditional branch ^^^"
                    #return (1, simStmt.state.scratch.tmp_expr(int(data[1:])))
                    branchUniqueSwitch = claripy.BVS("branchUniqueSwitch",1)
                    branchUniqueDependence = claripy.BVS("branchUniqueDependence",dependence.length)
                    return (claripy.If(claripy.And(branchPredictionSwitch==1, branchUniqueSwitch==1, dependence==branchUniqueDependence), claripy.BVV(5,32), claripy.BVV(1,32)), dependence)
                else:
                    #assume a branch failure takes 5 cycles to recover from.
                    print("^^^ conditional branch ^^^")
                    return (5, None)
            elif timingType == InstType.MEMOP:
                print("memory operation")
                return (2, None)
            elif timingType == InstType.FLOATOP:
                print("floating point instruction")
                #if denormal:
                return (100, None)
            else:
                print("unimplemented timing for instruction: " % simStmt.stmt.instruction)
                return (0, None)
            
    def str(simStmt):
        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! store statement !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        #print "depends on", simStmt.stmt.keyStatement
        #debugging code to access the stmt from the editor:
        #global stmt
        #stmt = simStmt
        #global keyStmt
        #keyStmt = simStmt.stmt.keyStatement
        storesAt = "%s" % simStmt.stmt.keyStatement.expressions[0]
        #data = "%s" % simStmt.stmt.keyStatement.expressions[1]
        #print "depends on data: ", data
        #print "store at: ", storesAt
        if storesAt[:1] == 't':
            storeLocation = simStmt.state.scratch.tmp_expr(simStmt.stmt.keyStatement.expressions[0].tmp)
            #global store
            #store = simStmt.state.scratch.tmp_expr(simStmt.stmt.keyStatement.expressions[0].tmp)
            #print "^^^ store statement ^^^"
            cacheUniqueSwitch = claripy.BVS("cacheUniqueSwitch",1)
            cacheUniqueDependence = claripy.BVS("cacheUniqueDependence",storeLocation.length)
            return (claripy.If(claripy.And(cacheMissSwitch==1, cacheUniqueSwitch==1,storeLocation==cacheUniqueDependence), claripy.BVV(20,32), claripy.BVV(2,32)), storeLocation)
        #here, we may actually want to make a difference between cache hits and misses independent of secret variables, but this may still cause a large difference if an earlier branch does depend on a secret:
        return (2, None)
        
    def ldr(simStmt):
        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! load statement !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        #print "depends on", simStmt.stmt.keyStatement
        #debugging code to access the stmt from the editor:
        #global stmt
        #stmt = simStmt
        #global keyStmt
        #keyStmt = simStmt.stmt.keyStatement
        loadsFrom = "%s" % simStmt.stmt.keyStatement.expressions[0].addr
        #print loadsFrom
        #data = "%s" % simStmt.stmt.keyStatement.expressions[1]
        #print "load from: ", loadsFrom
        if loadsFrom[:1] == 't':
            loadLocation = simStmt.state.scratch.tmp_expr(simStmt.stmt.keyStatement.expressions[0].addr.tmp)
            #print "^^^ store statement ^^^"
            cacheUniqueSwitch = claripy.BVS("cacheUniqueSwitch",1)
            cacheUniqueDependence = claripy.BVS("cacheUniqueDependence",loadLocation.length)
            return (claripy.If(claripy.And(cacheMissSwitch==1, cacheUniqueSwitch==1,loadLocation==cacheUniqueDependence), claripy.BVV(20,32), claripy.BVV(2,32)), loadLocation)
        #here, we may actually want to make a difference between cache hits and misses independent of secret variables, but this may still cause a large difference if an earlier branch does depend on a secret:
        return (2, None)
    
    """
    def mov_w(simStmt):
        return (4, None)
        
    def pop(simStmt):
        return (4, None)
        
    def mov(simStmt):
        print "depends on", simStmt.stmt.keyStatement
        print "offset: ", simStmt.stmt.keyStatement.offset
        print "AKA: ", simStmt.stmt.keyStatement.arch.translate_register_name(simStmt.stmt.keyStatement.offset, simStmt.stmt.keyStatement.data.result_size/8)
        data = "%s" % simStmt.stmt.keyStatement.data
        print "data: ", data
        #TODO: fix this very hacky solution
        result = 4
        if data[:1] == 't':
            dataExpr = simStmt.state.scratch.tmp_expr(int(data[1:]))
            #print "data expression:", dataExpr
            concrete = simStmt.state.se.any_n_int(simStmt.state.scratch.tmp_expr(int(data[1:])),10)
            print "concrete: ", concrete
            #result = claripy.If(dataExpr < 10, claripy.BVV(1,32), claripy.BVV(2,32))
        #return result
        return (5, None)
        
    def movzx(simStmt):
        print "depends on", simStmt.stmt.keyStatement
        print "offset: ", simStmt.stmt.keyStatement.offset
        print "AKA: ", simStmt.stmt.keyStatement.arch.translate_register_name(simStmt.stmt.keyStatement.offset, simStmt.stmt.keyStatement.data.result_size/8)
        data = "%s" % simStmt.stmt.keyStatement.data
        print "data: ", data
        #TODO: fix this very hacky solution
        if data[:1] == 't':
            #print "data expression:", simStmt.state.scratch.tmp_expr(int(data[1:]))
            concrete = simStmt.state.se.any_n_int(simStmt.state.scratch.tmp_expr(int(data[1:])),10)
            print "concrete: ", concrete
        return (4, None)
        
    def add(simStmt):
        return (4, None)
        
    def jmp(simStmt):
        print "depends on", simStmt.stmt.keyStatement
        print "offset: ", simStmt.stmt.keyStatement.offset
        print "AKA: ", simStmt.stmt.keyStatement.arch.translate_register_name(simStmt.stmt.keyStatement.offset, simStmt.stmt.keyStatement.data.result_size/8)
        data = "%s" % simStmt.stmt.keyStatement.data
        print "data: ", data
        #TODO: fix this very hacky solution
        if data[:1] == 't':
            #print "data expression:", simStmt.state.scratch.tmp_expr(int(data[1:]))
            concrete = simStmt.state.se.any_n_int(simStmt.state.scratch.tmp_expr(int(data[1:])),10)
            print "concrete: ", concrete
            print "HERE"
            return (1, simStmt.state.scratch.tmp_expr(int(data[1:])))
        else:
            return (1, None)
        
    def movSTle(simStmt):
        print "depends on", simStmt.stmt.keyStatement
        print "address: ", simStmt.stmt.keyStatement.addr
        data = "%s" % simStmt.stmt.keyStatement.data
        print "data: ", data
        #TODO: fix this very hacky solution
        if data[:1] == 't':
            #print "data expression:", simStmt.state.scratch.tmp_expr(int(data[1:]))
            concrete = simStmt.state.se.any_n_int(simStmt.state.scratch.tmp_expr(int(data[1:])),10)
            print "concrete: ", concrete
        d2 = simStmt._translate_expr(simStmt.stmt.keyStatement.data)
        expr = d2.expr.to_bv()
        #print "expr: %s" % expr
        return (2, None)
    """