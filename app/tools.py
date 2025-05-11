from app.tools.web_search import WebSearchTool
from app.tools.wikipedia import WikipediaTool
from app.tools.weather import WeatherTool
from app.tools.news import NewsTool
from app.tools.jira import JiraTool
from app.tools.confluence import ConfluenceTool
from typing import List
from langchain.tools import BaseTool

def get_available_tools() -> List[BaseTool]:
    """Return a list of all available tools"""
    return [
        WebSearchTool(),
        WikipediaTool(),
        WeatherTool(),
        NewsTool(),
        JiraTool(),
        ConfluenceTool()
    ]

# Tool descriptions for agent configuration
TOOL_DESCRIPTIONS = {
    "Web Search": "Search the web for current information on any topic",
    "Wikipedia": "Search Wikipedia for detailed information on a topic",
    "Weather": "Get current weather information for any location",
    "News": "Get latest news articles on any topic",
    "Jira": "Search and retrieve information from Jira tickets",
    "Confluence": "Search and retrieve information from Confluence pages"
} 