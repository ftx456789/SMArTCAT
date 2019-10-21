from __future__ import print_function
import simuvex
import numbers
from timingModel import TimingModel
import re
import claripy

#maintain the last statement to analyze changes between states
lastStmt = None

#maintain lists of violations:
type1violations = []
type2violations = []
type3violations = []

class SimIRStmt_Time(simuvex.vex.statements.SimIRStmt):
    def _execute(self):
        #executionTime = TimingModel.__dict__[self.stmt.instruction](self) #execution time for this instruction
        timingInfo = TimingModel.timing(self) #execution time for this instruction
        
        #print self.state.se._stored_solver.constraints
        
        executionTime = timingInfo[0]
        #we miss the dependecies from other execution paths, where differences exist due to earlier branches.
        #NOTE: perhaps we should maintain a timing-history for each execution path in the timing plugin, so we can compare these in hindsight
        #thus accept that not all violations can be identified on the fly :)
        if timingInfo[1] != None:
            #self-composition analysis to identify whether the function depends on a secret.
            #we only need to perform the simplest of self-composition analysis: see whether C, C', s!=s', p==p', t!=t' is satisfiable, where t is the just-returned execution time?
            
            #import analysisUtils as u
            #TODO: rather inefficient if we run over all these constraints so often, should probably only do this if the previously known secret can't be found.
            #print self.state.se._stored_solver.constraints
            #for c in self.state.se._stored_solver.constraints:
            #    for var in list(c.variables):
            #        if re.search("secret*",var):
            #            secretString = var
            #also quite inefficient to use stringToVar every time
            #secret = u.stringToVar(secretString,self.state.se._stored_solver.constraints)
            import timeAnalysis
            secret = timeAnalysis.secret
            solver = self.state.se._stored_solver.branch()
            v = claripy.BVS("v", timingInfo[1].length)
            solver.add(v == timingInfo[1])
            #if the value can't even take on two values we can skip self-composition because it will never be satisfiable
            if len(solver.eval(v,2)) == 2:
                import cdset
                cset = cdset.CDSet(solver, secret)
                import SelfComposition
                composition = SelfComposition.SelfComposition(cset)
                
                v0 = composition.symbols[v.args[0]][0]
                v1 = composition.symbols[v.args[0]][1]
                
                composition.publics.equal()
                composition.secrets.unequal()
                composition.connect(v0 != v1)
                
                if composition.satisfiable():
                    if TimingModel.InstType.instructions.__contains__(self.stmt.instruction):
                        if TimingModel.InstType.instructions[self.stmt.instruction] == TimingModel.InstType.BRANCH:
                            print("\033[93mWarning: Type 1 violation at instruction: %s @ 0x%x\033[0m" % (self.stmt.instruction, self.stmt.instructionAddress))
                            global type1violations
                            type1violations.append(self.stmt)
                        elif TimingModel.InstType.instructions[self.stmt.instruction] == TimingModel.InstType.MEMOP:
                            print("\033[93mWarning: Type 2 violation at instruction: %s @ 0x%x\033[0m" % (self.stmt.instruction, self.stmt.instructionAddress))
                            global type2violations
                            type2violations.append(self.stmt)
                            if not (self.state.options.__contains__(simuvex.o.CONSERVATIVE_WRITE_STRATEGY) and self.state.options.__contains__(simuvex.o.CONSERVATIVE_READ_STRATEGY)):
                                print("\033[93mFor better results you should probably run the analysis and with the initial states' options \"add_options={simuvex.o.CONSERVATIVE_WRITE_STRATEGY, simuvex.o.CONSERVATIVE_READ_STRATEGY}\"\033[0m")
                        else:
                            print("\033[93mWarning: violation of unknown type at instruction: %s @ 0x%x\033[0m" % (self.stmt.instruction, self.stmt.instructionAddress))
                    else:
                        print("\033[93mWarning: violation of unknown type at instruction: %s @ 0x%x\033[0m" % (self.stmt.instruction, self.stmt.instructionAddress))
                    #TODO: add warnings to a list of warnings for latter inspection
                else:
                    #make branching constant average time
                    #executionTime = (solver.min(executionTime) + solver.max(executionTime)) / 2
                    #make branching constant minimum time
                    executionTime = solver.min(executionTime)
            else:
                #executionTime = (solver.min(executionTime) + solver.max(executionTime)) / 2
                executionTime = solver.min(executionTime)
            
        #if isinstance(executionTime, numbers.Integral):
            
            #actually, the depending variable isn't (always) contained in the execution time symbolic expression. (atleast in the scenario of branches, time depends on branch prediction failures)
            #would be best if the timemodel somehow returned the depending variable(s) v so we can perform self-composition over that variable.
            
        
        self.state.time.countTime(executionTime) #cumulative execution time in this state
        
        
        #if len(self.state.se.constraints) > 0:
        #    print self.state.se.constraints[0]
        
        #all debugging code:
        global lastStmt
        
        targets = set([3221225849])
        
        #if lastStmt is not None:
        #    changes = self.state.memory.changed_bytes(lastStmt.state.memory)
        #    if len(changes) != 0:
        #        print "memory changes: %s" % changes
        #        if len(changes.intersection(targets)) > 0:
        #            print "XXXXXXXXXXXXXXXXXX changed memory location: %s XXXXXXXXXXXXXXXXXX" % changes.intersection(targets)
            
        
        lastStmt = self
        print("-- Processed %s, total execution time in this path, so far: %d --" % (self.stmt.instruction, self.state.se.any_int(self.state.time.totalExecutionTime)))
        #print "rbp: 0x%x" % self.state.se.any_int(self.state.regs.rbp)
        #self.irsb.pp()
        """
        if self.state.se.any_int(self.state.time.totalExecutionTime) == 152 or self.state.se.any_int(self.state.time.totalExecutionTime) == 160 or self.state.se.any_int(self.state.time.totalExecutionTime) == 164:
            self.irsb.pp()
            #b not available (of course), lets first try to get to a factory or project from the stmt
            #print "- start of capstone for T=152 -"
            #print self.stmt
            #self.state.meta.factory.block(self.stmt.addr+self.stmt.delta).capstone
            #print "- end of capstone for T=152 -"
        """