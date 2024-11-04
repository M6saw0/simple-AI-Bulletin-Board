# AI Bulletin Board
## Overview
This is a simple AI bulletin board code that uses WebSocket.  
It allows you to experience a virtual bulletin board with AI. The main features are as follows:

- **AI Response Creation**:  
  Using the local LLM "2b," AI generates virtual responses. The AI assumes multiple participants with different settings. Personas are automatically generated, and by specifying the number of participants, you can increase the number of participants on the board.(config.BOT_NUM)

- **AI-Assisted User Post Revision**:  
  People sometimes post emotionally charged messages. Through AI, users can modify their content to be more neutral before posting. This is an optional feature.(config.USE_MODIFY_FLAG)

For more details, please refer to [this website]().

## Environment Setup
First, install PyTorch for CUDA.
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
The available CUDA versions can be checked at [PyTorch Start](https://pytorch.org/get-started/locally/).  
Next, install the other required libraries.
```bash
pip install websockets fastapi[standard] accelerate transformers
```

## Execution
First, start the server.
```bash
uvicorn server:app --reload --port 8000
```
Then, start the client.
```bash
uvicorn client:app --reload --port 8001
```
Once both are running, access `http://localhost:8001` in your browser. After entering text in the textbox and submitting, an AI-generated response will appear. Each persona checks the board every 5 seconds and posts a reply with a 30% probability.

## Reference
This code uses `ibm-granite/granite-3.0-2b-instruct`.
- LLM: [ibm-granite/granite-3.0-2b-instruct](https://huggingface.co/ibm-granite/granite-3.0-2b-instruct)
