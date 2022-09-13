import copy
import neighbors as nutils

class Relation:
    # this initialization should fully initialize the relation with the given node(s)
    # g_nodes contains all of the graph's information on some node (or a pair of nodes)
    def __init__(self, template, g_nodes, count, l_term = "", op = "", r_term = "", ts = 9999):
        self.__template = template
        self.__nodes = g_nodes
        self.__type = template['type']
        self.__l_term = l_term
        self.__r_term = r_term
        self.__op = op
        self.__ID = "INV_" + str(count)

        self.__passed = 0
        self.__failed = 0
        self.__absent = 0
        self.__consec_absent = 0
        self.__uncertain = 0
        self.__string = ""
        self.__entityinfo = self.setEntityInfo()
        self.__evals = {}
        self.__ts = ts
        self.__child = False
        self.__generalForm = ""
        self.__isParent = False

    def setRTerm(self, val):
        self.__r_term = val
        self.setString()
    def setChild(self):
        self.__child = True
    def getChild(self):
        return self.__child

    def isParent(self):
        return self.__isParent
    def getNodeNames(self):
        names = []
        for node in self.__nodes:
            names.append(node['name'])
        return(names)

    def getGeneralForm(self, grouping):
        if self.__type == 'rh_const' and self.__op != '==':
            genForm = self.__l_term + " " + self.__op + " CONST"
        else:
            genForm = self.__l_term + " " + self.__op + " " + self.__r_term

        count = 1
        for node in self.__entityinfo[grouping]:
            cls = self.__entityinfo[grouping][node]
            genForm = genForm.replace(node, cls + str(count))
            count += 1

        self.__generalForm = genForm
        return genForm

    def getGenForm(self):
        return self.__generalForm

    def getTS(self):
        return self.__ts

    def setTerms(self, graph, tautmodel):
        self.__l_term = self.__template["l_term"].replace('NODE1', self.__nodes[0]['name'])
        if len(self.__nodes) > 1:
            self.__l_term = self.__l_term.replace('NODE2', self.__nodes[1]['name'])

        if self.__type == 'rh_const':
            self.__r_term = self.__template["r_term"].replace('CONST', str(eval(self.__l_term)))
        else:
            self.__r_term = self.__template["r_term"].replace('NODE2', self.__nodes[1]['name'])
        self.setString()

    def setEntityInfo(self):
        entity_info = {'class':{}}
        for group in list(entity_info.keys()):
            entity_info[group][self.__nodes[0]['name']] = self.__nodes[0][group]
            if self.__type == 'two_nodes':
                entity_info[group][self.__nodes[1]['name']] = self.__nodes[1][group]
        return entity_info

    def setString(self):
        if(self.__type == 'rh_const' or self.__type == 'two_nodes'):
            self.__string = self.__l_term + " " + self.__op + " " + self.__r_term

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

    def initChild(self, graph, timestep, count, tautmodel):
        self.__isParent == True

        new_relation = Relation(self.__template, self.__nodes, count, self.__l_term, self.__op, eval(self.__l_term), self.__ts)
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
