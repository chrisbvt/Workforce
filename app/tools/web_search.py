from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import BaseTool
from typing import Optional, Type, Any, Dict
from pydantic import BaseModel, Field

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the web")

class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the web for current information on a topic"
    args_schema: Type[BaseModel] = WebSearchInput
    return_direct: bool = False
    
    def _run(self, query: str) -> str:
        search = DuckDuckGoSearchRun()
        return search.run(query)
    
    async def _arun(self, query: str) -> str:
        search = DuckDuckGoSearchRun()
        return await search.arun(query)

search_tool = WebSearchTool() 