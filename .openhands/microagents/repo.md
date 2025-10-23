# Repository Information

This document contains information about the repository structure and purpose.

## Overview
This repository contains the OS Shell Agent application, which provides a command-line interface for interacting with the operating system through natural language commands.

## Structure
- `src/`: Source code for the application
- `examples/`: Example usage scenarios
- `tests/`: Test cases for the application
- `.openhands/microagents/`: Configuration for OpenHands microagents
- `app.py`: FastAPI web server for the chat interface
- `index.html`: Single-file frontend for the chat interface

## Usage
Please refer to the README.md file in the root directory for detailed usage instructions.

## System Behavior Rules

### Web Application Architecture
- Use FastAPI for web server. Serve the app just using single index.html file.
- Complete frontend code should be contained within one index.html. Put CSS, and JavaScript in same index.html file.
- Use VueJS, Vuetify and Vue-Router using CDN in index.html.
- Put VueJS templates in html and reference from it in the JavaScript code using its id.

### Communication
- Use WebSocket so that we can show the results from agent as soon as they arrive.
- If possible use stream when talking to LLM.
- Wherever it makes sense get the response in Markdown format. If the response is in Markdown format render it using some markdown library from CDN.

### Strands Agent Resources
Here are some resources for Strands Agent. You should consult it whenever necessary:
- https://strandsagents.com/latest/documentation/docs/
- https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/
