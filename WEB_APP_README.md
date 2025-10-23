# OS Shell Agent Web Application

This web application provides a chat interface to interact with the OS Shell Agent.

## Features

- Chat interface with WebSocket communication
- Real-time streaming of command outputs
- Markdown rendering of responses
- Dark/Light theme toggle
- Mobile-responsive design

## How to Run

1. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn websockets
   ```

2. Start the web server:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:54545
   ```

## Usage

- Type a message to get general information about the shell agent
- To execute a shell command, prefix your message with `!` followed by the command
  - Example: `!ls -la` or `!echo 'Hello World'`
- The response will be displayed in real-time with proper formatting

## Technical Details

### Backend

- FastAPI web server with WebSocket support
- Asynchronous command execution
- Streaming responses

### Frontend

- Single-file application (index.html)
- Vue.js for reactive UI
- Vuetify for Material Design components
- Vue Router for navigation
- Marked.js for Markdown rendering
- Highlight.js for code syntax highlighting
- DOMPurify for sanitizing HTML

## Architecture

The application follows a simple client-server architecture:

1. Client sends messages via WebSocket
2. Server processes messages and executes shell commands
3. Server streams responses back to the client
4. Client renders the responses in real-time

## Security Considerations

- The application executes shell commands directly, which can be a security risk
- In a production environment, you should implement proper authentication and authorization
- Consider adding command validation and restrictions

## Future Improvements

- Integration with the full Strands Agent capabilities
- User authentication
- Command history
- Session persistence
- More advanced UI features
