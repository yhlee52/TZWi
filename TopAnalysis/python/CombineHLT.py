import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import os
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

import json

class CombineHLT(Module, object):
    def __init__(self, *args, **kwargs):
        #super(CombineHLT, self).__init__(*args, **kwargs)
        self.outName = kwargs.get("outName") if "outName" in kwargs else "HLT"

        if "/CombineHLTCppWorker_cc.so" not in  ROOT.gSystem.GetLibraries():
            print "Load C++ CombineHLT worker module"
            base = os.getenv("NANOAODTOOLS_BASE")
            if base:
                ROOT.gROOT.ProcessLine(".L %s/src/CombineHLTCppWorker.cc+O" % base)
            else:
                base = "%s/src/TZWi/TopAnalysis"%os.getenv("CMSSW_BASE")
                ROOT.gSystem.Load("libPhysicsToolsNanoAODTools.so")
                ROOT.gSystem.Load("libTZWiTopAnalysis.so")
                ROOT.gROOT.ProcessLine(".L %s/interface/CombineHLTCppWorker.h" % base)

        fName, setName = kwargs.get("hltSet").split('.')
        base = "%s/src/TZWi/TopAnalysis"%os.getenv("CMSSW_BASE")
        d = json.loads(open(base+"/data/combineHLT/"+fName+".json").read())

        formula = d[setName]
        oprs = ["(", ")", "||", "&&"]
        for opr in oprs: formula = formula.replace(opr, " %s " % opr)
        formula = formula.strip()

        self.names = []
        self.shortFormula = []
        for tok in formula.split():
            if tok in oprs:
                self.shortFormula.append(tok)
                continue
            
            idx = -1
            if tok in self.names:
                idx = self.names.index(tok)
            else:
                idx = len(self.names)
                self.names.append(tok)
            self.shortFormula.append("[%d]" % idx)
        self.shortFormula = ''.join(self.shortFormula)

        pass
    def beginJob(self):
        self.worker = ROOT.CombineHLTCppWorker(str(self.shortFormula), self.outName)
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch(self.outName, "O")
        self.initReaders(inputTree)
        pass
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def initReaders(self,tree):
        for i, name in enumerate(self.names):
            setattr(self, "b_"+name, tree.valueReader(name))
            self.worker.addHLT(getattr(self, "b_"+name))

        self._ttreereaderversion = tree._ttreereaderversion

        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        if event._tree._ttreereaderversion > self._ttreereaderversion:
            self.initReaders(event._tree)

        res = self.worker.analyze()
        self.out.fillBranch(self.outName, res)

        return res
