
# OS Shell Agent Web Application

This web application provides a chat interface to interact with the OS Shell Agent.

## Features

- Chat interface with WebSocket communication
- Real-time streaming of command outputs
- Markdown rendering of responses
- Dark/Light theme toggle
- Mobile-responsive design
- File operations (read, write, append)
- Advanced shell command execution

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

### Shell Commands
Start your message with `!` followed by the shell command:
```
!ls -la
!echo "Hello World"
!python -c "print('Hello from Python')"
```

### File Operations
Read a file:
```
read:/path/to/file.txt
```

Write to a file (overwrites existing content):
```
write:/path/to/file.txt:Content to write
```

Append to a file:
```
append:/path/to/file.txt:Content to append
```

### Examples
- `!ls -la` - List all files in the current directory
- `!cat app.py` - Display the content of app.py
- `read:app.py` - Read the content of app.py with syntax highlighting
- `write:test.txt:Hello World` - Create or overwrite test.txt with "Hello World"
- `append:log.txt:New log entry` - Append "New log entry" to log.txt

## Technical Details

### Backend

- FastAPI web server with WebSocket support
- Asynchronous command execution
- Streaming responses
- Simplified Advanced Shell Agent implementation
- Per-client agent instances

### Frontend

- Single-file application (index.html)
- Vue.js for reactive UI
- Vuetify for Material Design components
- Vue Router for navigation
- Marked.js for Markdown rendering
- Highlight.js for code syntax highlighting
- DOMPurify for sanitizing HTML

## Architecture

The application follows a client-server architecture:

1. Client sends messages via WebSocket
2. Server routes messages to the client's dedicated agent instance
3. Agent processes messages and executes commands or file operations
4. Server streams responses back to the client
5. Client renders the responses in real-time with Markdown formatting

## Security Considerations

- The application executes shell commands directly, which can be a security risk
- In a production environment, you should implement proper authentication and authorization
- Consider adding command validation and restrictions
- File operations should be restricted to specific directories

## Future Improvements

- Integration with the full Strands Agent capabilities
- User authentication
- Command history
- Session persistence
- More advanced UI features
- Task planning and execution
- Integration with external APIs
