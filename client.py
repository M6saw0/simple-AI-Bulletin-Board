from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
        <style>
            .user-message {
                color: blue;
            }
            .assistant-message {
                color: black;
            }
            .message-header {
                margin-bottom: 5px;
            }
            .sender-name {
                font-size: 1.1em;
                margin-right: 15px;
            }
            .timestamp {
                font-size: 0.9em;
                color: #666;
            }
            .message-content {
                font-size: 1.4em;
                margin-bottom: 5px;
            }
            #messages {
                list-style-type: none;
                padding: 0;
            }
            hr {
                border: none;
                border-top: 1px solid #ddd;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <h1>AI Bulletin Board</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var data = JSON.parse(event.data)
                
                message.className = data.role === 'user' ? 'user-message' : 'assistant-message'
                
                var header = document.createElement('div')
                header.className = 'message-header'
                
                var name = document.createElement('span')
                name.className = 'sender-name'
                name.textContent = data.role === 'user' ? 'You' : 'bot_' + data.name
                
                var timestamp = document.createElement('span')
                timestamp.className = 'timestamp'
                timestamp.textContent = data.datetime
                
                var content = document.createElement('div')
                content.className = 'message-content'
                content.textContent = data.content
                
                var divider = document.createElement('hr')
                
                header.appendChild(name)
                header.appendChild(timestamp)
                message.appendChild(header)
                message.appendChild(content)
                message.appendChild(divider)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


# uvicorn server:app --reload --port 8001