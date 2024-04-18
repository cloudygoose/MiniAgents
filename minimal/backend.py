import socket
import struct
import traceback
import logging
import time
import os, random, sys
from copy import deepcopy

import json

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger()

sys.path.append("../shared/")

from map import Map
from comm import Comm

from my_utils import MyTimer, MyStruct, helper_clear_path
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                        prog='ProgramName',
                        description='What the program does',
                        epilog='Text at the bottom of help')

    parser.add_argument('--path', default ='../runs/minimal_run0/') 
    parser.add_argument('--map_path', default='../')
    parser.add_argument('--online', action='store_true') #in this case, the back end will wait the front end to interact
    parser.add_argument('--clear_dir', action='store_true') #remove files already in the dir, useful if you are doing online communication with the unity front end
    parser.add_argument('--step_num', type=int, default = 20)
    parser.add_argument('--step_wait', type=float, default = 0) #mimic that there some processing time for each time
    #parser.add_argument('--unit_num_per_step', default = 15) #(deprecated) how many tile units you allow your agent to move in one step (you can vary it for each agent, does not need to be the same)

    args = parser.parse_args()
    
    logger.info(str(args))

    args.comm_path = args.path + '/comm/'
    if not os.path.exists(args.path):
        os.makedirs(args.path)
        logger.info("Making online path " + args.comm_path)
        os.makedirs(args.comm_path, exist_ok = True); 
    else:
        logger.info("Attention, path already exists, wating 2 seconds...")
        time.sleep(2)

    if args.online:
        assert(args.clear_dir) #in the online case, responses should be generated on-the-fly
        comm = Comm(args); args.comm = comm;

    if args.clear_dir:
        helper_clear_path(args)

    map = Map(args.map_path)

    ADMIN_cxy = (24.5, 58.5);

    npcs = []
    npcs += [MyStruct(name = "John", tile_cur = None, item_cur = None)]
    if (1 == 1):
        npcs += [MyStruct(name = "Minnie", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Mickle", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Lu", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Guu", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Peter", tile_cur = None, item_cur = None)]

    if (1 == 0): #you can add any number of npc you want
        npcs += [MyStruct(name = "Alta", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Popcorn", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Bro", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Samo", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Oba", tile_cur = None, item_cur = None)]
        npcs += [MyStruct(name = "Julia", tile_cur = None, item_cur = None)]

    assert(len(set([npc.name for npc in npcs])) == len(npcs))
    #below is a random message set, just add diversity to this random simulation
    message_set = ['good idea', 'it is so exciting', 'remember to walk the dog']
    message_set += ["1SAME1"] * 40; message_set += [""] * 3;
    #1SAME1 means the message of this unit is the same as last unit (repeated 30 times so that it is easier to be sampled), "" means don't show any message

    t = 0; #current step index
    while t < args.step_num:
        fd = {"F0": "STEP_REQUEST", "F1": str(t)}
        if args.online:
            fd = comm.waitAndGetNextMessage()
            while (fd["F0"] != "STEP_REQUEST"):
                assert(fd["F0"] == "AGENT_DIALOGUE_REQUEST")
                if (args.step_wait > 0.0):
                    logger.info('sleep for %f', args.step_wait); time.sleep(args.step_wait);
                comm.respondMessage({"F0": "AGENT_DIALOGUE_RESPONSE", "F1": "Backend got message: " + fd["F2"]})
                fd = comm.waitAndGetNextMessage()

        if fd["F0"] == "STEP_REQUEST":
            t = int(fd["F1"]) #TODO: revered step is not implemented yet
            save_d = {} # make sure all values are strings
            save_d["NPCNames"] = '_'.join([npc.name for npc in npcs]) #on each checkpoint, you can set which npcs are active in the game (you can add new npc at each step)
            save_d["BackEndMessage"] = "Back End Step: {}".format(t)
            for npc in npcs:
                if t == 0:
                    item = map.getRandItem(closeto_c = ADMIN_cxy, closeto_dis = 30.0)
                    npc.tile_cur = map.getCloseTile(item.cxy, add_random = True);
                    npc.item_cur = item;

                #here, we assume all npc stays at the center of a tile, but this is not necessary
                path_l = [npc.tile_cur.cxy] #the first unit is just to set the starting position of each agent
                mes_l = ["step {} start".format(t)] #message can be anything
                if t > 0:
                    item_next = map.getRandItem(closeto_c = npc.tile_cur.cxy, closeto_dis = 60.0)
                    print(npc.name, item_next.name, item_next.sec_name)
                    tile_next = map.getCloseTile(item_next.cxy, add_random = True);
                    path_l = map.getPath(npc.tile_cur.cxy, tile_next.cxy, add_random = True)

                    mes_set_cur = message_set + ["Item " + item_next.name] * 3 + ["Going to area " + item_next.area_name] * 3 + ["Going to sector " + item_next.sec_name] * 3
                    for mk in range(1, len(path_l)):
                        mes_l.append(random.choice(mes_set_cur))
                        #mx = random.randint(-1, 1); my = 0;
                        #if mx == 0: my = random.randint(-1, 1) #we allow two adjacent position to be the same, in this case, the NPC will stay at the same position for a unit of time
                        #cx += mx; cy += my;
                        #ll.append(MyStruct(cx = cx, cy = cy))
                    npc.tile_cur = tile_next; #if you want, the starting position does not need to be same as the ending position of last step
                    npc.item_cur = item_next;

                assert(len(path_l) == len(mes_l))
                sll = ["{:.3f}_{:.3f}".format(k[0], k[1]) for k in path_l]
                save_d[npc.name + ":Path"] = ','.join(sll)
                save_d[npc.name + ":SpeedMul"] = "2.0"; #use this to change the movement speed in the front end
                if (len(path_l) > 50):
                    save_d[npc.name + ":SpeedMul"] = "4.0";
                save_d[npc.name + ":Message"] = "_|||_".join(mes_l); #i just want to use a special splitter for the message strings
            fn = "backend_{}.json".format(t)

            if (args.step_wait > 0.0):
                logger.info('sleep for %f', args.step_wait)
                time.sleep(args.step_wait)

            logger.info('writing to %s', fn)
            with open(os.path.join(args.path, fn), 'w', encoding='utf-8') as f:
                json.dump(save_d, f, ensure_ascii=False, indent=4)

            t += 1;
            if args.online:
                comm.respondMessage({"F0": "STEP_FINISH", "F1": str(t), "F2": fn})
    
