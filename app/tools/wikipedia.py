from langchain.tools import BaseTool
from langchain.utilities import WikipediaAPI
from typing import Optional, Type
from pydantic import BaseModel, Field

class WikipediaInput(BaseModel):
    query: str = Field(description="The search query to look up on Wikipedia")

class WikipediaTool(BaseTool):
    name: str = "Wikipedia"
    description: str = "Search Wikipedia for information on a topic"
    args_schema: Type[BaseModel] = WikipediaInput
    return_direct: bool = False
    
    def __init__(self):
        super().__init__()
        self.wikipedia = WikipediaAPI()
    
    def _run(self, query: str) -> str:
        """Search Wikipedia for information"""
        try:
            return self.wikipedia.run(query)
        except Exception as e:
            return f"Error searching Wikipedia: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        return self._run(query)

wikipedia_tool = WikipediaTool() 