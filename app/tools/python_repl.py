from langchain.tools import BaseTool
from langchain.tools import PythonREPL
from typing import Optional, Type
from pydantic import BaseModel, Field

class PythonREPLInput(BaseModel):
    code: str = Field(description="The Python code to execute")

class PythonREPLTool(BaseTool):
    name: str = "Python"
    description: str = "Run Python code for data analysis and processing"
    args_schema: Type[BaseModel] = PythonREPLInput
    return_direct: bool = False
    
    def __init__(self):
        super().__init__()
        self.python_repl = PythonREPL()
    
    def _run(self, code: str) -> str:
        """Execute Python code"""
        try:
            return self.python_repl.run(code)
        except Exception as e:
            return f"Error executing Python code: {str(e)}"
    
    async def _arun(self, code: str) -> str:
        return self._run(code)

python_tool = PythonREPLTool() 