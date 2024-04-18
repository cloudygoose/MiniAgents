import struct
import traceback
import logging
import time
import os, random, sys
from copy import deepcopy

import json
#import openai
#openai.api_key = os.environ['OPENAI_API_KEY']
from openai import OpenAI
client = OpenAI()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger()

sys.path.append("../shared/")
from helper_methods import *


def run_gpt_prompt_conversation_simple(persona, env, act_his_l, conv_his_l):
  
  act_ss = '\n'.join(act_his_l);
  conv_ss = '\n'.join(conv_his_l);
  scratch = persona.scratch;

  prompt = (f"Please do role playing and have a conversation with {env.admin_name}. Given a persona description, what you did so far, and a conversation history, please give the user an interesting response.\n"
    f"Below is your persona description:\n"
    f"{scratch.get_str_iss_basic()}"
    f"Below is what you did so far:\n"
    f"{act_ss}\n"
    f"Below is the conversation history, please give your response in the end:\n"
    f"{conv_ss}\n"
    f"{scratch.get_str_firstname()}: ")

  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 100, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}

  s = GPT_request(prompt, gpt_param).strip()
  if '\n' in s:
    s = s[:s.find('\n')].strip()

  return s


def run_gpt_prompt_get_item_simple(act_s_full, area):
  item_l = list(set([item.name for item in area.item_l]))
  #print('item_l:', item_l)
  item_ls = ', '.join(['{'+s+'}' for s in item_l])

  area_s, sec_s = area.name, area.sec_name;
  area_sec_s = '{} in {}'.format(area_s, sec_s) if area_s != sec_s else sec_s

  prompt = (f"Please choose an appropriate item from the item options for an event at hand.\n"
    f"Must be one of the \"item options\", verbatim.\n"
    f"Item options: {item_ls}.\n"
    f"Example 1: Place: Minnie's home. Event: Minnie is waking up. Item: {{bed}}.\n"
    f"Example 2: Place: Offices in Company. Event: Klaus is working. Item: {{desk}}.\n"
    f"Again, your answer must be one of the options, verbatim: {item_ls}\n"
    f"Place: {area_sec_s} Event: {act_s_full} Item: "
    )
  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 25, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  s = GPT_request(prompt, gpt_param).strip()

  sp = s[1:s.find('}')]
  if sp in item_l:
    return sp
  else:
    logger.info('error in run_gpt_prompt_get_item_simple, [%s] not in the viable options [%s]', s, item_ls)
    logger.info('returning a random item...')
    return random.choice(item_l)


def run_gpt_prompt_get_place_simple(act_s_full, env):
  map = env.map;
  sector_l = [s.name for s in map.sector_l]
  sector_ls = ', '.join(['{'+s+'}' for s in sector_l])
  prompt = (f"Please choose an appropriate area from the area options for an event at hand.\n"
    f"Must be one of the \"area options\", verbatim.\n"
    f"Area options: {sector_ls}.\n"
    f"Example 1: Event: Minnie is waking up. Place: {{Minnie's home}}.\n"
    f"Example 2: Event: Klaus is working. Place: {{Company}}\n"
    f"Again, your answer must be one of the options, verbatim: {sector_ls}\n"
    f"Event: {act_s_full} Place: "
    )
  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 25, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  s = GPT_request(prompt, gpt_param).strip()

  sp = s[1:s.find('}')]
  if sp in sector_l:
    return sp
  else:
    logger.info('error in run_gpt_prompt_get_place_simple, [%s] not in the viable options [%s]', s, sector_ls)
    logger.info('returning a random sector...')
    return random.choice(sector_l)


def run_gpt_prompt_get_action_simple(persona, env):
  scratch = persona.scratch
  prompt = (f"Please guess what a character is doing at certain time in a day given a persona description. Please directly give your response and make it very short.\n"
    f"Example response 1: Isabella is waking up.\n"
    f"Example response 2: Kelly is creating materials for the lesson.\n"
    f"Example response 3: Klaus is working out.\n"
    f"Below is persona description and the time:\n"
    f"{scratch.get_str_iss_basic()}"
    f"Time:\n"
    f"{str(env.curr_time)}\n" #2023-02-13 06:00:00
    f"Response: {scratch.get_str_firstname()} is "
    )
  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 20, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  res = GPT_request(prompt, gpt_param).strip()
  res = res.replace("probably ", "").replace("likely ", "")
  if len(res) < 3:
    logger.info('[ERROR] problem in run_gpt_prompt_get_action_simple, res: [%s], setting it to [working.].', res)
    res = "working."
    
  res_full = f"{scratch.get_str_firstname()} is " + res
  return res, res_full
  #breakpoint()


def run_gpt_prompt_event_poignancy(persona, event_description, test_input=None, verbose=False): 
  def create_prompt_input(persona, event_description, test_input=None): 
    prompt_input = [persona.scratch.name,
                    persona.scratch.get_str_iss(),
                    persona.scratch.name,
                    event_description]
    return prompt_input
  
  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = int(gpt_response.strip())
    return gpt_response

  def __func_validate(gpt_response, prompt=""): 
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  def get_fail_safe(): 
    return 4

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response, prompt=""): ############
    gpt_response = int(gpt_response)
    return gpt_response

  def __chat_func_validate(gpt_response, prompt=""): ############
    try: 
      __func_clean_up(gpt_response, prompt)
      return True
    except:
      return False 

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 7") ########
  gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 15, 
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "./prompt_template/v3_ChatGPT/poignancy_event_v1.txt" ########
  prompt_input = create_prompt_input(persona, event_description)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  example_output = "5" ########
  special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10." ########
  fail_safe = get_fail_safe() ########
  output = safe_generate_response_json(prompt, gpt_param, example_output, special_instruction, 3, fail_safe,
                                          __chat_func_validate, __chat_func_clean_up, verbose=False)
  if output != False: 
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================


def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the GPT3 server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()


def safe_generate_response(prompt, 
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  if verbose: 
    print (prompt)

  for i in range(repeat): 
    curr_gpt_response = GPT_request(prompt, gpt_parameter)
    if func_validate(curr_gpt_response, prompt=prompt): 
      return func_clean_up(curr_gpt_response, prompt=prompt)
    if verbose: 
      print ("---- repeat count: ", i, curr_gpt_response)
      print (curr_gpt_response)
      print ("~~~~")
  return fail_safe_response


def safe_generate_response_json(prompt,
                                   gpt_param,
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = GPT_request(prompt, gpt_param).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]

      # print ("---ashdfaf")
      # print (curr_gpt_response)
      # print ("000asdfhia")
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except Exception as e:
      print(e)
      breakpoint()

  return False

def GPT_request(prompt, gpt_parameter): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  wait_sec = 1;
  for try_idx in range(10):
    try:
      time.sleep(1)
      #breakpoint()
      if gpt_parameter["engine"] == "gpt-3.5-turbo-instruct":
        response = client.completions.create(
        #response = openai.Completion.create(
                model=gpt_parameter["engine"],
                prompt = prompt,
                temperature=gpt_parameter["temperature"],
                max_tokens=gpt_parameter["max_tokens"],
                top_p=gpt_parameter["top_p"],
                frequency_penalty=gpt_parameter["frequency_penalty"],
                presence_penalty=gpt_parameter["presence_penalty"],
                stream=gpt_parameter["stream"],
                stop=gpt_parameter["stop"],)
        return response.choices[0].text

      if gpt_parameter["engine"] == "gpt-3.5-turbo":
        response = client.chat.completions(
        #response = openai.Completion.create(
                model=gpt_parameter["engine"],
                messages=[{"role": "user", "content": prompt}],
                temperature=gpt_parameter["temperature"],
                max_tokens=gpt_parameter["max_tokens"],
                top_p=gpt_parameter["top_p"],
                frequency_penalty=gpt_parameter["frequency_penalty"],
                presence_penalty=gpt_parameter["presence_penalty"],
                stream=gpt_parameter["stream"],
                stop=gpt_parameter["stop"],)
        breakpoint()
        return response.choices[0].text
      
    except Exception as e: 
      if 'Rate limit' in str(e):
        #this is for openai 0.28 version, in >1.0 version, the client will handle this
        print(f'openai rate_limit_exceeded, retrying in {wait_sec}s...')
        time.sleep(wait_sec); wait_sec *= 2;
        pass
      else:
        print(e)
        breakpoint()
  print('something wrong in GPT_Request...')
  return "GPT_Request Error"


def ChatGPT_request(prompt): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  # temp_sleep()
  #completion = openai.ChatCompletion.create(
  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature = 0.7,
  )
  return completion.choices[0].message.content

