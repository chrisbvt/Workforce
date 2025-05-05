# CrewAI UI

A modern web interface for managing and interacting with CrewAI agents and crews.

## Features

- Create and manage crews of AI agents
- Define agent roles and goals
- Create and assign tasks to agents
- Real-time task execution and monitoring
- Modern, responsive UI built with React and Tailwind CSS

## Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL (optional, can use SQLite for development)
- Poetry (Python package manager)

## Setup

### Database Setup

The application supports both PostgreSQL and SQLite databases. You can choose which one to use by setting the `DATABASE_TYPE` environment variable.

#### PostgreSQL (Production)

1. Install PostgreSQL:
   ```bash
   # macOS
   brew install postgresql
   
   # Ubuntu
   sudo apt-get install postgresql postgresql-contrib
   ```

2. Create a database:
   ```bash
   createdb crewai_db
   ```

3. Configure environment variables in `.env`:
   ```
   DATABASE_TYPE=postgresql
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=crewai_db
   POSTGRES_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
   ```

#### SQLite (Development)

For development and testing, you can use SQLite with an in-memory database:

1. Configure environment variables in `.env`:
   ```
   DATABASE_TYPE=sqlite
   SQLITE_URL=sqlite+aiosqlite:///:memory:
   ```

### Backend Setup

1. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your OpenAI API key and database configuration.

4. Start the backend server:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## API Documentation

Once the backend is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

The application uses the following environment variables:

### Required
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_TYPE`: Database type ('postgresql' or 'sqlite')

### PostgreSQL Configuration (if using PostgreSQL)
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_HOST`: PostgreSQL host
- `POSTGRES_PORT`: PostgreSQL port
- `POSTGRES_DB`: PostgreSQL database name
- `POSTGRES_URL`: PostgreSQL connection URL

### SQLite Configuration (if using SQLite)
- `SQLITE_URL`: SQLite connection URL (use `sqlite+aiosqlite:///:memory:` for in-memory database)

### Optional
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (debug/info/warning/error)

## Development Tools

### Database Migrations

The project uses Alembic for database migrations. To create and apply migrations:

1. Create a new migration:
   ```bash
   poetry run alembic revision --autogenerate -m "description of changes"
   ```

2. Apply migrations:
   ```bash
   poetry run alembic upgrade head
   ```

### Code Formatting

The project uses Black for Python code formatting and Prettier for frontend code:

```bash
# Format Python code
poetry run black .

# Format frontend code
cd frontend
npm run format
```

### Type Checking

The project uses mypy for Python type checking:

```bash
poetry run mypy .
```

## License

MIT 