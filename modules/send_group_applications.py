# -*- coding: utf-8 -*-
import requests
from config import TOKEN, APPLICATION_SENDGROUP_ID


async def send(text: str):
    token = TOKEN
    url = "https://api.telegram.org/bot"
    channel_id = APPLICATION_SENDGROUP_ID
    url += token
    method = url + "/sendMessage"

    req = requests.post(method, data={
        "chat_id": channel_id,
        "text": text
    })

    if req.status_code != 200:
        raise Exception("post_text error")