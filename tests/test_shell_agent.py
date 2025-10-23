

#!/usr/bin/env python3
"""
Tests for the Shell Agent
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shell_agent import ShellAgent, ShellCommandTool

class TestShellCommandTool(unittest.TestCase):
    """Tests for the ShellCommandTool class."""
    
    def test_init(self):
        """Test initialization of ShellCommandTool."""
        tool = ShellCommandTool()
        self.assertEqual(tool.name, "shell_command")
        self.assertIn("command", tool.parameters)
    
    @patch('subprocess.run')
    def test_execute_success(self, mock_run):
        """Test successful execution of a command."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.stdout = "test output"
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Create the tool and execute a command
        tool = ShellCommandTool()
        result = tool.execute({"command": "echo test"})
        
        # Check the result
        self.assertEqual(result["stdout"], "test output")
        self.assertEqual(result["stderr"], "")
        self.assertEqual(result["exit_code"], 0)
        
        # Check that subprocess.run was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs["shell"], True)
        self.assertEqual(kwargs["capture_output"], True)
        self.assertEqual(kwargs["text"], True)
    
    def test_execute_no_command(self):
        """Test execution with no command provided."""
        tool = ShellCommandTool()
        result = tool.execute({})
        self.assertTrue(hasattr(result, "message"))
        self.assertIn("No command provided", result.message)

class TestShellAgent(unittest.TestCase):
    """Tests for the ShellAgent class."""
    
    @patch('strands.Agent')
    def test_init(self, mock_agent_class):
        """Test initialization of ShellAgent."""
        # Create a mock Agent instance
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Create the ShellAgent
        agent = ShellAgent(model_id="test-model")
        
        # Check that Agent was initialized correctly
        mock_agent_class.assert_called_once()
        args, kwargs = mock_agent_class.call_args
        self.assertEqual(kwargs["model_id"], "test-model")
        self.assertEqual(len(kwargs["tools"]), 2)  # ShellCommandTool and PlanningTool
    
    @patch('strands.Agent')
    def test_run(self, mock_agent_class):
        """Test running the ShellAgent."""
        # Create a mock Agent instance
        mock_agent = MagicMock()
        mock_agent.return_value = "test response"
        mock_agent_class.return_value = mock_agent
        
        # Create the ShellAgent and run a task
        agent = ShellAgent()
        response = agent.run("test task")
        
        # Check that the agent was called correctly
        mock_agent.assert_called_once_with("test task")
        self.assertEqual(response, "test response")

if __name__ == "__main__":
    unittest.main()

