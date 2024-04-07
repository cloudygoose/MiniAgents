import os

from my_utils import MyTimer, MyStruct

from openai import OpenAI
client = OpenAI()

name_map = {
    'gpt_35_turbo': 'gpt-3.5-turbo',
}

def openai_call(llm_name, user_s):
    assert(llm_name in ['gpt_35_turbo', 'gpt-3.5-turbo'])
    if llm_name in name_map: #i can not use gpt-3.5-turbo as a c# enum
        llm_name = name_map[llm_name]
    completion = client.chat.completions.create(
      model= llm_name,
      messages=[
        {"role": "system", "content": "You are a helpful assistant in a farm. Please give a interesting response to the following user utterance."},
        {"role": "user", "content": user_s}
      ],
      temperature = 0.7,
      top_p = 0.95,
    )
    return completion.choices[0].message.content

if __name__ == "__main__":
    completion = openai_call("gpt-3.5-turbo", "Who are you?")
    print(completion)
    breakpoint()