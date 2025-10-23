import subprocess
import json
import platform
import os
from datetime import datetime
from typing import List, Dict, Any
import boto3
from strands import Agent, tool
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from safety_guardrails import SafetyGuardrails

class CLIAgent(Agent):
    """Agent that can execute CLI commands and handle complex multi-step tasks."""
    
    def __init__(self, session_id: str = None, safe_mode: bool = True):
        # Initialize safety guardrails
        self.safety = SafetyGuardrails(safe_mode=safe_mode)
        self.safe_mode = safe_mode
        
        # Set user ID for memory operations
        self.user_id = session_id or f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Load and display system prompt
        system_prompt = self._load_system_prompt()
        print("🤖 CLI Agent System Prompt:")
        print("=" * 50)
        print(system_prompt)
        print("=" * 50)
        
        self._print_safety_status()
        print("=" * 50)
        
        # Enhanced system prompt with memory capabilities
        enhanced_system_prompt = f"""{system_prompt}

## Memory Capabilities
You have access to persistent memory through the built-in memory system. Use this to:
- Store important information about user preferences, past commands, and context
- Retrieve relevant memories to provide better assistance
- Remember conversation history and user patterns

Always include user_id="{self.user_id}" when using memory operations.
When users ask about previous conversations or "what was my first question", use memory retrieval instead of shell commands.
"""
        
        # Initialize simple local memory system (fallback for environments without AWS)
        self.local_memory = {}
        self.memory_counter = 0
        
        # Try to initialize AgentCore memory system for production use
        try:
            # Create a simple in-memory client for local testing
            # In production, you would use AWS Bedrock AgentCore
            self.memory_client = MemoryClient(region_name="us-east-1")
            
            # Create or get memory
            self.memory_resource = self.memory_client.create_memory(
                name=f"CLIAgent_Memory_{self.session_id}",
                description="CLI Agent conversation memory"
            )
            memory_id = self.memory_resource.get('id')
            
            # Configure memory
            agentcore_memory_config = AgentCoreMemoryConfig(
                memory_id=memory_id,
                session_id=self.session_id,
                actor_id=self.user_id
            )
            
            # Create session manager
            session_manager = AgentCoreMemorySessionManager(
                agentcore_memory_config=agentcore_memory_config,
                region_name="us-east-1"
            )
            
            # Initialize the Agent with AgentCore memory session manager
            super().__init__(
                name="CLI Command Agent",
                description="An agent that can execute any CLI command and handle complex tasks by breaking them into steps with persistent memory",
                model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                system_prompt=enhanced_system_prompt,
                tools=[],
                session_manager=session_manager
            )
            
            self.use_agentcore_memory = True
            print("✅ AgentCore memory initialized successfully")
            
        except Exception as e:
            print(f"⚠️  AgentCore memory not available, using local memory: {e}")
            # Fallback to basic agent with local memory
            super().__init__(
                name="CLI Command Agent",
                description="An agent that can execute any CLI command and handle complex tasks by breaking them into steps with persistent memory",
                model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                system_prompt=enhanced_system_prompt,
                tools=[]
            )
            self.use_agentcore_memory = False
        
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    def _print_safety_status(self):
        """Print current safety mode status."""
        if self.safe_mode:
            print("🛡️  SAFETY MODE: ON - Dangerous commands will be blocked or require confirmation")
        else:
            print("⚠️  SAFETY MODE: OFF - All commands allowed (USE WITH CAUTION)")
    
    def toggle_safety_mode(self, enable_safe_mode: bool = None) -> Dict[str, Any]:
        """Toggle or set the safety mode for this agent instance.
        
        Args:
            enable_safe_mode: If provided, sets the safety mode to this value.
                            If None, toggles the current mode.
        
        Returns:
            Dictionary with the new safety mode status and message.
        """
        if enable_safe_mode is None:
            # Toggle current mode
            self.safe_mode = not self.safe_mode
        else:
            # Set to specific mode
            self.safe_mode = enable_safe_mode
        
        # Update safety guardrails
        self.safety.safe_mode = self.safe_mode
        
        # Print status update
        print("=" * 50)
        print("🔄 SAFETY MODE CHANGED:")
        self._print_safety_status()
        print("=" * 50)
        
        # Log the change to memory
        mode_str = "ENABLED" if self.safe_mode else "DISABLED"
        log_message = f"Safety mode {mode_str} by user request"
        self._store_interaction_memory("safety_mode_change", log_message, mode_str, True)
        
        return {
            "safe_mode": self.safe_mode,
            "message": f"Safety mode {'enabled' if self.safe_mode else 'disabled'}",
            "warning": None if self.safe_mode else "⚠️ CAUTION: Risky mode enabled - dangerous commands will not be blocked!"
        }
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety mode status.
        
        Returns:
            Dictionary with current safety mode information.
        """
        return {
            "safe_mode": self.safe_mode,
            "status": "enabled" if self.safe_mode else "disabled",
            "description": "Dangerous commands are blocked or require confirmation" if self.safe_mode else "All commands allowed without safety checks"
        }
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from SYSTEM-PROMPT.md file."""
        try:
            with open('SYSTEM-PROMPT.md', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "You are a CLI Command Agent that helps execute system commands and answer questions."
    
    def _store_interaction_memory(self, interaction_type: str, input_data: str, output_data: str, success: bool = True):
        """Store interaction in memory using AgentCore or local fallback."""
        try:
            from datetime import datetime
            
            if hasattr(self, 'use_agentcore_memory') and self.use_agentcore_memory:
                # AgentCore memory automatically stores conversation context
                memory_content = f"[{interaction_type}] {input_data}"
                if output_data:
                    memory_content += f" -> {output_data[:200]}"
                print(f"💾 Memory stored via AgentCore: {memory_content[:50]}{'...' if len(memory_content) > 50 else ''}")
            else:
                # Use local memory fallback
                memory_key = f"{interaction_type}_{self.memory_counter}"
                self.memory_counter += 1
                
                memory_entry = {
                    "type": interaction_type,
                    "input": input_data,
                    "output": output_data[:500],
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                    "content": f"[{interaction_type}] {input_data}" + (f" -> {output_data[:200]}" if output_data else "")
                }
                
                self.local_memory[memory_key] = memory_entry
                print(f"💾 Memory stored locally: {memory_entry['content'][:50]}{'...' if len(memory_entry['content']) > 50 else ''}")
                
        except Exception as e:
            print(f"Warning: Could not store interaction to memory: {e}")
    
    def _retrieve_memories(self, query: str, limit: int = 5):
        """Retrieve memories using AgentCore or local fallback."""
        try:
            if hasattr(self, 'use_agentcore_memory') and self.use_agentcore_memory:
                # AgentCore memory automatically retrieves relevant context
                print(f"🧠 AgentCore retrieving memories for: {query[:50]}{'...' if len(query) > 50 else ''}")
                return []
            else:
                # Use local memory fallback
                print(f"🧠 Local memory retrieving memories for: {query[:50]}{'...' if len(query) > 50 else ''}")
                matching_memories = []
                query_lower = query.lower()
                
                for key, memory_entry in self.local_memory.items():
                    content = memory_entry.get('content', '').lower()
                    input_data = memory_entry.get('input', '').lower()
                    memory_type = memory_entry.get('type', '')
                    
                    # Enhanced matching for conversation history questions
                    is_match = False
                    
                    # Direct word matching
                    if any(word in content or word in input_data for word in query_lower.split()):
                        is_match = True
                    
                    # Special handling for conversation history questions
                    if any(phrase in query_lower for phrase in ['first question', 'previous question', 'what did i ask', 'my question']):
                        if memory_type == 'user_question':
                            is_match = True
                    
                    # Special handling for command history questions  
                    if any(phrase in query_lower for phrase in ['first command', 'previous command', 'what command', 'last command']):
                        if memory_type == 'command_execution':
                            is_match = True
                    
                    if is_match:
                        matching_memories.append({
                            'memory': memory_entry.get('content', ''),
                            'type': memory_entry.get('type', ''),
                            'timestamp': memory_entry.get('timestamp', ''),
                            'success': memory_entry.get('success', True)
                        })
                        
                        if len(matching_memories) >= limit:
                            break
                
                print(f"🔍 Found {len(matching_memories)} matching memories")
                return matching_memories
                
        except Exception as e:
            print(f"Warning: Could not retrieve memories: {e}")
            return []
    
    @tool
    def execute_command(self, command: str, working_directory: str = None, force: bool = False) -> Dict[str, Any]:
        """Execute a CLI command and return the result.
        
        Args:
            command: The CLI command to execute
            working_directory: Optional working directory for the command
            force: Skip safety checks (use with extreme caution)
            
        Returns:
            Dictionary with command output, error, and return code
        """
        print(f"🔧 Tool: execute_command(command='{command}', working_directory={working_directory})")
        if working_directory:
            print(f"📁 Working directory: {working_directory}")
        
        # Safety validation (unless forced)
        if not force:
            validation = self.safety.validate_command(command, working_directory)
            
            # Display risk assessment
            risk_level = validation['risk_level']
            risk_icons = {'safe': '✅', 'low': '🟡', 'medium': '🟠', 'high': '🔴', 'critical': '⛔'}
            print(f"{risk_icons.get(risk_level, '❓')} Risk Level: {risk_level.upper()} - {validation['reason']}")
            
            # Display warnings
            for warning in validation['warnings']:
                print(f"⚠️  Warning: {warning}")
            
            # Block if not allowed
            if not validation['allowed']:
                error_msg = f"Command blocked: {validation['blocked_reason']}"
                print(f"❌ {error_msg}")
                
                # Suggest alternatives
                alternatives = self.safety.get_safe_alternatives(command)
                if alternatives:
                    print("💡 Suggested alternatives:")
                    for alt in alternatives:
                        print(f"  - {alt}")
                
                self._store_interaction_memory('command', command, error_msg, False)
                return {
                    "command": command,
                    "stdout": "",
                    "stderr": error_msg,
                    "return_code": -1,
                    "success": False,
                    "blocked": True,
                    "risk_level": risk_level
                }
            
            # Require confirmation for risky commands
            if validation['requires_confirmation']:
                print(f"❓ This command requires confirmation due to {risk_level} risk level.")
                
                # Show backup recommendation
                backup_rec = self.safety.create_backup_recommendation(command)
                if backup_rec:
                    print(f"💾 Backup recommendation: {backup_rec}")
                
                print("⚠️  Command execution paused. Use force=True to override or modify the command.")
                self._store_interaction_memory('command', command, "Execution paused - confirmation required", False)
                return {
                    "command": command,
                    "stdout": "",
                    "stderr": "Execution paused - confirmation required",
                    "return_code": -2,
                    "success": False,
                    "requires_confirmation": True,
                    "risk_level": risk_level
                }
            
        try:
            print("⚙️  Executing command...")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_directory
            )
            
            print(f"📤 Command output:")
            if result.stdout:
                print(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"STDERR:\n{result.stderr}")
            print(f"Return code: {result.returncode}")
            
            # Save to memory
            output_summary = result.stdout[:200] if result.stdout else result.stderr[:200]
            self._store_interaction_memory('command_execution', command, output_summary, result.returncode == 0)
            
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }
        except Exception as e:
            print(f"❌ Exception during execution: {str(e)}")
            self._store_interaction_memory('command', command, str(e), False)
            return {
                "command": command,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "success": False
            }
    
    @tool
    def answer_question(self, question: str, working_directory: str = None) -> Dict[str, Any]:
        """Answer a natural language question by determining the appropriate CLI command and executing it.
        
        Args:
            question: Natural language question in English
            working_directory: Optional working directory for the command
            
        Returns:
            Dictionary with the answer, command used, and execution result
        """
        print(f"🔧 Tool: answer_question(question='{question}', working_directory={working_directory})")
        # Detect operating system
        is_windows = platform.system().lower() == 'windows'
        
        if is_windows:
            examples = """
Examples for Windows:
- "What files are in this directory?" -> "dir"
- "What's my current location?" -> "cd"
- "What processes are running?" -> "tasklist"
- "How much disk space is available?" -> "wmic logicaldisk get size,freespace,caption"
- "What's in this file?" -> "type filename"
- "What's the system info?" -> "systeminfo"""
        else:
            examples = """
Examples for Unix/Linux:
- "What files are in this directory?" -> "ls -la"
- "What's my current location?" -> "pwd"
- "What processes are running?" -> "ps aux"
- "How much disk space is available?" -> "df -h"
- "What's in this file?" -> "cat filename"""
        
        # First, check if we can answer from memory without executing commands
        try:
            memories = self._retrieve_memories(query=question, limit=5)
            
            if memories and len(memories) > 0:
                # Check if the question can be answered directly from memory
                memory_context = "Previous interactions and information:\n"
                for memory in memories:
                    memory_context += f"- {memory.get('memory', '')}\n"
                
                # Try to answer from memory first
                memory_prompt = f"""Based on the following previous interactions, can you directly answer this question without needing to execute any new commands?

{memory_context}

Question: {question}

If you can answer the question directly from the above information, provide the answer. 
If you cannot answer from the available information, respond with "NEED_COMMAND" and I will execute a command to get the information.

Answer:"""
                
                print("🧠 Checking if question can be answered from memory...")
                memory_response = self.bedrock.invoke_model(
                    modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": memory_prompt}]
                    })
                )
                
                memory_answer = json.loads(memory_response['body'].read())['content'][0]['text'].strip()
                
                if not memory_answer.startswith("NEED_COMMAND"):
                    print("✅ Answered from memory!")
                    # Store this Q&A interaction in memory
                    self._store_interaction_memory("question_answer", question, memory_answer, True)
                    return {
                        "answer": memory_answer,
                        "command_used": "Retrieved from memory",
                        "success": True,
                        "from_memory": True
                    }
                else:
                    print("🔍 Memory insufficient, will execute command...")
            
            # Prepare context for command generation
            context = ""
            if memories and len(memories) > 0:
                context = "Previous relevant context:\n"
                for memory in memories:
                    context += f"- {memory.get('memory', '')}\n"
                context += "\n"
        except Exception as e:
            print(f"Warning: Could not retrieve memories: {e}")
            context = ""
        
        prompt = f"""{context}Convert this English question to the most appropriate CLI command for {platform.system()}:

Question: {question}

Provide only the CLI command that would answer this question. Be specific and use commands available on {platform.system()}.
If multiple commands are needed, provide the most important one.
{examples}

Command:"""
        
        try:
            print(f"🤔 Thinking: Converting question '{question}' to appropriate command for {platform.system()}...")
            
            response = self.bedrock.invoke_model(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            command = result['content'][0]['text'].strip()
            
            # Clean up the command (remove any extra text)
            command_lines = command.split('\n')
            command = command_lines[0].strip()
            
            print(f"💡 Selected command: {command}")
            print(f"⚡ Executing command...")
            
            # Execute the command
            exec_result = self.execute_command(command, working_directory)
            
            if exec_result['success']:
                print(f"✅ Command executed successfully")
            else:
                print(f"❌ Command failed with return code {exec_result['return_code']}")
                if exec_result['stderr']:
                    print(f"Error: {exec_result['stderr']}")
            
            print(f"🧠 Interpreting results...")
            
            # Generate human-readable answer
            # Retrieve relevant memories for context
            try:
                memories = self._retrieve_memories(query=f"question: {question} command: {command}", limit=2)
                context = ""

                if memories and len(memories) > 0:
                    context = "Previous relevant context:\n"
                    for memory in memories:
                        context += f"- {memory.get('memory', '')}\n"
                    context += "\n"
            except Exception as e:
                print(f"Warning: Could not retrieve memories for answer generation: {e}")
                context = ""
            
            answer_prompt = f"""{context}Based on this command output, provide a clear English answer to the original question.

Original Question: {question}
Command Used: {command}
Command Output: {exec_result['stdout']}
Command Error: {exec_result['stderr']}

Provide a concise, helpful answer in plain English:"""
            
            answer_response = self.bedrock.invoke_model(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": answer_prompt}]
                })
            )
            
            answer_result = json.loads(answer_response['body'].read())
            answer = answer_result['content'][0]['text'].strip()
            
            print(f"📝 Generated answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            
            # Save to memory - store both the question and the full interaction
            self._store_interaction_memory('question_answer', question, answer, exec_result['success'])
            # Also store the user question separately for conversation history
            self._store_interaction_memory('user_question', f"User asked: {question}", f"Answered with command: {command}", exec_result['success'])
            
            return {
                "question": question,
                "command_used": command,
                "answer": answer,
                "raw_output": exec_result,
                "success": exec_result['success']
            }
            
        except Exception as e:
            error_msg = f"Sorry, I couldn't process your question: {str(e)}"
            self._store_interaction_memory('question_answer', question, error_msg, False)
            self._store_interaction_memory("user_question", f"User asked: {question}", "Error occurred", False)
            return {
                "question": question,
                "command_used": "unknown",
                "answer": error_msg,
                "raw_output": None,
                "success": False
            }
    
    def answer_question_with_force(self, question: str, working_directory: str = None) -> Dict[str, Any]:
        """Answer a question with force mode enabled for risky commands."""
        print(f"🔧 Tool: answer_question_with_force(question='{question}', working_directory={working_directory})")
        is_windows = platform.system().lower() == 'windows'
        
        if is_windows:
            examples = """
Examples for Windows:
- "What files are in this directory?" -> "dir"
- "What's my current location?" -> "cd"
- "What processes are running?" -> "tasklist"
- "How much disk space is available?" -> "wmic logicaldisk get size,freespace,caption"
- "What's in this file?" -> "type filename"
- "What's the system info?" -> "systeminfo"""
        else:
            examples = """
Examples for Unix/Linux:
- "What files are in this directory?" -> "ls -la"
- "What's my current location?" -> "pwd"
- "What processes are running?" -> "ps aux"
- "How much disk space is available?" -> "df -h"
- "What's in this file?" -> "cat filename"""
        
        # Retrieve relevant memories for context
        try:
            memories = self._retrieve_memories(query=question, limit=3)
            context = ""

            if memories and len(memories) > 0:
                context = "Previous relevant context:\n"
                for memory in memories:
                    context += f"- {memory.get('memory', '')}\n"
                context += "\n"
        except Exception as e:
            print(f"Warning: Could not retrieve memories: {e}")
            context = ""
        prompt = f"""{context}Convert this English question to the most appropriate CLI command for {platform.system()}:

Question: {question}

Provide only the CLI command that would answer this question. Be specific and use commands available on {platform.system()}.
If multiple commands are needed, provide the most important one.
{examples}

Command:"""
        
        try:
            print(f"🤔 Thinking: Converting question '{question}' to appropriate command for {platform.system()}...")
            
            response = self.bedrock.invoke_model(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            command = result['content'][0]['text'].strip()
            
            command_lines = command.split('\n')
            command = command_lines[0].strip()
            
            print(f"💡 Selected command: {command}")
            print(f"🔥 FORCE MODE: Executing command with safety bypassed...")
            
            exec_result = self.execute_command(command, working_directory, force=True)
            
            if exec_result['success']:
                print(f"✅ Command executed successfully")
            else:
                print(f"❌ Command failed with return code {exec_result['return_code']}")
                if exec_result['stderr']:
                    print(f"Error: {exec_result['stderr']}")
            
            print(f"🧠 Interpreting results...")
            
            # Retrieve relevant memories for context
            try:
                memories = self._retrieve_memories(query=question, limit=3)
                context = ""

                if memories and len(memories) > 0:
                    context = "Previous relevant context:\n"
                    for memory in memories:
                        context += f"- {memory.get('memory', '')}\n"
                    context += "\n"
            except Exception as e:
                print(f"Warning: Could not retrieve memories: {e}")
                context = ""
            answer_prompt = f"""{context}Based on this command output, provide a clear English answer to the original question.

Original Question: {question}
Command Used: {command}
Command Output: {exec_result['stdout']}
Command Error: {exec_result['stderr']}

Provide a concise, helpful answer in plain English:"""
            
            answer_response = self.bedrock.invoke_model(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": answer_prompt}]
                })
            )
            
            answer_result = json.loads(answer_response['body'].read())
            answer = answer_result['content'][0]['text'].strip()
            
            print(f"📝 Generated answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            
            self._store_interaction_memory('question_answer', question, answer, exec_result['success'])
            # Also store the user question separately for conversation history
            self._store_interaction_memory('user_question', f"User asked: {question}", f"Answered with command: {command}", exec_result['success'])
            
            return {
                "question": question,
                "command_used": command,
                "answer": answer,
                "raw_output": exec_result,
                "success": exec_result['success']
            }
            
        except Exception as e:
            error_msg = f"Sorry, I couldn't process your question: {str(e)}"
            self._store_interaction_memory('question_answer', question, error_msg, False)
            self._store_interaction_memory("user_question", f"User asked: {question}", "Error occurred", False)
            return {
                "question": question,
                "command_used": "unknown",
                "answer": error_msg,
                "raw_output": None,
                "success": False
            }
    
    @tool
    def create_task_plan(self, task_description: str) -> List[str]:
        """Create a step-by-step plan for complex tasks using Bedrock Claude model.
        
        Args:
            task_description: Description of the task to be completed
            
        Returns:
            List of executable CLI commands
        """
        print(f"🔧 Tool: create_task_plan(task_description='{task_description}')")
        
        # Detect OS for appropriate commands
        is_windows = platform.system().lower() == 'windows'
        os_info = "Windows (use cmd/powershell commands)" if is_windows else "Unix/Linux (use bash commands)"
        
        prompt = f"""Create executable CLI commands for this task: {task_description}

Operating System: {os_info}

Provide ONLY executable CLI commands, one per line. Each command should be ready to run directly.
For Windows, use commands like: mkdir, cd, python -m venv, pip install, echo, etc.
Do not include explanatory text, just the commands."""
        
        try:
            response = self.bedrock.invoke_model(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            plan_text = result['content'][0]['text']
            
            # Extract commands from the response
            commands = []
            for line in plan_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('Step'):
                    # Remove numbering if present
                    if line[0].isdigit() and '.' in line:
                        line = line.split('.', 1)[1].strip()
                    # Remove bullet points
                    line = line.lstrip('-*').strip()
                    if line:
                        commands.append(line)
            
            return commands if commands else [task_description]
            
        except Exception as e:
            return [task_description]
    
    def summarize_command_output(self, command: str, result: Dict[str, Any]) -> str:
        """Summarize command output using LLM for better user understanding.
        
        Args:
            command: The CLI command that was executed
            result: The execution result dictionary
            
        Returns:
            Human-readable summary of the command output
        """
        try:
            # Retrieve relevant memories for context
            memories = self._retrieve_memories(query=question, limit=3)
            context = ""

            if memories and len(memories) > 0:
                context = "Previous relevant context:\n"
                for memory in memories:
                    context += f"- {memory.get('memory', '')}\n"
                context += "\n"
        except Exception as e:
            print(f"Warning: Could not retrieve memories: {e}")
            context = ""
            prompt = f"""{context}Summarize this command output in a clear, concise way for the user.

Command: {command}
Output: {result.get('stdout', '')}
Error: {result.get('stderr', '')}
Return Code: {result.get('return_code', 0)}

Provide a helpful summary that explains what the command did and what the results mean. Be concise but informative:"""
            
            response = self.bedrock.invoke_model(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            summary_result = json.loads(response['body'].read())
            summary = summary_result['content'][0]['text'].strip()
            
            return summary
            
        except Exception as e:
            # Fallback to basic summary if LLM fails
            if result['success']:
                return f"Command '{command}' executed successfully. Output length: {len(result.get('stdout', ''))} characters."
            else:
                return f"Command '{command}' failed with return code {result.get('return_code', -1)}. Error: {result.get('stderr', 'Unknown error')[:100]}"
    
    def execute_task(self, task: str, working_dir: str = None) -> Dict[str, Any]:
        """Execute a task, creating a plan if it's complex."""
        print(f"🔧 Method: execute_task(task='{task}', working_dir={working_dir})")
        
        # Check if task seems complex
        complex_keywords = ["and", "then", "after", "install", "build", "deploy", "setup"]
        is_complex = any(keyword in task.lower() for keyword in complex_keywords) or len(task.split()) > 10
        
        if is_complex:
            plan = self.create_task_plan(task)
            results = []
            
            for i, step in enumerate(plan, 1):
                print(f"Step {i}: {step}")
                # Execute each step as individual command
                result = self.execute_command(step, working_dir)
                results.append(result)
                
                # Stop if step failed (unless it's a non-critical step)
                if not result['success'] and not any(word in step.lower() for word in ['create', 'mkdir', 'echo']):
                    print(f"❌ Step {i} failed, stopping execution")
                    break
            
            return {"plan": plan, "results": results, "task_type": "complex"}
        else:
            result = self.execute_command(task, working_dir)
            return {"results": [result], "task_type": "simple"}