import neighbors as nutils

class ImplicationRelation:
    # this initialization should fully initialize the relation with the given node(s)
    # g_nodes contains all of the graph's information on some node (or a pair of nodes)
    def __init__(self, relationA, relationB):
        self.__relationA = relationA
        self.__relationB = relationB

        self.__a_evals = list(relationA.getAllEvals().values())
        self.__b_evals = list(relationB.getAllEvals().values())
        self.__a_true = 0
        self.__a_false = 0
        self.__b_true = 0
        self.__b_false = 0
        self.__both_true = 0
        self.__both_false = 0
        self.__contradict_timesteps = []
        self.__contradiction = False

        self.__delta1_fail = False
        self.__delta2_fail = False
        self.computeEvals()
        self.__tautologyLeft = self.__a_true == 0
        self.__tautologyRight = self.__b_false == 0

        self.__delta1 = self.__both_true / (self.__b_true + 0.0001)
        self.__delta2 = self.__both_false / (self.__a_false + 0.0001)
        self.__string = relationA.getString() + " implies " + relationB.getString()
        self.__generalForm = ''

    def computeEvals(self):
        for timestep, (a_eval, b_eval) in enumerate(zip(self.__a_evals, self.__b_evals)):
            if a_eval == 1:
                self.__a_true += 1
            else:
                self.__a_false += 1

            if b_eval == 1:
                self.__b_true += 1
            else:
                self.__b_false += 1

            if a_eval == 1 and b_eval == -1:
                self.__contradict_timesteps.append(timestep)
                self.__contradiction = True

            if a_eval == 1 and b_eval == 1:
                self.__both_true += 1
            elif a_eval == -1 and b_eval == -1:
                self.__both_false += 1


    def getString(self):
        return self.__string

    def getLeftRelation(self):
        return self.__relationA

    def getRightRelation(self):
        return self.__relationB

    def retGenForm(self):
        return self.__generalForm

    def getGeneralForm(self, grouping):
        self.__generalForm = self.__relationA.getGeneralForm(grouping), self.__relationB.getGeneralForm(grouping)
        return self.__generalForm

    def getDelta1(self):
        return self.__delta1

    def getDelta2(self):
        return self.__delta2

    def getContradiction(self):
        return self.__contradiction

    def getTautologyLeft(self):
        return self.__tautologyLeft

    def getTautologyRight(self):
        return self.__tautologyRight

    def getContradictionTimesteps(self):
        return self.__contradict_timesteps
