# Shell Agent App

A web application that uses the Strands Agents library to create an AI assistant that can execute shell commands to answer user questions.

## Features

- AI agent that can execute shell commands to answer questions
- Web interface with real-time streaming responses
- Markdown rendering for better readability
- Conversation memory per session
- WebSocket communication for real-time updates

## Technologies Used

- **Backend**:
  - [Strands Agents](https://strandsagents.com/) - AI agent framework
  - [FastAPI](https://fastapi.tiangolo.com/) - Web framework
  - [WebSockets](https://websockets.readthedocs.io/) - Real-time communication
  - [Uvicorn](https://www.uvicorn.org/) - ASGI server

- **Frontend**:
  - [Vue.js](https://vuejs.org/) - JavaScript framework
  - [Vuetify](https://vuetifyjs.com/) - Material Design component framework
  - [markdown-it](https://github.com/markdown-it/markdown-it) - Markdown parser
  - [highlight.js](https://highlightjs.org/) - Syntax highlighting

## Setup

1. Install dependencies:
   ```bash
   pip install strands-agents fastapi uvicorn websockets boto3
   ```

2. Configure AWS credentials for Bedrock:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Open your browser and navigate to http://localhost:54302

## Usage

1. Type a question in the input field and press Enter or click Send
2. The agent will process your question, execute relevant shell commands, and provide a response
3. The conversation history is maintained for the duration of your session

## Examples

- "What files are in the current directory?"
- "How much disk space is available?"
- "What's my IP address?"
- "Show me the top 5 CPU-intensive processes"
- "Create a simple Python script that prints 'Hello, World!'"

## License

MIT