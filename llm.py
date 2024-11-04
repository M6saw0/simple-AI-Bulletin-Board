import datetime
import random
import queue
import time
import threading
import uuid

import torch


SYSTEM_PROMPT = """You have the following persona.
# Persona
{persona}

You are chatting on a message board. The other person is anonymous, and you only know their ID. Below is the conversation history on the message board.
# Conversation History
{chat_history}

# Task
Create a reply that continues this conversation history. Careful **not to reveal personal information**, this is anonymous bulletin board.
Create a reply less than 30 words.
Output **only the reply**.

Now, please begin the task.

response: 
"""

PERSONA_PROMPT = """Create a brief persona for a fictional character with the following attributes:

1. **Name and Age** - Basic identity of the character.  
2. **Occupation** - Their job or social role, impacting their perspective and expertise.  
3. **Hobbies and Interests** - Topics they enjoy discussing or exploring.  

Please focus on creating a consistent and realistic persona based on these points. Output only the completed persona. Output less than 512 letters.

persona: 
"""

CHECK_USER_MESSAGE_PROMPT = """Check whether user message contains any of the following:
1. Emotional expressions
2. A strong preference for a particular stance
3. Language that may cause discomfort to others

If Contains, Output: "yes"
If Not Contains, Output: "no"

# user message
{user_message}

Contains:
"""

MODIFY_USER_MESSAGE_PROMPT = """Convert the user's message to a calm and polite expression that avoids inappropriate or overly emotional language while maintaining the original intent. Ensure that the essential facts or requests are preserved so the core message remains clear without causing discomfort to the reader.

# user message
{user_message}

Converted message:
"""


class Chatbot:
    def __init__(self, model, tokenizer, pub_queue: queue.Queue, modify_user_message_flag: bool=True, bot_num: int=2, stop_time: int=10, wait_time: int=60):
        print("Chatbot initialized")
        self.pub_queue = pub_queue
        self.generate_response_queue = queue.Queue()
        self.stop_time = stop_time
        self.wait_time = wait_time
        self.modify_user_message_flag = modify_user_message_flag
        self.model = model
        self.tokenizer = tokenizer
        print("Start creating persona...")
        self.persona_list = []
        for _ in range(bot_num):
            persona = self.create_persona()
            self.persona_list.append(persona)
        self.is_chat_start = False
        self.messages = []
        print("Chatbot ready to run")

    def run(self):
        for persona in self.persona_list:
            threading.Thread(target=self.chat_loop, args=(persona,), daemon=True).start()
        threading.Thread(target=self.generate_response_loop, daemon=True).start()

    def chat_loop(self, persona):
        name = str(uuid.uuid4())
        while True:
            if self.is_chat_start:
                time.sleep(self.stop_time)
                if random.random() < 0.3:
                    print(f"Bot {name} is generating response...")
                    self.generate_response_queue.put(("assistant", name, persona, None))
                    time.sleep(self.wait_time)
                else:
                    print(f"Bot {name} is waiting...")
            time.sleep(0.1)

    def generate_response_loop(self):
        while True:
            role, name, persona, message = self.generate_response_queue.get()
            print("{} received".format(name))
            if role == "user" and self.modify_user_message_flag:
                check_response = self.check_user_chat(message)
                print("User Message modify check: {}".format(check_response))
                if "yes" in check_response.lower():
                    response = self.modify_user_chat(message)
                else:
                    response = message
            elif role == "assistant":
                response = self.generate_response(self.messages, persona).strip(" \"\n")
            else:
                response = message
            print("Bot {} generated: {}".format(name, response))
            self.pub_queue.put({"role": role, "name": name, "content": response, "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            time.sleep(0.1)
            

    def create_persona(self, do_sample=True, temperature=0.8, max_tokens=256):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        messages = [{
            "role": "system",
            "content": PERSONA_PROMPT,
        }]
        chat = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        input_tokens = self.tokenizer(chat, add_special_tokens=False, return_tensors="pt").to(device)
        output = self.model.generate(**input_tokens, do_sample=do_sample, temperature=temperature, max_new_tokens=max_tokens)
        generated_text = self.tokenizer.decode(output[0][input_tokens["input_ids"].shape[1]:], skip_special_tokens=True)
        print("Persona created:")
        print(generated_text)
        return generated_text

    def generate_response(self, messages, persona, do_sample=True, temperature=0.8, max_tokens=1024):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"{len(messages)=}")
        system_messages = [{
            "role": "system",
            "content": SYSTEM_PROMPT.format(persona=persona, chat_history="\n\n".join([f"## ID\n{msg['name']}\n## content\n{msg['content']}" for msg in messages]))
        }]
        chat = self.tokenizer.apply_chat_template(system_messages, tokenize=False, add_generation_prompt=True)
        input_tokens = self.tokenizer(chat, add_special_tokens=False, return_tensors="pt").to(device)
        output = self.model.generate(**input_tokens, do_sample=do_sample, temperature=temperature, max_new_tokens=max_tokens)
        generated_text = self.tokenizer.decode(output[0][input_tokens["input_ids"].shape[1]:], skip_special_tokens=True)
        return generated_text

    def check_user_chat(self, user_message, do_sample=True, temperature=0.8, max_tokens=1024):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        system_messages = [{
            "role": "system",
            "content": CHECK_USER_MESSAGE_PROMPT.format(user_message=user_message)
        }]
        chat = self.tokenizer.apply_chat_template(system_messages, tokenize=False, add_generation_prompt=True)
        input_tokens = self.tokenizer(chat, add_special_tokens=False, return_tensors="pt").to(device)
        output = self.model.generate(**input_tokens, do_sample=do_sample, temperature=temperature, max_new_tokens=max_tokens)
        generated_text = self.tokenizer.decode(output[0][input_tokens["input_ids"].shape[1]:], skip_special_tokens=True)
        return generated_text

    def modify_user_chat(self, user_message, do_sample=True, temperature=0.8, max_tokens=1024):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        system_messages = [{
            "role": "system",
            "content": MODIFY_USER_MESSAGE_PROMPT.format(user_message=user_message)
        }]
        chat = self.tokenizer.apply_chat_template(system_messages, tokenize=False, add_generation_prompt=True)
        input_tokens = self.tokenizer(chat, add_special_tokens=False, return_tensors="pt").to(device)
        output = self.model.generate(**input_tokens, do_sample=do_sample, temperature=temperature, max_new_tokens=max_tokens)
        generated_text = self.tokenizer.decode(output[0][input_tokens["input_ids"].shape[1]:], skip_special_tokens=True)
        return generated_text

    def append_message(self, role, content, name, datetime):
        self.messages.append({"role": role, "content": content, "name": name, "datetime": datetime})


