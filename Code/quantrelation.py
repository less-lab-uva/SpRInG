import copy
import neighbors as nutils

class QuantRelation:
    # this initialization should fully initialize the relation with the given node(s)
    # g_nodes contains all of the graph's information on some node (or a pair of nodes)
    def __init__(self, template, g_nodes, count, graph, l_term = "", op = "", r_term = "", ts = 9999):
        self.__template = template
        self.__nodes = g_nodes
        self.__type = template['type']

        self.__membersString = template['members'].replace("NODE1", g_nodes[0]['name'])
        self.__members = eval(eval(self.__membersString))

        self.__l_term = template['property']['l_term']
        self.__r_term = template['property']['r_term']
        self.__op = template['property']['op']

        self.__ID = "INV_" + str(count)
        self.__token = template['alias']
        self.__passed = 0
        self.__failed = 0
        self.__absent = 0
        self.__consec_absent = 0
        self.__uncertain = 0
        self.__string = self.__type + "(" + self.__membersString +  ", '" + template['alias'] + "', " + '"' + self.__l_term + " " + self.__op + " " + str(self.__r_term) + '", graph)'

        self.__entityinfo = self.setEntityInfo()
        self.__evals = {}
        self.__child = False
        self.__generalForm = ""
        self.__isParent = False
        self.__ts = ts

    def isParent(self):
        return self.__isParent


    def initChild(self, graph, timestep, count, tautmodel):
        self.__isParent == True

        new_relation = QuantRelation(self.__template, self.__nodes, count, graph, self.__l_term, self.__op, eval(self.__l_term.replace(self.__token, self.__nodes[0]['name'])), self.__ts)
        new_relation.setChild()

        parent_evals = self.getAllEvals()
        if self.__op == '==':
            for ev in parent_evals:
                if parent_evals[ev] == -1:
                    new_relation.setEval(ev, -1)
                elif parent_evals[ev] == 1:
                    new_relation.setEval(ev, -1)
                else:
                    new_relation.setEval(ev, 0)
        else:
            for ev in parent_evals:
                if parent_evals[ev] == -1:
                    new_relation.setEval(ev, 1)
                elif parent_evals[ev] == 1:
                    new_relation.setEval(ev, 1)
                else:
                    new_relation.setEval(ev, 0)
        new_relation.setEval(timestep, 1)
        new_relation.setTerms(graph, tautmodel)
        return new_relation

    def evaluate(self, graph, tautmodel):
        if self.__type == 'forall': # check 'forall'
            for m in self.__members:
                if not eval(self.__l_term.replace(self.__token, m) + " " + self.__op + " " + str(self.__r_term)):
                    return False
            return True
        else: # check 'exists'
            for m in self.__members:
                if eval(self.__l_term.replace(self.__token, m) + " " + self.__op + " " + str(self.__r_term)):
                    return True
            return False

        
    def getToken(self):
        return self.__token

    def getMembers(self):
        return self.__members

    def setRTerm(self, val):
        self.__r_term = val
        self.setString()
    def setChild(self):
        self.__child = True
    def getChild(self):
        return self.__child
    def getNodeNames(self):
        names = []
        for node in self.__nodes:
            names.append(node['name'])
        return(names)

    def getGeneralForm(self, grouping = "class"):
        self.__generalForm = self.__string.replace(self.__nodes[0]['name'], self.__nodes[0][grouping])
        return self.__generalForm

    def getGenForm(self):
        return self.__generalForm

    def getTS(self):
        return self.__ts

    def setTerms(self, graph, tautmodel):
        self.__r_term = eval(self.__template['property']["l_term"].replace(self.__token, self.__nodes[0]['name']))
        self.setString()


    def setEntityInfo(self):
        entity_info = {'class':{}}
        for group in list(entity_info.keys()):
            entity_info[group][self.__nodes[0]['name']] = self.__nodes[0][group]
            if self.__type == 'two_nodes':
                entity_info[group][self.__nodes[1]['name']] = self.__nodes[1][group]
        return entity_info

    def setString(self):
        self.__string = self.__type + "(" + self.__membersString +  ", '" + self.__token + "', " + '"' + self.__l_term + " " + self.__op + " " + str(self.__r_term) + '", graph)'

    def setEval(self, timestep, val):
        # if passed or uncertain:
        if val == 1 or val == 0:
            self.__evals[timestep] = 1
            self.__passed += 1
            self.__consec_absent = 0
        # if failed
        elif val == -1:
            self.__evals[timestep] = -1
            self.__failed += 1
            self.__consec_absent = 0
        # if absent
        else:
            pass
            '''
            self.__evals[timestep] = 0
            self.__absent += 1
            self.__consec_absent += 1
            if self.__absent > athresh or self.__consec_absent > acthresh:
                print("failed")
                exit(0)
                self.__failed += 1
            '''

    def getNodes(self):
        return self.__nodes

    def getID(self):
        return self.__ID

    def getLTerm(self):
        return self.__l_term

    def getOp(self):
        return self.__op

    def getRTerm(self):
        return self.__r_term

    def getType(self):
        return self.__type

    def getUncertainty(self):
        return self.__uncertain

    def getEntityInfo(self):
        return self.__entityinfo

    def getPassed(self):
        return self.__passed

    def getFailed(self):
        return self.__failed

    def getAbsence(self):
        return self.__absent

    def getConsecAbsence(self):
        return self.__consec_absent

    def getString(self):
        return self.__string

    def getAllEvals(self):
        return self.__evals
