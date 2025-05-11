from langchain.tools import BaseTool
from atlassian import Jira
import os
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel, Field
import requests
from datetime import datetime

class CreateJiraIssueInput(BaseModel):
    project_key: str = Field(description="The Jira project key (e.g., 'PROJ')")
    summary: str = Field(description="The summary/title of the issue")
    description: str = Field(description="The detailed description of the issue")
    issue_type: str = Field(default="Task", description="The type of issue (e.g., 'Task', 'Bug', 'Story')")

class UpdateJiraIssueInput(BaseModel):
    issue_key: str = Field(description="The key of the issue to update (e.g., 'PROJ-123')")
    summary: Optional[str] = Field(default=None, description="The new summary/title of the issue")
    description: Optional[str] = Field(default=None, description="The new description of the issue")

class DeleteJiraIssueInput(BaseModel):
    issue_key: str = Field(description="The key of the issue to delete (e.g., 'PROJ-123')")

class AddJiraCommentInput(BaseModel):
    issue_key: str = Field(description="The key of the issue to comment on (e.g., 'PROJ-123')")
    comment: str = Field(description="The comment text to add")

class GetJiraIssueInput(BaseModel):
    issue_key: str = Field(description="The key of the issue to retrieve (e.g., 'PROJ-123')")

class SearchJiraIssuesInput(BaseModel):
    jql: str = Field(description="The JQL query to search for issues")

class JiraAPI:
    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.cloud = os.getenv("JIRA_CLOUD", "true").lower() == "true"
        
        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Missing Jira credentials. Please set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN")
        
        self.jira = Jira(
            url=self.base_url,
            username=self.email,
            password=self.api_token,
            cloud=self.cloud
        )
    
    def create_issue(self, project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
        """Create a new Jira issue"""
        try:
            issue = self.jira.issue_create(
                fields={
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type}
                }
            )
            return f"Successfully created issue: {issue['key']}"
        except Exception as e:
            return f"Error creating issue: {str(e)}"
    
    def update_issue(self, issue_key: str, summary: Optional[str] = None, description: Optional[str] = None) -> str:
        """Update an existing Jira issue"""
        try:
            fields = {}
            if summary:
                fields["summary"] = summary
            if description:
                fields["description"] = description
            
            self.jira.issue_update(issue_key, fields=fields)
            return f"Successfully updated issue {issue_key}"
        except Exception as e:
            return f"Error updating issue: {str(e)}"
    
    def delete_issue(self, issue_key: str) -> str:
        """Delete a Jira issue"""
        try:
            self.jira.issue_delete(issue_key)
            return f"Successfully deleted issue {issue_key}"
        except Exception as e:
            return f"Error deleting issue: {str(e)}"
    
    def add_comment(self, issue_key: str, comment: str) -> str:
        """Add a comment to a Jira issue"""
        try:
            self.jira.issue_add_comment(issue_key, comment)
            return f"Successfully added comment to issue {issue_key}"
        except Exception as e:
            return f"Error adding comment: {str(e)}"
    
    def get_issue(self, issue_key: str) -> str:
        """Get a Jira issue by key"""
        try:
            issue = self.jira.issue(issue_key)
            return f"Issue: {issue['key']}\nSummary: {issue['fields']['summary']}\nDescription: {issue['fields']['description']}"
        except Exception as e:
            return f"Error getting issue: {str(e)}"
    
    def search_issues(self, jql: str) -> str:
        """Search for Jira issues using JQL"""
        try:
            issues = self.jira.jql(jql)
            results = []
            for issue in issues['issues']:
                results.append(f"Issue: {issue['key']}\nSummary: {issue['fields']['summary']}")
            return "\n\n".join(results) if results else "No issues found"
        except Exception as e:
            return f"Error searching issues: {str(e)}"

# Initialize the API
jira_api = JiraAPI()

class CreateJiraIssueTool(BaseTool):
    name: str = "CreateJiraIssue"
    description: str = "Create a new Jira issue"
    args_schema: Type[BaseModel] = CreateJiraIssueInput
    return_direct: bool = False
    
    def _run(self, project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
        return jira_api.create_issue(project_key, summary, description, issue_type)
    
    async def _arun(self, project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
        return self._run(project_key, summary, description, issue_type)

class UpdateJiraIssueTool(BaseTool):
    name: str = "UpdateJiraIssue"
    description: str = "Update an existing Jira issue"
    args_schema: Type[BaseModel] = UpdateJiraIssueInput
    return_direct: bool = False
    
    def _run(self, issue_key: str, summary: Optional[str] = None, description: Optional[str] = None) -> str:
        return jira_api.update_issue(issue_key, summary, description)
    
    async def _arun(self, issue_key: str, summary: Optional[str] = None, description: Optional[str] = None) -> str:
        return self._run(issue_key, summary, description)

class DeleteJiraIssueTool(BaseTool):
    name: str = "DeleteJiraIssue"
    description: str = "Delete a Jira issue"
    args_schema: Type[BaseModel] = DeleteJiraIssueInput
    return_direct: bool = False
    
    def _run(self, issue_key: str) -> str:
        return jira_api.delete_issue(issue_key)
    
    async def _arun(self, issue_key: str) -> str:
        return self._run(issue_key)

class AddJiraCommentTool(BaseTool):
    name: str = "AddJiraComment"
    description: str = "Add a comment to a Jira issue"
    args_schema: Type[BaseModel] = AddJiraCommentInput
    return_direct: bool = False
    
    def _run(self, issue_key: str, comment: str) -> str:
        return jira_api.add_comment(issue_key, comment)
    
    async def _arun(self, issue_key: str, comment: str) -> str:
        return self._run(issue_key, comment)

class GetJiraIssueTool(BaseTool):
    name: str = "GetJiraIssue"
    description: str = "Get a Jira issue by key"
    args_schema: Type[BaseModel] = GetJiraIssueInput
    return_direct: bool = False
    
    def _run(self, issue_key: str) -> str:
        return jira_api.get_issue(issue_key)
    
    async def _arun(self, issue_key: str) -> str:
        return self._run(issue_key)

class SearchJiraIssuesTool(BaseTool):
    name: str = "SearchJiraIssues"
    description: str = "Search for Jira issues using JQL"
    args_schema: Type[BaseModel] = SearchJiraIssuesInput
    return_direct: bool = False
    
    def _run(self, jql: str) -> str:
        return jira_api.search_issues(jql)
    
    async def _arun(self, jql: str) -> str:
        return self._run(jql)

# Create tool instances
create_issue_tool = CreateJiraIssueTool()
update_issue_tool = UpdateJiraIssueTool()
delete_issue_tool = DeleteJiraIssueTool()
add_comment_tool = AddJiraCommentTool()
get_issue_tool = GetJiraIssueTool()
search_issues_tool = SearchJiraIssuesTool()

class JiraInput(BaseModel):
    query: str = Field(description="The JQL query to search for issues")
    max_results: Optional[int] = Field(5, description="Maximum number of results to return")

class JiraTool(BaseTool):
    name: str = "Jira"
    description: str = "Search and retrieve information from Jira tickets"
    args_schema: Type[BaseModel] = JiraInput
    return_direct: bool = False
    
    def _run(self, query: str, max_results: int = 5) -> str:
        """Search Jira using JQL query"""
        jira_url = os.getenv("JIRA_URL")
        jira_email = os.getenv("JIRA_EMAIL")
        jira_token = os.getenv("JIRA_API_TOKEN")
        
        if not all([jira_url, jira_email, jira_token]):
            return "Jira credentials not found. Please set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables."
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        auth = (jira_email, jira_token)
        search_url = f"{jira_url}/rest/api/2/search"
        
        try:
            response = requests.post(
                search_url,
                headers=headers,
                auth=auth,
                json={
                    "jql": query,
                    "maxResults": max_results,
                    "fields": ["summary", "description", "status", "assignee", "created", "updated"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                
                if not issues:
                    return "No issues found matching the query."
                
                result = []
                for issue in issues:
                    fields = issue["fields"]
                    result.append(
                        f"Key: {issue['key']}\n"
                        f"Summary: {fields['summary']}\n"
                        f"Status: {fields['status']['name']}\n"
                        f"Assignee: {fields['assignee']['displayName'] if fields['assignee'] else 'Unassigned'}\n"
                        f"Created: {datetime.fromisoformat(fields['created'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Updated: {datetime.fromisoformat(fields['updated'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
                return "\n".join(result)
            else:
                return f"Error: {response.text}"
        except Exception as e:
            return f"Error accessing Jira: {str(e)}"
    
    async def _arun(self, query: str, max_results: int = 5) -> str:
        return self._run(query, max_results)

jira_tool = JiraTool() 