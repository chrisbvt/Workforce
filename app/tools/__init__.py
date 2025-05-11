from app.tools.web_search import search_tool
from app.tools.weather import weather_tool
from app.tools.news import news_tool
from app.tools.confluence import (
    create_page_tool,
    update_page_tool,
    delete_page_tool,
    get_page_tool,
    search_pages_tool
)
from app.tools.jira import (
    create_issue_tool,
    update_issue_tool,
    delete_issue_tool,
    add_comment_tool,
    get_issue_tool,
    search_issues_tool
)

# Dictionary of all available tools
TOOLS = {
    "WebSearch": search_tool,
    "Weather": weather_tool,
    "News": news_tool,
    "CreateJiraIssue": create_issue_tool,
    "UpdateJiraIssue": update_issue_tool,
    "DeleteJiraIssue": delete_issue_tool,
    "AddJiraComment": add_comment_tool,
    "GetJiraIssue": get_issue_tool,
    "SearchJiraIssues": search_issues_tool,
    "CreateConfluencePage": create_page_tool,
    "UpdateConfluencePage": update_page_tool,
    "DeleteConfluencePage": delete_page_tool,
    "GetConfluencePage": get_page_tool,
    "SearchConfluencePages": search_pages_tool
}

# Tool descriptions for documentation
TOOL_DESCRIPTIONS = {
    "WebSearch": "Search the web for current information and news",
    "Weather": "Get current weather information for a location",
    "News": "Get the latest news articles based on a query",
    "CreateJiraIssue": "Create a new Jira issue",
    "UpdateJiraIssue": "Update an existing Jira issue",
    "DeleteJiraIssue": "Delete a Jira issue",
    "AddJiraComment": "Add a comment to a Jira issue",
    "GetJiraIssue": "Get a Jira issue by key",
    "SearchJiraIssues": "Search for Jira issues using JQL",
    "CreateConfluencePage": "Create a new Confluence page",
    "UpdateConfluencePage": "Update an existing Confluence page",
    "DeleteConfluencePage": "Delete a Confluence page",
    "GetConfluencePage": "Get a Confluence page by ID",
    "SearchConfluencePages": "Search for Confluence pages using CQL"
}

def get_available_tools(tool_names: list = None) -> dict:
    """
    Get a dictionary of available tools, optionally filtered by name.
    
    Args:
        tool_names (list, optional): List of tool names to include. If None, returns all tools.
    
    Returns:
        dict: Dictionary of tool name to Tool object
    """
    if tool_names is None:
        return TOOLS
    
    return {name: TOOLS[name] for name in tool_names if name in TOOLS} 