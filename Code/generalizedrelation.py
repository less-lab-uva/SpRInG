import neighbors as nutils

class GeneralizedImplicationRelation:
    def __init__(self, generalform, relationA, relationB, all_nodes):
        self.__generalformA, self.__generalformB = generalform[0], generalform[1]
        self.__leftOp = relationA.getOp()
        self.__rightOp = relationB.getOp()
        self.__leftVal = relationA.getRTerm()
        self.__rightVal = relationB.getRTerm()
        self.__leftType = relationA.getType()
        self.__rightType = relationB.getType()
        self.__implications = []
        self.__leftRelations = []
        self.__rightRelations = []
        self.__delta1s = {}
        self.__delta2s = {}
        self.__delta1fail = {}
        self.__delta2fail = {}
        self.__contradictions = {}
        self.__tautologyLeft = {}
        self.__tautologyRight = {}
        self.__leftConst = {}
        self.__rightConst = {}
        self.__reason = None
        self.__string = ""
        self.__all_nodes = all_nodes

    def getLeftType(self):
        return self.__leftType

    def getRightType(self):
        return self.__rightType

    def getImplications(self):
        return self.__implications

    def getLeftVal(self):
        return self.__leftVal

    def getRightVal(self):
        return self.__rightVal

    def getGenFormA(self):
        return self.__generalformA

    def getGenFormB(self):
        return self.__generalformB

    def getString(self):
        return self.__string

    def getLeftOp(self):
        return self.__leftOp

    def getRightOp(self):
        return self.__rightOp

    def getLeftConst(self):
        return self.__leftConst

    def getRightConst(self):
        return self.__rightConst

    def setReason(self, reason):
        self.__reason = reason

    def getReason(self):
        return self.__reason

    def getContradictions(self):
        return self.__contradictions

    def getTautLeft(self):
        return self.__tautologyLeft

    def getTautRight(self):
        return self.__tautologyRight


    def includeImplication(self, implication):
        leftRelation = implication.getLeftRelation()
        rightRelation = implication.getRightRelation()

        # keep track of all implications that are of this generalized form
        if implication not in self.__implications:
            self.__implications.append(implication)
        if leftRelation not in self.__leftRelations:
            self.__leftRelations.append(leftRelation)
        if rightRelation not in self.__rightRelations:
            self.__rightRelations.append(rightRelation)

        # keep track of their delta scores, contradictions, and tautologies
        self.__delta1s[(leftRelation.getString(), rightRelation.getString())] = implication.getDelta1()
        self.__delta2s[(leftRelation.getString(), rightRelation.getString())] = implication.getDelta2()

        if implication.getContradiction() == True:
            self.__contradictions[(leftRelation.getGenForm(), rightRelation.getGenForm())] = implication.getContradictionTimesteps()
        if implication.getTautologyLeft() == True:
            self.__tautologyLeft[(leftRelation.getString(), rightRelation.getString())] = True
        if implication.getTautologyRight() == True:
            self.__tautologyRight[(leftRelation.getString(), rightRelation.getString())] = True

        if leftRelation.getType() == 'rh_const' and leftRelation.getOp() != '==':
            self.__leftConst[(leftRelation.getString(), rightRelation.getString())] = leftRelation.getRTerm()

        if rightRelation.getType() == 'rh_const' and rightRelation.getOp() != '==':
            self.__rightConst[(leftRelation.getString(), rightRelation.getString())] = rightRelation.getRTerm()

    def evalDelta1(self, delta1, thresh):
        num_failed = 0
        for implication in self.__delta1s:
            if self.__delta1s[implication] < delta1:
                self.__delta1fail[implication] = self.__delta1s[implication]
                #del self.__leftConst(implication)
                #del self.__rightConst(implication)
                num_failed += 1
        if num_failed / len(self.__delta1s) > thresh:
            return False
        else:
            return True

    def evalDelta2(self, delta2, thresh):
        num_failed = 0
        for implication in self.__delta2s:
            if self.__delta2s[implication] < delta2:
                self.__delta2fail[implication] = self.__delta2s[implication]
                #del self.__leftConst(implication)
                #del self.__rightConst(implication)
                num_failed += 1
        if num_failed / len(self.__delta2s) > thresh:
            return False
        else:
            return True

    def evalTautLeft(self, thresh):
        if len(self.__tautologyLeft) / len(self.__leftRelations) > thresh:
            return False
        else:
            return True

    def evalTautRight(self, thresh):
        if len(self.__tautologyRight) / len(self.__rightRelations) > thresh:
            return False
        else:
            return True

    def getDelta1Fail(self):
        return self.__delta1fail

    def getDelta2Fail(self):
        return self.__delta2fail

    def eval(self, thresh, thresh2):
        s1 = self.__generalformA
        s2 = self.__generalformB

        if len(self.__contradictions) > 0:
            self.__reason = 'contradict'

        if self.__reason == None:
            if self.__leftConst != {}:
                vals = list(self.__leftConst.values())
                if self.__leftOp == '>=':
                    final = str(min(vals))
                elif self.__leftOp == '<=':
                    final = str(max(vals))
                s1 = s1.replace("CONST", final)
                self.__leftVal = final

            if self.__rightConst != {}:
                vals = list(self.__rightConst.values())
                if self.__rightOp == '>=':
                    final = str(min(vals))
                elif self.__rightOp == '<=':
                    final = str(max(vals))
                s2 = s2.replace("CONST", final)
                self.__rightVal = final

            s = s1 + " implies " + s2
            self.__string = s
            return True

        else:
            s = s1 + " implies " + s2
            self.__string = s
            return False
