# Agent Workforce

A FastAPI-based application for managing and executing AI agent crews.

## Features

- Create and manage AI agent crews
- Execute crews with custom inputs
- View execution history and results
- Support for multiple LLM providers (Anthropic, OpenAI)
- Integration with various tools (Weather, News, Jira, Confluence)
- Selective tool access for agents

## Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- API keys for:
  - Anthropic (required)
  - OpenWeather (optional, for weather tool)
  - NewsAPI (optional, for news tool)
  - Atlassian (optional, for Jira and Confluence tools)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agent-workforce.git
cd agent-workforce
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file in the root directory with your API keys and configuration:
```bash
cp .env.example .env
```

Then edit the `.env` file to add your API keys and configuration.

## Running the Application

Start the server with hot reload:
```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Crews

- `POST /crews/`: Create a new crew
- `GET /crews/`: List all crews
- `GET /crews/{crew_id}`: Get crew details
- `PUT /crews/{crew_id}`: Update a crew
- `DELETE /crews/{crew_id}`: Delete a crew
- `POST /crews/{crew_id}/execute`: Execute a crew

### Executions

- `GET /executions/`: List all executions
- `GET /executions/{execution_id}`: Get execution details

## Environment Variables

Required:
- `ANTHROPIC_API_KEY`: Your Anthropic API key

Optional:
- `OPENWEATHER_API_KEY`: For weather tool
- `NEWS_API_KEY`: For news tool
- `ATLASSIAN_API_TOKEN`: For Jira and Confluence tools
- `ATLASSIAN_EMAIL`: For Jira and Confluence tools
- `ATLASSIAN_URL`: For Jira and Confluence tools
- `CONFLUENCE_BASE_URL`: For Confluence tool
- `CONFLUENCE_EMAIL`: For Confluence tool
- `CONFLUENCE_API_TOKEN`: For Confluence tool
- `CONFLUENCE_CLOUD`: Set to true for cloud instance, false for server instance
- `JIRA_BASE_URL`: For Jira tool
- `JIRA_EMAIL`: For Jira tool
- `JIRA_API_TOKEN`: For Jira tool
- `JIRA_CLOUD`: Set to true for cloud instance, false for server instance

## Development

The project uses Poetry for dependency management. To add new dependencies:

```bash
poetry add package-name
```

To update dependencies:

```bash
poetry update
```

### Database

The project currently uses SQLite for simplicity. Database migrations with Alembic are not implemented at this time. The database schema is managed through SQLAlchemy models and will be created automatically when the application starts.

### Available Tools

The following tools are available for use with agents:

- `WebSearch`: Search the web for current information and news
- `Weather`: Get current weather information for a location
- `News`: Get the latest news articles based on a query
- `CreateJiraIssue`: Create a new Jira issue
- `UpdateJiraIssue`: Update an existing Jira issue
- `DeleteJiraIssue`: Delete a Jira issue
- `AddJiraComment`: Add a comment to a Jira issue
- `GetJiraIssue`: Get a Jira issue by key
- `SearchJiraIssues`: Search for Jira issues using JQL
- `CreateConfluencePage`: Create a new Confluence page
- `UpdateConfluencePage`: Update an existing Confluence page
- `DeleteConfluencePage`: Delete a Confluence page
- `GetConfluencePage`: Get a Confluence page by ID
- `SearchConfluencePages`: Search for Confluence pages using CQL

When executing a crew, you can specify which tools should be available to the agents using the `allowed_tools` parameter. For example:

```python
execution_params = {
    "inputs": {
        "location": "New York",
        "topic": "AI"
    },
    "allowed_tools": ["WebSearch", "Weather", "News"]
}
```

If `allowed_tools` is not specified, all available tools will be provided to the agents.

## TODO

- [ ] Fix tool selection and tool handling to ensure agents only have access to the correct tools during execution.
- [ ] Improve tool configuration and error handling for agent-tool integration.

## License

MIT 