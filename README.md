# OS Shell Agent Web Application

A modern web-based chat interface for interacting with an AI-powered OS Shell Agent built with FastAPI, Vue.js 3, Vuetify 3, and WebSockets. This application provides real-time communication with an intelligent agent that can execute shell commands and provide system information.

## 🚀 Features

- **Real-time Chat Interface**: WebSocket-powered communication for instant responses
- **AI-Powered Shell Agent**: Intelligent agent using Strands Agents framework
- **Safety Mode Toggle**: User-controlled risky mode for potentially dangerous operations
- **Modern UI**: Built with Vue.js 3, Vuetify 3, and Vue Router
- **Single Page Application**: Complete frontend contained in one HTML file
- **Markdown Support**: Rich text rendering with syntax highlighting
- **Command Execution**: Execute shell commands through the agent
- **Expandable Output**: Detailed command output with collapsible sections
- **Responsive Design**: Works on desktop and mobile devices
- **Connection Status**: Real-time WebSocket connection indicator
- **Safety Guardrails**: Built-in protection against dangerous commands

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **WebSockets**: Real-time bidirectional communication
- **Strands Agents**: AI agent framework for intelligent interactions
- **Python 3.8+**: Core programming language

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **Vuetify 3**: Material Design component framework
- **Vue Router**: Client-side routing
- **Marked.js**: Markdown parsing and rendering
- **Highlight.js**: Syntax highlighting for code blocks

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser with WebSocket support

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kashodiya/os-shell-agent-app.git
   cd os-shell-agent-app
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Strands Agents** (if not in requirements.txt):
   ```bash
   pip install strands-agents
   ```

## 🚀 Running the Application

### Basic Usage

1. **Start the FastAPI server with default settings**:
   ```bash
   python web_app.py
   ```

2. **Access the application**:
   Open your web browser and navigate to:
   ```
   http://localhost:51983
   ```

The server will start on port 51983 by default and serve the single-page application.

### Advanced Configuration

The application supports command-line arguments for flexible configuration:

1. **Custom Port**:
   ```bash
   python web_app.py --port 8080
   ```

2. **Custom Host and Port**:
   ```bash
   python web_app.py --host 127.0.0.1 --port 9000
   ```

3. **Debug Logging**:
   ```bash
   python web_app.py --log-level debug
   ```

4. **All Options Combined**:
   ```bash
   python web_app.py --port 8080 --host 0.0.0.0 --log-level info
   ```

5. **View All Available Options**:
   ```bash
   python web_app.py --help
   ```

### Command Line Options

- `--port PORT`: Port number to run the server on (default: 51983)
- `--host HOST`: Host to bind the server to (default: 0.0.0.0)
- `--log-level LEVEL`: Log level - debug, info, warning, error, critical (default: info)
- `--help`: Show help message and exit

## 📁 Project Structure

```
os-shell-agent-app/
├── web_app.py              # FastAPI server with WebSocket support
├── index.html              # Complete SPA with Vue.js frontend
├── cli_agent.py            # CLI agent implementation
├── safety_guardrails.py    # Safety configuration for agent
├── safety_config.json      # Safety rules and restrictions
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── README.md              # This documentation
└── __pycache__/           # Python cache files (ignored)
```

## 🎯 Usage

### Chat Interface

1. **Navigate to Chat**: Click the "CHAT" button in the navigation bar
2. **Safety Mode Control**: Use the toggle switch in the header to enable/disable risky mode
   - **Safe Mode (Default)**: Dangerous commands are blocked or require confirmation
   - **Risky Mode**: All commands allowed (use with caution)
3. **Send Messages**: Type your questions or commands in the input field
4. **Sample Questions**: Use the provided sample buttons for quick testing:
   - "What files are in the current directory?"
   - "Show me the contents of the README.md file"
5. **View Responses**: Agent responses appear in real-time with markdown formatting
6. **Expand Details**: Click on "Command Output" sections to see detailed execution results

### Sample Interactions

**File Listing**:
```
User: What files are in the current directory?
Agent: [Executes 'ls' command and shows formatted file list]
```

**File Content**:
```
User: Show me the contents of the README.md file
Agent: [Executes 'cat README.md' and displays file contents]
```

**Custom Commands**:
```
User: Create a simple Python script that prints "Hello World"
Agent: [Creates hello.py file with the requested content]
```

### Safety Mode Control

The application includes a user-controlled safety mode toggle that allows users to enable or disable risky operations:

**Safe Mode (Default)**:
- Dangerous commands are automatically blocked or require confirmation
- System-critical operations are restricted
- File deletion and modification commands are carefully evaluated
- Network operations may be limited

**Risky Mode**:
- All commands are allowed without restrictions
- Users have full control over system operations
- Confirmation dialog appears when switching from safe to risky mode
- Visual indicators show current safety status

**Toggle Usage**:
1. Click the safety mode toggle switch in the chat interface header
2. When disabling safe mode, a confirmation dialog will appear
3. Confirm or cancel the safety mode change
4. Visual indicators update to reflect current safety status
5. Agent responses include safety mode status messages

## 🔧 Configuration

### Server Configuration

The FastAPI server can be configured using command-line arguments:

```bash
# Default configuration
python web_app.py

# Custom configuration
python web_app.py --port 8080 --host 127.0.0.1 --log-level debug
```

**CORS Configuration** (in `web_app.py`):
```python
# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Available Command Line Options**:
- `--port`: Server port (default: 51983)
- `--host`: Server host (default: 0.0.0.0)
- `--log-level`: Logging level (default: info)

### Agent Configuration

The CLI agent behavior can be modified in `cli_agent.py` and safety rules in `safety_config.json`.

## 🔒 Security Features

- **Safety Mode Toggle**: User-controlled safety mode with confirmation dialogs
- **Safety Guardrails**: Built-in safety checks for command execution
- **Dynamic Safety Control**: Real-time switching between safe and risky modes
- **Command Risk Assessment**: Automatic evaluation of command safety levels
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Server-side validation of user inputs
- **Command Restrictions**: Configurable limits on executable commands

## 🌐 API Endpoints

### HTTP Endpoints

- `GET /`: Serves the main application (index.html)
- `GET /health`: Health check endpoint

### WebSocket Endpoints

- `WS /ws`: WebSocket connection for real-time chat communication

### WebSocket Message Format

**Client to Server**:
```json
{
  "type": "chat_message",
  "content": "Your question or command here",
  "message_id": "unique_message_id"
}
```

**Safety Mode Toggle**:
```json
{
  "type": "toggle_safety_mode",
  "enable_safe_mode": true,
  "message_id": "unique_message_id"
}
```

**Get Safety Status**:
```json
{
  "type": "get_safety_status",
  "message_id": "unique_message_id"
}
```

**Server to Client**:
```json
{
  "type": "agent_response",
  "content": "Agent response in markdown format",
  "message_id": "unique_message_id"
}
```

**Safety Status Response**:
```json
{
  "type": "safety_status",
  "safe_mode": true,
  "message_id": "unique_message_id"
}
```

## 🎨 Frontend Architecture

### Vue.js Components

1. **App Component**: Main application wrapper
2. **Home Component**: Landing page with welcome message
3. **Chat Component**: Real-time chat interface
4. **About Component**: Application information

### Routing

- `/` or `/home`: Home page
- `/chat`: Chat interface
- `/about`: About page

### State Management

The application uses Vue.js reactive data for:
- WebSocket connection status
- Chat messages and history
- Safety mode status and toggle state
- UI state management
- Confirmation dialog states

## 🔧 Development

### Adding New Features

1. **Backend**: Modify `web_app.py` for new API endpoints
2. **Frontend**: Update `index.html` for new Vue.js components
3. **Agent**: Extend `cli_agent.py` for new agent capabilities

### Debugging

1. **Server Logs**: Check console output from `web_app.py`
2. **Browser Console**: Use browser developer tools for frontend debugging
3. **WebSocket**: Monitor WebSocket messages in browser network tab

## 🚀 Deployment

### Local Development
```bash
# Default configuration
python web_app.py

# Custom configuration
python web_app.py --port 8080 --host 127.0.0.1 --log-level debug
```

### Production Deployment

For production, consider using:

1. **Direct Python with custom configuration**:
   ```bash
   python web_app.py --port 80 --host 0.0.0.0 --log-level warning
   ```

2. **Gunicorn with Uvicorn workers**:
   ```bash
   gunicorn web_app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:51983
   ```

3. **Docker** (create Dockerfile):
   ```dockerfile
   FROM python:3.9
   COPY . /app
   WORKDIR /app
   RUN pip install -r requirements.txt
   EXPOSE 51983
   CMD ["python", "web_app.py", "--port", "51983", "--host", "0.0.0.0"]
   ```

4. **Reverse Proxy**: Use Nginx or Apache for production serving

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -am 'Add new feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Find and kill process using port 51983 (default port)
   lsof -ti:51983 | xargs kill -9
   
   # Or use a different port
   python web_app.py --port 8080
   ```

2. **WebSocket Connection Failed**:
   - Check if server is running
   - Verify firewall settings
   - Ensure browser supports WebSockets

3. **Agent Not Responding**:
   - Check Strands Agents installation
   - Verify safety configuration
   - Review server logs for errors

4. **Frontend Not Loading**:
   - Clear browser cache
   - Check browser console for errors
   - Verify CDN resources are accessible

### Performance Optimization

1. **Enable Gzip Compression**
2. **Use CDN for Static Assets**
3. **Implement Connection Pooling**
4. **Add Response Caching**

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue.js 3 Guide](https://vuejs.org/guide/)
- [Vuetify 3 Documentation](https://vuetifyjs.com/)
- [Strands Agents Documentation](https://strandsagents.com/latest/documentation/docs/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## 🏷️ Version History

- **v1.0.0**: Initial release with basic chat functionality
- **v1.1.0**: Added markdown rendering and syntax highlighting
- **v1.2.0**: Improved UI with expandable command output
- **v1.3.0**: Enhanced safety features and error handling
- **v1.4.0**: Added risky mode toggle with user-controlled safety settings
- **v1.5.0**: Added command-line argument support for port, host, and log level configuration

## 👥 Authors

- **OpenHands Agent** - Initial development and implementation

## 🙏 Acknowledgments

- Strands Agents team for the AI agent framework
- FastAPI community for the excellent web framework
- Vue.js and Vuetify teams for the frontend frameworks
- All contributors and testers

---

For more information, visit the [project repository](https://github.com/kashodiya/os-shell-agent-app) or contact the development team.
