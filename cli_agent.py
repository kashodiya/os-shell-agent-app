import subprocess
import json
import platform
import os
from datetime import datetime
from typing import List, Dict, Any
import boto3
from strands import Agent, tool
from strands_tools import mem0_memory
from safety_guardrails import SafetyGuardrails

class CLIAgent(Agent):
    """Agent that can execute CLI commands and handle complex multi-step tasks."""
    
    def __init__(self, session_id: str = None, safe_mode: bool = True):
        # Initialize safety guardrails
        self.safety = SafetyGuardrails(safe_mode=safe_mode)
        self.safe_mode = safe_mode
        
        # Set user ID for memory operations
        self.user_id = session_id or f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
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
You have access to persistent memory through the mem0_memory tool. Use this to:
- Store important information about user preferences, past commands, and context
- Retrieve relevant memories to provide better assistance
- Remember conversation history and user patterns

Always include user_id="{self.user_id}" when using memory operations.
When users ask about previous conversations or "what was my first question", use memory retrieval instead of shell commands.
"""
        
        super().__init__(
            name="CLI Command Agent",
            description="An agent that can execute any CLI command and handle complex tasks by breaking them into steps with persistent memory",
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt=enhanced_system_prompt,
            tools=[mem0_memory]
        )
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
        log_message = f"Safety mode {mode_str} by user request at {datetime.now().isoformat()}"
        try:
            self.tool.mem0_memory(action="store", content=log_message, user_id=self.user_id)
        except Exception as e:
            print(f"Warning: Could not store safety mode change to memory: {e}")
        
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
        """Store interaction in persistent memory."""
        try:
            memory_content = f"Interaction: {interaction_type} - Input: {input_data[:200]} - Output: {output_data[:200]} - Success: {success} - Time: {datetime.now().isoformat()}"
            self.tool.mem0_memory(action="store", content=memory_content, user_id=self.user_id)
        except Exception as e:
            print(f"Warning: Could not store interaction to memory: {e}")
    
    def _parse_memory_result(self, result):
        """Parse memory retrieval result and return list of memories."""
        try:
            if result and result.get('status') == 'success' and result.get('content'):
                import json
                memories_text = result['content'][0]['text']
                return json.loads(memories_text)
            return []
        except Exception as e:
            print(f"Warning: Could not parse memory result: {e}")
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
            self._store_interaction_memory('command', command, output_summary, result.returncode == 0)
            
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
        
        # Retrieve relevant memories for context
        try:
            result = self.tool.mem0_memory(action="retrieve", query=question, user_id=self.user_id, limit=3)
            context = ""
            memories = self._parse_memory_result(result)

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
                result = self.tool.mem0_memory(action="retrieve", query=f"question: {question} command: {command}", user_id=self.user_id, limit=2)
                context = ""
                memories = self._parse_memory_result(result)

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
            
            # Save to memory
            self._store_interaction_memory('question', question, answer, exec_result['success'])
            
            return {
                "question": question,
                "command_used": command,
                "answer": answer,
                "raw_output": exec_result,
                "success": exec_result['success']
            }
            
        except Exception as e:
            error_msg = f"Sorry, I couldn't process your question: {str(e)}"
            self._store_interaction_memory('question', question, error_msg, False)
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
            result = self.tool.mem0_memory(action="retrieve", query=question, user_id=self.user_id, limit=3)
            context = ""
            memories = self._parse_memory_result(result)

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
                result = self.tool.mem0_memory(action="retrieve", query=question, user_id=self.user_id, limit=3)
                context = ""
                memories = self._parse_memory_result(result)

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
            
            self._store_interaction_memory('question', question, answer, exec_result['success'])
            
            return {
                "question": question,
                "command_used": command,
                "answer": answer,
                "raw_output": exec_result,
                "success": exec_result['success']
            }
            
        except Exception as e:
            error_msg = f"Sorry, I couldn't process your question: {str(e)}"
            self._store_interaction_memory('question', question, error_msg, False)
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
            result = self.tool.mem0_memory(action="retrieve", query=question, user_id=self.user_id, limit=3)
            context = ""
            memories = self._parse_memory_result(result)

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