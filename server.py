import asyncio
import datetime
import logging
import threading
import queue
import uuid

from fastapi import FastAPI, WebSocket
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import BOT_NUM, USE_MODIFY_FLAG
from llm import Chatbot


def initialize_model():
    device_map = "auto"
    model_path = "ibm-granite/granite-3.0-2b-instruct"
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map=device_map)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model.eval()
    return model, tokenizer

async def receive_message(websocket, llm_manager):
    user_id = str(uuid.uuid4())
    print("Receive task started")
    while True:
        data = await websocket.receive_text()
        if llm_manager.is_chat_start is False:
            llm_manager.is_chat_start = True
        print("User message: {}".format(data))
        llm_manager.generate_response_queue.put(("user", user_id, None, data))
        await asyncio.sleep(0.1)
        

async def send_response(websocket, llm_manager, response_queue):
    print("Send task started")
    while True:
        try:
            response_json = response_queue.get(block=False)
            llm_manager.append_message(**response_json)
            await websocket.send_json(response_json)
        except queue.Empty:
            await asyncio.sleep(1.0)
        await asyncio.sleep(0.1)


app = FastAPI()

# ロガーの設定
logger = logging.getLogger("uvicorn")
# set llm
logger.info("Setting up model")
model, tokenizer = initialize_model()
response_queue = queue.Queue()
llm_manager = Chatbot(model, tokenizer, response_queue, modify_user_message_flag=USE_MODIFY_FLAG, bot_num=BOT_NUM)
logger.info("Model setup complete")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    llm_manager.run()
    receive_task = asyncio.create_task(receive_message(websocket, llm_manager))
    send_task = asyncio.create_task(send_response(websocket, llm_manager, response_queue))
    await websocket.accept()
    await asyncio.gather(receive_task, send_task)


# uvicorn server:app --reload --port 8000