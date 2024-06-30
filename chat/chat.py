from openai import OpenAI
import requests
import json
import os
import toml
import datetime

config = toml.load('settings.toml')
openai_api_key = config['apikey']

client = OpenAI(api_key=openai_api_key)

aimodel = "gpt-4"

def queryai(msg):
    msgs = [
        # {"role": "system", "content": "You are FunnyBot"},
        # {"role": "assistant", "content": "relevant:"}, # RAG
        {"role": "user", "content": msg}
    ]

    cc=client.chat.completions.create(
    messages=[
    # {"role": "system", "content": "You are FunnyBot"},
    {"role": "assistant", "content": ""}, # RAG
    {"role": "user", "content": msg}
    ], stream=True, max_tokens=420, top_p=.69, model=aimodel)
    reply1 = ''
    for ck in cc:
        reply1 += (ck.choices[0].delta.content or "")
    print('reply: ', reply1)
    now = datetime.datetime.now()

    # format the timestamp
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # create a new file with the timestamp in its name
    with open(f"reply_{timestamp}.txt", "w") as f:
        f.write(reply1)
    # with open('reply.txt','w') as f:
    #     f.write(reply1)


msg = """"thisisatestpleaserepondwithello"""
queryai(msg)
