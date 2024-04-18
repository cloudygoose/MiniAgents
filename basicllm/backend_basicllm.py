import struct
import traceback
import logging
import time, datetime
import os, random, sys
from copy import deepcopy

from persona import Persona

import json

import logging
import gpt_prompt as gp
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger()

sys.path.append("../shared/")

from map import Map
from comm import Comm
from helper_methods import *

from my_utils import MyTimer, MyStruct, helper_clear_path
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                        prog='ProgramName',
                        description='What the program does',
                        epilog='Text at the bottom of help')

    parser.add_argument('--path', default ='../runs/run0/') 
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
        logger.info("Attention, path %s already exists, wating 2 seconds...", args.path)
        time.sleep(2)

    if args.online:
        assert(args.clear_dir) #in the online case, responses should be generated on-the-fly
        comm = Comm(args); args.comm = comm;

    if args.clear_dir:
        helper_clear_path(args)

    map = Map(args.map_path)

    #pnames = ['Minnie Bradley', 'Mickey Jackson', 'Klaus Mueller',]; #
    pnames = ['Minnie Bradley', 'Mickey Jackson', 'Klaus Mueller', 'Lu Mi', 'Coco Reese', 'Adam Liu']
    meta = {'fork_sim_code': 'base_the_ville_isabella_maria_klaus', 'start_date': 'February 13, 2023', 'curr_time': 'February 13, 2023, 07:00:00', 'min_per_step': 60, 'maze_name': 'the_ville', 'persona_names': pnames, 'step': 0}
    curr_time = datetime.datetime.strptime(meta['curr_time'], "%B %d, %Y, %H:%M:%S")

    meta_folder = './storage/minnie_mickey/'; personas = {}
    for persona_name in meta['persona_names']: 
        persona_folder = f"{meta_folder}/personas/{persona_name}"
        #p_x = init_env[persona_name]["x"] #TODO
        #p_y = init_env[persona_name]["y"] #TODO
        curr_persona = Persona(persona_name, persona_folder)
        personas[persona_name] = curr_persona

    env = MyStruct(meta = meta, curr_time = curr_time, personas = personas, map = map, args = args, admin_name = "Tianxing")

    """
    minnie = personas['Minnie Bradley']
    minnie.scratch.curr_time = curr_time
    #ll = gp.run_gpt_prompt_event_poignancy(bella, "super important: my son graduated from colleague!")
    for kk in range(15):
        print(env.curr_time)
        act_s, act_s_full = gp.run_gpt_prompt_get_action_simple(minnie, env)
        print(act_s_full)
        env.curr_time += datetime.timedelta(minutes=meta["min_per_step"])
        sec_s = gp.run_gpt_prompt_get_place_simple(act_s, env)
        print(sec_s)
    breakpoint()
    """

    ADMIN_cxy = (24.5, 58.5);

    assert(len(set([p.name for p in personas.values()])) == len(personas))
    #below is a random message set, just add diversity to this random simulation
    #message_set = ['good idea', 'it is so exciting', 'remember to walk the dog']
    #message_set += ["1SAME1"] * 40; message_set += [""] * 3;
    #1SAME1 means the message of this unit is the same as last unit (repeated 30 times so that it is easier to be sampled), "" means don't show any message

    t = 0; #current step index
    while t < args.step_num:
        fd = {"F0": "STEP_REQUEST", "F1": str(t)}
        if args.online:
            fd = comm.waitAndGetNextMessage();
            conv_lis = []; last_p_name = "";
            while (fd["F0"] != "STEP_REQUEST"):
                assert(fd["F0"] == "AGENT_DIALOGUE_REQUEST")
                p = personas[fd["F1"]];
                if (last_p_name != p.name):
                    conv_lis = []; #reset conv_lis since this is a new npc
                    last_p_name = p.name;
                logger.info("AGENT_DIALOGUE_REQUEST talking with %s", p.name)
                conv_lis.append(f"{env.admin_name}: {fd['F2']}")
                logger.info("\n conv_lis:\n" + "\n".join(conv_lis))
                res = gp.run_gpt_prompt_conversation_simple(p, env, p.act_s_lis, conv_lis)
                logger.info("gpt response: %s", res)
                conv_lis.append(f"{p.scratch.get_str_firstname()}: {res}")   
                comm.respondMessage({"F0": "AGENT_DIALOGUE_RESPONSE", "F1": res})
                fd = comm.waitAndGetNextMessage()

        if fd["F0"] == "STEP_REQUEST":
            t = int(fd["F1"]) #TODO: revered step is not implemented yet
            save_d = {} # make sure all values are strings
            save_d["NPCNames"] = '_'.join([p.name for p in personas.values()]) #on each checkpoint, you can set which npcs are active in the game (you can add new npc at each step)
            save_d["BackEndMessage"] = str(env.curr_time) + "\n" + "Back End Step: {}".format(t)

            logger.info('STEP %d TIME: %s', t, str(env.curr_time))

            for p in personas.values():
                p.s.curr_time = env.curr_time
                act_s, act_s_full = gp.run_gpt_prompt_get_action_simple(p, env)
                sec_s = gp.run_gpt_prompt_get_place_simple(act_s_full, env)
                area = random.choice(list(map.sector_d[sec_s].area_d.values())) #TODO!
                item_s = gp.run_gpt_prompt_get_item_simple(act_s_full, area)
                item_next = map.findItemByName(area, item_s);
                logger.info('\nPERSONA %s: ACT: %s \n SEC: %s AREA: %s ITEM: %s', p.name, act_s, sec_s, area.name, item_s)
                p.act_s_lis.append(str(env.curr_time) + " " + act_s_full)

                if t == 0:
                    #item = map.getRandItem(closeto_c = ADMIN_cxy, closeto_dis = 30.0)
                    p.tile_cur = map.getCloseTile(item_next.cxy, add_random = True);
                    p.item_cur = item_next;

                #here, we assume all npc stays at the center of a tile, but this is not necessary
                path_l = [p.tile_cur.cxy] #the first unit is just to set the starting position of each agent
                mes_l = [act_s] #message can be anything
                if t > 0:
                    tile_next = map.getCloseTile(item_next.cxy, add_random = True);
                    path_l = map.getPath(p.tile_cur.cxy, tile_next.cxy, add_random = False)

                    #mes_set_cur = message_set + ["Item " + item_next.name] * 3 + ["Going to area " + item_next.area_name] * 3 + ["Going to sector " + item_next.sec_name] * 3
                    for mk in range(1, len(path_l)):
                        mes_l.append("1SAME1") #to be simple, we can just show act_s

                    p.tile_cur = tile_next; #if you want, the starting position does not need to be same as the ending position of last step
                    p.item_cur = item_next;

                assert(len(path_l) == len(mes_l))
                sll = ["{:.3f}_{:.3f}".format(k[0], k[1]) for k in path_l]
                save_d[p.name + ":Path"] = ','.join(sll)
                save_d[p.name + ":SpeedMul"] = str(2.0 * random.uniform(1.0, 1.4)); #use this to change the movement speed in the front end #here i make move speed slightly different so that agents are less likely to overlap
                if (len(path_l) > 50):
                    save_d[p.name + ":SpeedMul"] = "4.0";
                save_d[p.name + ":Message"] = "_|||_".join(mes_l); #i just want to use a special splitter for the message strings
            fn = "backend_{}.json".format(t)

            if (args.step_wait > 0.0):
                logger.info('sleep for %f', args.step_wait)
                time.sleep(args.step_wait)

            logger.info('writing to %s', fn)
            with open(os.path.join(args.path, fn), 'w', encoding='utf-8') as f:
                json.dump(save_d, f, ensure_ascii=False, indent=4)

            env.curr_time += datetime.timedelta(minutes=meta["min_per_step"])

            t += 1;
            if args.online:
                comm.respondMessage({"F0": "STEP_FINISH", "F1": str(t), "F2": fn})
    
