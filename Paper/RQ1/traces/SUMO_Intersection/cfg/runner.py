from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import random
import json
# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa


def generate_routefile():
    random.seed(42)  # make tests reproducible
    N = 3600  # number of time steps
    # demand per second from different directions
    pWE = 1. / 10
    with open("autobahn2.rou.xml", "w") as routes:
        print("""<routes>
        <vType id="cautious" vClass="passenger" maxSpeed="30" speedFactor="0.9" speedDev="0.2" sigma="0.0" tau="1" color = "0,1,0" />
        <vType id="aggressive" vClass="passenger" maxSpeed="70" speedFactor="1.3" speedDev="0.1" sigma="0.8" tau="0.5" color = "1,0,0"/>
        <vType id="normal" vClass="passenger"  maxSpeed="50" speedFactor="1" speedDev="0.05" sigma="0.3" tau = "0.1" color="1,1,0"/>
    
        <route id="move" edges="51o 1i 2o 52i" />""", file=routes)
        vehNr = 0
        for i in range(N):
            if random.uniform(0, 1) < pWE:
                print('    <vehicle id="right_%i" type="typeWE" route="right" depart="%i" />' % (
                    vehNr, i), file=routes)
                vehNr += 1
        print("</routes>", file=routes)


def run():
    """execute the TraCI control loop"""
    step = 0
    trace = {}
    # we start with phase 2 where EW has green
    #while traci.simulation.getMinExpectedNumber() > 0:
    #for i in range(20):
    #    traci.simulationStep()

    while step < 500:
        try:
            traci.simulationStep()
            print("-----------")

            state_ob = {"State":{}, "Entities":{}}

            if(step >= 20 and step <= 100):
                state_ob["State"]["laneclosure"] = 0
            else:
                state_ob["State"]["laneclosure"] = 0
            count = 0

            '''
            entity = {}
            entity['name'] = 'tls_junction'
            entity['class'] = 'junction'
            entity['pos_x'] = 91.64
            entity['pos_y'] = 56.69            
            state_ob["Entities"]["Entity" + str(count)] = entity
            count += 1
            '''
            for vehicle in traci.vehicle.getIDList():
                entity = {}
                entity['name'] = vehicle
                entity['class'] = traci.vehicle.getVehicleClass(vehicle)
            
                #entity['bclass'] = traci.vehicle.getTypeID(vehicle)
                #entity['route_edges'] = traci.vehicle.getRoute(vehicle)
                #entity['current_edge'] = traci.vehicle.getRouteIndex(vehicle)

                if "J" in traci.vehicle.getRoadID(vehicle):
                    entity['in_junction'] = 1
                else:
                    entity['in_junction'] = 0



                if vehicle == 'cautious.0':
                    print(entity['in_junction'])
                    print(traci.vehicle.getNextTLS(vehicle)[0][3])
                entity['pos_x'] = traci.vehicle.getPosition(vehicle)[0]
                entity['pos_y'] = traci.vehicle.getPosition(vehicle)[1]

                #entity['leader'] = []
                #entity['follower'] = []
                #if traci.vehicle.getLeader(vehicle, 0):
                #    entity['leader'] = [traci.vehicle.getLeader(vehicle, 0)]
                #    fix.append([traci.vehicle.getLeader(vehicle, 0)[0], vehicle, traci.vehicle.getLeader(vehicle, 0)[1]])

                '''
                if traci.vehicle.getFollower(vehicle, 0):
                    entity['follower'] = [traci.vehicle.getFollower(vehicle, 0)]
                
                if entity['class'] == "emergency":
                    if step >= 20 and step <= 100:
                        entity['siren'] = {"val": 1, "err":0}
                    else:
                        entity['siren'] = {"val": 0, "err":0}
                '''

                #entity['l_leaders'] = traci.vehicle.getLeftLeaders(vehicle)
                #entity['l_followers'] = traci.vehicle.getLeftFollowers(vehicle)
                #entity['r_leaders'] = traci.vehicle.getRightLeaders(vehicle)
                #entity['r_followers'] = traci.vehicle.getRightFollowers(vehicle)
                #entity['all_neighbors'] = entity['leader'] + entity['l_leaders'] + entity['l_followers'] + entity['r_leaders'] + entity['r_followers']
                #entity['left'] = entity['l_leaders'] + entity['l_followers']
                #entity['right'] = entity['r_leaders'] + entity['r_followers']
                entity['vel_z'] = int(traci.vehicle.getSpeed(vehicle))

                tls = traci.vehicle.getNextTLS(vehicle)[0][3]
                if tls == 'G':
                    entity['tls_state'] = 1
                elif tls == 'r':
                    entity['tls_state'] = -1
                else:
                    entity['tls_state'] = 0

                #entity['acc_z'] = {"val": traci.vehicle.getAcceleration(vehicle), "err":0}
                #entity['pos_x'] = {"val": traci.vehicle.getPosition(vehicle)[0], "err":0}
                #entity['pos_y'] = {"val": traci.vehicle.getPosition(vehicle)[1], "err":0}
                #entity['direction'] = {"val": traci.vehicle.getAngle(vehicle), "err":0}
                entity['edge'] = traci.vehicle.getRoadID(vehicle)
                entity['lane'] = traci.vehicle.getLaneIndex(vehicle)
                entity['frontBumperPos'] = traci.vehicle.getLanePosition(vehicle)
                entity['backBumperPos'] = traci.vehicle.getLanePosition(vehicle) - traci.vehicle.getLength(vehicle)

                bids = '{0:08b}'.format(traci.vehicle.getSignals(vehicle))
                #if bids[-1] == '1':
                #    entity['signals'] = 1
                #elif bids[-2] == '1':
                #    entity['signals'] = -1
                #else:
                #    entity['signals'] = 0
                if bids[-4] == '1':
                    entity['brake'] = 1
                else:
                    entity['brake'] = 0

                #if entity['brake'] == 1 and entity['vel_z']['val'] < 1 and entity['leader'] == [] and (entity['next_tls'] == () or entity['next_tls'][0][3] == 'g'):
                #if (entity['brake']["val"] == 1 and entity['signals']["val"] != 0) or (entity['vel_z']['val'] < 1 and entity['signals']["val"] != 0 and entity['leader'] != []):
                #if (entity['brake']["val"] == 1 and  entity['leader'] == [] and entity['vel_z']['val'] < 1) or (entity['leader'] != [] and entity['vel_z']['val'] < 1):
                #    entity['yield'] = {"val": 1, "err":0}
                #else:
                #    entity['yield'] = {"val": 0, "err":0}

                #entity['left_lanechange'] = 0
                #entity['right_lanechange'] = 0
                #if "'left'" in str(traci.vehicle.getLaneChangeStatePretty(vehicle, 1)[0]) and 'cked' not in str(traci.vehicle.getLaneChangeStatePretty(vehicle, 1)[0]):
                #    if len(traci.vehicle.getLeftLeaders(vehicle,True)) == 0 and len(traci.vehicle.getLeftFollowers(vehicle,True)) == 0:
                #        entity['left_lanechange'] = 1
                #if "'right'" in str(traci.vehicle.getLaneChangeStatePretty(vehicle, -1)[0]) and 'cked' not in str(traci.vehicle.getLaneChangeStatePretty(vehicle, -1)[0]):
                #    if len(traci.vehicle.getRightLeaders(vehicle,True)) == 0 and len(traci.vehicle.getRightFollowers(vehicle,True)) == 0:
                #        entity['right_lanechange'] = 1

                #entity['current_wait'] = traci.vehicle.getWaitingTime(vehicle)
                #entity['total_wait'] = traci.vehicle.getAccumulatedWaitingTime(vehicle)
                state_ob["Entities"]["Entity" + str(count)] = entity

                count += 1

            '''
            for person in traci.person.getIDList():
                entity = {}
                entity['name'] = person
                entity['class'] = "person"
                entity['vel_z'] = traci.person.getSpeed(person)
                entity['acc_z'] = traci.person.getAcceleration(person)
                entity['pos_x'] = traci.person.getPosition(person)[0]
                entity['pos_y'] = traci.person.getPosition(person)[1]
                entity['lane'] = traci.person.getLaneID(person)
                entity['direction'] = traci.person.getAngle(person)

                state_ob["Entities"]["Entity" + str(count)] = entity
                count += 1
            '''


            trace["T" + str(step)] = state_ob
            step += 1
        except Exception as e:
            print(e)
            step += 1
            continue

    print("here")
    with open('../trace3.json', 'w') as fp:
        json.dump(trace, fp, indent=4)
    print("done")

    traci.close()
    sys.stdout.flush()

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # first, generate the route file for this simulation
    #generate_routefile()

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    
    #traci.start([sumoBinary, "-c", "autobahn.sumocfg.xml",
    #                         "--tripinfo-output", "autobahn_info.xml", "--fcd-output", "autobahn_trace.xml","--lanechange-output", "autobahn_lanechange_output.xml", "--seed", "5933", "--lateral-resolution", "1"])
    #traci.start([sumoBinary, "-c", "intersection.sumocfg",
    #                         "--tripinfo-output", "intersection_info.xml", "--fcd-output", "intersection_trace.xml","--lanechange-output", "intersection_lanechange_output.xml", "--seed", "5933"])
    traci.start([sumoBinary, "-c", "./1.sumocfg.xml",
                             "--tripinfo-output", "merge_info.xml", "--fcd-output", "merge_trace.xml","--lanechange-output", "merge_lanechange_output.xml", "--seed", "3333"])
    
    run()

