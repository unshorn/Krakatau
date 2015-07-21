import collections

from .base import BaseJump
from .goto import Goto
from ..constraints import IntConstraint

class Switch(BaseJump):
    def __init__(self, parent, default, table, arguments):
        super(Switch, self).__init__(parent, arguments)

        #get ordered successors since our map will be unordered. Default is always first successor
        if not table:
            ordered = [default]
        else:
            tset = set()
            ordered = [x for x in (default,) + zip(*table)[1] if not x in tset and not tset.add(x)]

        self.successors = ordered
        reverse = collections.defaultdict(set)
        for k,v in table:
            if v != default:
                reverse[v].add(k)
        self.reverse = dict(reverse)

    def getNormalSuccessors(self):
        return self.successors

    def replaceBlocks(self, blockDict):
        self.successors = [blockDict.get(key,key) for key in self.successors]
        self.reverse = {blockDict.get(k,k):v for k,v in self.reverse.items()}

    def reduceSuccessors(self, pairsToRemove):
        temp = list(self.successors)
        for (child, t) in pairsToRemove:
            temp.remove(child)

        if len(temp) == 0:
            return None
        elif len(temp) == 1:
            return Goto(self.parent, temp.pop())
        elif len(temp) < len(self.successors):
            self.successors = temp
            self.reverse = {v:self.reverse[v] for v in temp[1:]}
        return self

    ###############################################################################
    def constrainJumps(self, x):
        impossible = []
        for child in self.successors:
            func = self.getSuccessorConstraints((child,False))
            results = func(x)
            if results[0] is None:
                impossible.append((child,False))
        return self.reduceSuccessors(impossible)

    def getSuccessorConstraints(self, (block, t)):
        cmin, cmax = -1<<31, (1<<31)-1
        if block in self.reverse:
            cmin = min(self.reverse[block])
            cmax = max(self.reverse[block])

        def propagateConstraints(x):
            if x is None:
                return None,
            return IntConstraint.range(x.width, max(cmin, x.min), min(cmax, x.max)),
        return propagateConstraints
