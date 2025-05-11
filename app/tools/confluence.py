from langchain.tools import BaseTool
from atlassian import Confluence
import os
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel, Field
import requests
from datetime import datetime

class CreateConfluencePageInput(BaseModel):
    space_key: str = Field(description="The Confluence space key")
    title: str = Field(description="The title of the page")
    content: str = Field(description="The content of the page in Confluence storage format")
    parent_id: Optional[str] = Field(default=None, description="The ID of the parent page (optional)")

class UpdateConfluencePageInput(BaseModel):
    page_id: str = Field(description="The ID of the page to update")
    title: Optional[str] = Field(default=None, description="The new title of the page")
    content: Optional[str] = Field(default=None, description="The new content of the page in Confluence storage format")

class DeleteConfluencePageInput(BaseModel):
    page_id: str = Field(description="The ID of the page to delete")

class GetConfluencePageInput(BaseModel):
    page_id: str = Field(description="The ID of the page to retrieve")

class SearchConfluencePagesInput(BaseModel):
    query: str = Field(description="The search query to find pages")
    space_key: Optional[str] = Field(default=None, description="The space key to search in (optional)")

class ConfluenceAPI:
    def __init__(self):
        self.base_url = os.getenv("CONFLUENCE_BASE_URL")
        self.email = os.getenv("CONFLUENCE_EMAIL")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        self.cloud = os.getenv("CONFLUENCE_CLOUD", "true").lower() == "true"
        
        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Missing Confluence credentials. Please set CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN")
        
        self.confluence = Confluence(
            url=self.base_url,
            username=self.email,
            password=self.api_token,
            cloud=self.cloud
        )
    
    def create_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> str:
        """Create a new Confluence page"""
        try:
            page = self.confluence.create_page(
                space=space_key,
                title=title,
                body=content,
                parent_id=parent_id,
                representation='storage'
            )
            return f"Successfully created page: {page['_links']['webui']}"
        except Exception as e:
            return f"Error creating page: {str(e)}"
    
    def update_page(self, page_id: str, title: Optional[str] = None, content: Optional[str] = None) -> str:
        """Update an existing Confluence page"""
        try:
            # Get current page version
            page = self.confluence.get_page_by_id(page_id)
            version = page['version']['number'] + 1
            
            # Update the page
            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=title or page['title'],
                body=content or page['body']['storage']['value'],
                version=version,
                representation='storage'
            )
            return f"Successfully updated page: {updated_page['_links']['webui']}"
        except Exception as e:
            return f"Error updating page: {str(e)}"
    
    def delete_page(self, page_id: str) -> str:
        """Delete a Confluence page"""
        try:
            self.confluence.remove_page(page_id)
            return f"Successfully deleted page {page_id}"
        except Exception as e:
            return f"Error deleting page: {str(e)}"
    
    def get_page(self, page_id: str) -> str:
        """Get a Confluence page by ID"""
        try:
            page = self.confluence.get_page_by_id(page_id)
            return f"Page Title: {page['title']}\nContent: {page['body']['storage']['value']}"
        except Exception as e:
            return f"Error getting page: {str(e)}"
    
    def search_pages(self, query: str, space_key: Optional[str] = None) -> str:
        """Search for Confluence pages"""
        try:
            results = self.confluence.cql(
                query,
                limit=10,
                space_key=space_key
            )
            pages = []
            for result in results['results']:
                pages.append(f"Title: {result['title']}\nID: {result['id']}\nURL: {result['_links']['webui']}")
            return "\n\n".join(pages) if pages else "No pages found"
        except Exception as e:
            return f"Error searching pages: {str(e)}"

# Initialize the API
confluence_api = ConfluenceAPI()

class CreateConfluencePageTool(BaseTool):
    name: str = "CreateConfluencePage"
    description: str = "Create a new Confluence wiki page"
    args_schema: Type[BaseModel] = CreateConfluencePageInput
    return_direct: bool = False
    
    def _run(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> str:
        return confluence_api.create_page(space_key, title, content, parent_id)
    
    async def _arun(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> str:
        return self._run(space_key, title, content, parent_id)

class UpdateConfluencePageTool(BaseTool):
    name: str = "UpdateConfluencePage"
    description: str = "Update an existing Confluence wiki page"
    args_schema: Type[BaseModel] = UpdateConfluencePageInput
    return_direct: bool = False
    
    def _run(self, page_id: str, title: Optional[str] = None, content: Optional[str] = None) -> str:
        return confluence_api.update_page(page_id, title, content)
    
    async def _arun(self, page_id: str, title: Optional[str] = None, content: Optional[str] = None) -> str:
        return self._run(page_id, title, content)

class DeleteConfluencePageTool(BaseTool):
    name: str = "DeleteConfluencePage"
    description: str = "Delete a Confluence wiki page"
    args_schema: Type[BaseModel] = DeleteConfluencePageInput
    return_direct: bool = False
    
    def _run(self, page_id: str) -> str:
        return confluence_api.delete_page(page_id)
    
    async def _arun(self, page_id: str) -> str:
        return self._run(page_id)

class GetConfluencePageTool(BaseTool):
    name: str = "GetConfluencePage"
    description: str = "Get a Confluence page by ID"
    args_schema: Type[BaseModel] = GetConfluencePageInput
    return_direct: bool = False
    
    def _run(self, page_id: str) -> str:
        return confluence_api.get_page(page_id)
    
    async def _arun(self, page_id: str) -> str:
        return self._run(page_id)

class SearchConfluencePagesTool(BaseTool):
    name: str = "SearchConfluencePages"
    description: str = "Search for Confluence pages"
    args_schema: Type[BaseModel] = SearchConfluencePagesInput
    return_direct: bool = False
    
    def _run(self, query: str, space_key: Optional[str] = None) -> str:
        return confluence_api.search_pages(query, space_key)
    
    async def _arun(self, query: str, space_key: Optional[str] = None) -> str:
        return self._run(query, space_key)

# Create tool instances
create_page_tool = CreateConfluencePageTool()
update_page_tool = UpdateConfluencePageTool()
delete_page_tool = DeleteConfluencePageTool()
get_page_tool = GetConfluencePageTool()
search_pages_tool = SearchConfluencePagesTool()

class ConfluenceInput(BaseModel):
    query: str = Field(description="The search query to find Confluence pages")
    max_results: Optional[int] = Field(5, description="Maximum number of results to return")

class ConfluenceTool(BaseTool):
    name: str = "Confluence"
    description: str = "Search and retrieve information from Confluence pages"
    args_schema: Type[BaseModel] = ConfluenceInput
    return_direct: bool = False
    
    def _run(self, query: str, max_results: int = 5) -> str:
        """Search Confluence using CQL query"""
        confluence_url = os.getenv("CONFLUENCE_URL")
        confluence_email = os.getenv("CONFLUENCE_EMAIL")
        confluence_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        if not all([confluence_url, confluence_email, confluence_token]):
            return "Confluence credentials not found. Please set CONFLUENCE_URL, CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN environment variables."
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        auth = (confluence_email, confluence_token)
        search_url = f"{confluence_url}/rest/api/content/search"
        
        try:
            response = requests.get(
                search_url,
                headers=headers,
                auth=auth,
                params={
                    "cql": f'text ~ "{query}"',
                    "limit": max_results,
                    "expand": "version,space"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return "No pages found matching the query."
                
                result = []
                for page in results:
                    result.append(
                        f"Title: {page['title']}\n"
                        f"Space: {page['space']['name']}\n"
                        f"URL: {confluence_url}/pages/viewpage.action?pageId={page['id']}\n"
                        f"Last Updated: {datetime.fromisoformat(page['version']['when'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
                return "\n".join(result)
            else:
                return f"Error: {response.text}"
        except Exception as e:
            return f"Error accessing Confluence: {str(e)}"
    
    async def _arun(self, query: str, max_results: int = 5) -> str:
        return self._run(query, max_results)

confluence_tool = ConfluenceTool() 