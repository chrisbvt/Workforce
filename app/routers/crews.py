from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional, Dict, Any
from crewai import Crew, Agent, Task
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload
import os
import json
import uuid
from datetime import datetime, UTC

from app.database import get_db
from app.models import Crew as DBCrew, Agent as DBAgent, Task as DBTask, Execution as DBExecution
from app.tools import get_available_tools, TOOL_DESCRIPTIONS

router = APIRouter()

class LLMConfig(BaseModel):
    provider: str = "anthropic"  # anthropic, openai, or openai_compatible
    model: str = "claude-3-5-haiku-20241022"
    base_url: Optional[str] = None  # for OpenAI-compatible APIs
    api_key: Optional[str] = None
    api_version: Optional[str] = None  # for OpenAI API version

class AgentConfig(BaseModel):
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    llm_config: Optional[LLMConfig] = None
    allowed_tools: Optional[List[str]] = None

class ParameterDefinition(BaseModel):
    name: str
    description: str
    type: str = "string"  # string, number, boolean, etc.
    required: bool = True
    default: Optional[Any] = None

class TaskConfig(BaseModel):
    description: str
    agent_role: str
    expected_output: str
    input_parameters: Optional[Dict[str, Dict[str, Any]]] = None
    context_variables: Optional[Dict[str, Dict[str, Any]]] = None
    output_variables: Optional[Dict[str, Dict[str, Any]]] = None
    dependencies: Optional[List[str]] = None

class CrewConfig(BaseModel):
    name: str
    description: Optional[str] = None
    input_variables: Optional[Dict[str, Dict[str, Any]]] = None
    output_variables: Optional[Dict[str, Dict[str, Any]]] = None
    agents: List[AgentConfig]
    tasks: List[TaskConfig]

class TaskExecutionParams(BaseModel):
    input_parameters: Optional[Dict[str, Any]] = None
    context_variables: Optional[Dict[str, Any]] = None

class CrewExecutionParams(BaseModel):
    inputs: Optional[Dict[str, Any]] = None
    allowed_tools: Optional[List[str]] = None

@router.post("/")
async def create_crew(crew_config: CrewConfig, db: AsyncSession = Depends(get_db)):

    from pprint import pprint
    pprint(crew_config)
    try:
        print(f"Creating crew: {crew_config.name}")
        # Check if crew name already exists
        result = await db.execute(select(DBCrew).where(DBCrew.name == crew_config.name))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Crew name already exists")

        # Create crew
        db_crew = DBCrew(
            name=crew_config.name,
            description=crew_config.description
        )
        db.add(db_crew)
        await db.flush()
        print(f"Created crew with ID: {db_crew.id}")

        # Create agents
        agents = {}
        for agent_config in crew_config.agents:
            print(f"Creating agent with role: {agent_config.role}")
            llm_config = agent_config.llm_config or LLMConfig()
            db_agent = DBAgent(
                role=agent_config.role,
                goal=agent_config.goal,
                backstory=agent_config.backstory,
                verbose=agent_config.verbose,
                llm_provider=llm_config.provider,
                llm_model=llm_config.model,
                llm_base_url=llm_config.base_url,
                llm_api_key=llm_config.api_key,
                llm_api_version=llm_config.api_version,
                allowed_tools=json.dumps(agent_config.allowed_tools) if agent_config.allowed_tools else None
            )
            db.add(db_agent)
            await db.flush()
            print(f"Created agent with ID: {db_agent.id}")
            agents[agent_config.role] = db_agent

        # Create tasks
        task_map = {}  # Map to store task IDs for dependency resolution
        for task_config in crew_config.tasks:
            print(f"Creating task for agent role: {task_config.agent_role}")
            if task_config.agent_role not in agents:
                raise HTTPException(status_code=400, detail=f"Agent role {task_config.agent_role} not found")
            
            db_task = DBTask(
                description=task_config.description,
                expected_output=task_config.expected_output,
                input_parameters=json.dumps(task_config.input_parameters) if task_config.input_parameters else None,
                context_variables=json.dumps(task_config.context_variables) if task_config.context_variables else None,
                output_variables=json.dumps(task_config.output_variables) if task_config.output_variables else None,
                dependencies=json.dumps(task_config.dependencies) if task_config.dependencies else None,
                crew_id=db_crew.id,
                agent_id=agents[task_config.agent_role].id
            )
            db.add(db_task)
            await db.flush()
            task_map[task_config.description] = db_task.id
            print(f"Created task for agent {agents[task_config.agent_role].id}")

        # Add agents to crew using the association table directly
        for agent in agents.values():
            await db.execute(
                text("INSERT INTO crew_agent_association (crew_id, agent_id) VALUES (:crew_id, :agent_id)"),
                {"crew_id": db_crew.id, "agent_id": agent.id}
            )
            print(f"Added agent {agent.id} to crew {db_crew.id}")

        await db.commit()
        print("Successfully committed all changes")
        return {"message": f"Crew {crew_config.name} created successfully"}

    except Exception as e:
        print(f"Error creating crew: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_crews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBCrew))
    crews = result.scalars().all()
    return {"crews": [{"id": crew.id, "name": crew.name} for crew in crews]}

@router.get("/executions")
async def list_all_executions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBExecution, DBCrew.name.label('crew_name'))
        .join(DBCrew, DBExecution.crew_id == DBCrew.id)
        .order_by(DBExecution.created_at.desc())
    )
    executions = result.all()
    
    return {
        "executions": [
            {
                "id": execution.Execution.id,
                "crew_id": execution.Execution.crew_id,
                "crew_name": execution.crew_name,
                "status": execution.Execution.status,
                "result": json.loads(execution.Execution.result) if execution.Execution.result else None,
                "error": execution.Execution.error,
                "input_variables": json.loads(execution.Execution.input_variables) if execution.Execution.input_variables else None,
                "task_params": json.loads(execution.Execution.task_params) if execution.Execution.task_params else None,
                "created_at": execution.Execution.created_at.isoformat(),
                "completed_at": execution.Execution.completed_at.isoformat() if execution.Execution.completed_at else None
            } for execution in executions
        ]
    }

@router.get("/{crew_id}")
async def get_crew(crew_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBCrew)
        .where(DBCrew.id == crew_id)
        .options(
            selectinload(DBCrew.agents),
            selectinload(DBCrew.tasks)
        )
    )
    crew = result.scalar_one_or_none()
    
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    
    # Parse input and output variables from JSON strings
    input_variables = json.loads(crew.input_variables) if crew.input_variables else {}
    output_variables = json.loads(crew.output_variables) if crew.output_variables else {}
    
    return {
        "name": crew.name,
        "description": crew.description,
        "input_variables": input_variables,
        "output_variables": output_variables,
        "agents": [
            {
                "role": agent.role,
                "goal": agent.goal,
                "backstory": agent.backstory,
                "verbose": agent.verbose,
                "llm_config": {
                    "provider": agent.llm_provider,
                    "model": agent.llm_model,
                    "base_url": agent.llm_base_url,
                    "api_key": agent.llm_api_key,
                    "api_version": agent.llm_api_version
                },
                "allowed_tools": json.loads(agent.allowed_tools) if agent.allowed_tools else []
            } for agent in crew.agents
        ],
        "tasks": [
            {
                "description": task.description,
                "agent_role": task.agent.role,
                "expected_output": task.expected_output,
                "input_parameters": json.loads(task.input_parameters) if task.input_parameters else {},
                "context_variables": json.loads(task.context_variables) if task.context_variables else {},
                "output_variables": json.loads(task.output_variables) if task.output_variables else {},
                "dependencies": json.loads(task.dependencies) if task.dependencies else []
            } for task in crew.tasks
        ]
    }

@router.post("/{crew_id}/execute")
async def execute_crew(
    crew_id: int,
    execution_params: CrewExecutionParams,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DBCrew)
        .where(DBCrew.id == crew_id)
        .options(
            selectinload(DBCrew.agents),
            selectinload(DBCrew.tasks)
        )
    )
    crew = result.scalar_one_or_none()
    
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    
    # Create execution record
    execution = DBExecution(
        crew_id=crew_id,
        status="in_progress",
        input_variables=json.dumps(execution_params.inputs) if execution_params.inputs else None,
        task_params=json.dumps(execution_params.allowed_tools) if execution_params.allowed_tools else None
    )
    db.add(execution)
    await db.flush()

    try:
        # Get all available tools
        tools_dict = get_available_tools()

        # Create CrewAI agents
        crewai_agents = []
        for db_agent in crew.agents:
            # Configure LLM based on provider
            if db_agent.llm_provider == "anthropic":
                if db_agent.llm_api_key:
                    os.environ["ANTHROPIC_API_KEY"] = db_agent.llm_api_key
                from langchain_anthropic import ChatAnthropic
                llm = ChatAnthropic(model=db_agent.llm_model)
            elif db_agent.llm_provider == "openai":
                if db_agent.llm_api_key:
                    os.environ["OPENAI_API_KEY"] = db_agent.llm_api_key
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=db_agent.llm_model,
                    api_version=db_agent.llm_api_version
                )
            elif db_agent.llm_provider == "openai_compatible":
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=db_agent.llm_model,
                    base_url=db_agent.llm_base_url,
                    api_key=db_agent.llm_api_key,
                    api_version=db_agent.llm_api_version
                )

            # Filter tools based on allowed_tools
            agent_tools = []
            if db_agent.allowed_tools:
                allowed_tools = json.loads(db_agent.allowed_tools)
                for tool_name in allowed_tools:
                    if tool_name in tools_dict:
                        agent_tools.append(tools_dict[tool_name])

            # Create agent with tools and LLM
            agent = Agent(
                role=db_agent.role,
                goal=db_agent.goal,
                backstory=db_agent.backstory,
                verbose=db_agent.verbose,
                tools=agent_tools,  # Pass tools as a list
                llm=llm  # Pass the configured LLM instance
            )
            crewai_agents.append(agent)

        # Create CrewAI tasks
        crewai_tasks = []
        for db_task in crew.tasks:
            task = Task(
                description=db_task.description,
                agent=next(agent for agent in crewai_agents if agent.role == db_task.agent.role),
                expected_output=db_task.expected_output
            )
            crewai_tasks.append(task)

        # Create and execute crew
        crew = Crew(
            agents=crewai_agents,
            tasks=crewai_tasks,
            verbose=True
        )

        # Execute crew with input variables
        result = crew.kickoff(inputs=execution_params.inputs or {})

        # CrewOutput object structure:
        # - raw: str - The raw text output
        # - pydantic: Optional[Any] - Pydantic model if output was structured
        # - json_dict: Optional[Dict] - JSON representation if available
        # - tasks_output: List[TaskOutput] - List of individual task outputs
        #   - TaskOutput contains: description, name, expected_output, summary, raw, pydantic, json_dict, agent, output_format
        # - token_usage: UsageMetrics - Token usage statistics
        #   - UsageMetrics contains: total_tokens, prompt_tokens, cached_prompt_tokens, completion_tokens, successful_requests
        raw_output = result.raw if hasattr(result, 'raw') else str(result)

        # Update execution record
        execution.status = "completed"
        execution.result = json.dumps(result)
        execution.completed_at = datetime.now(UTC)
        await db.commit()

        return {"result": raw_output}

    except Exception as e:
        execution.status = "failed"
        execution.error = str(e)
        execution.completed_at = datetime.now(UTC)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{crew_id}/executions")
async def list_crew_executions(crew_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBExecution, DBCrew.name.label('crew_name'))
        .join(DBCrew, DBExecution.crew_id == DBCrew.id)
        .where(DBExecution.crew_id == crew_id)
        .order_by(DBExecution.created_at.desc())
    )
    executions = result.all()
    
    return {
        "executions": [
            {
                "id": execution.Execution.id,
                "crew_id": execution.Execution.crew_id,
                "crew_name": execution.crew_name,
                "status": execution.Execution.status,
                "result": json.loads(execution.Execution.result) if execution.Execution.result else None,
                "error": execution.Execution.error,
                "input_variables": json.loads(execution.Execution.input_variables) if execution.Execution.input_variables else None,
                "task_params": json.loads(execution.Execution.task_params) if execution.Execution.task_params else None,
                "created_at": execution.Execution.created_at.isoformat(),
                "completed_at": execution.Execution.completed_at.isoformat() if execution.Execution.completed_at else None
            } for execution in executions
        ]
    }

@router.delete("/{crew_id}")
async def delete_crew(crew_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBCrew).where(DBCrew.id == crew_id))
    crew = result.scalar_one_or_none()
    
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    
    await db.delete(crew)
    await db.commit()
    return {"message": f"Crew {crew.name} deleted successfully"}

@router.put("/{crew_id}")
async def update_crew(crew_id: int, crew_config: CrewConfig, db: AsyncSession = Depends(get_db)):
    try:
        # Check if crew exists
        result = await db.execute(select(DBCrew).where(DBCrew.id == crew_id))
        db_crew = result.scalar_one_or_none()
        if not db_crew:
            raise HTTPException(status_code=404, detail="Crew not found")

        # Check if new name conflicts with existing crew
        if crew_config.name != db_crew.name:
            result = await db.execute(select(DBCrew).where(DBCrew.name == crew_config.name))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Crew name already exists")

        # Update crew details
        db_crew.name = crew_config.name
        db_crew.description = crew_config.description
        db_crew.input_variables = json.dumps(crew_config.input_variables) if crew_config.input_variables else None
        db_crew.output_variables = json.dumps(crew_config.output_variables) if crew_config.output_variables else None

        # Delete existing agents and tasks
        await db.execute(text("DELETE FROM crew_agent_association WHERE crew_id = :crew_id"), {"crew_id": crew_id})
        await db.execute(text("DELETE FROM tasks WHERE crew_id = :crew_id"), {"crew_id": crew_id})
        await db.execute(text("DELETE FROM agents WHERE id IN (SELECT agent_id FROM crew_agent_association WHERE crew_id = :crew_id)"), {"crew_id": crew_id})

        # Create new agents
        agents = {}
        for agent_config in crew_config.agents:
            llm_config = agent_config.llm_config or LLMConfig()
            db_agent = DBAgent(
                role=agent_config.role,
                goal=agent_config.goal,
                backstory=agent_config.backstory,
                verbose=agent_config.verbose,
                llm_provider=llm_config.provider,
                llm_model=llm_config.model,
                llm_base_url=llm_config.base_url,
                llm_api_key=llm_config.api_key,
                llm_api_version=llm_config.api_version,
                allowed_tools=json.dumps(agent_config.allowed_tools) if agent_config.allowed_tools else None
            )
            db.add(db_agent)
            await db.flush()
            agents[agent_config.role] = db_agent

        # Create new tasks
        for task_config in crew_config.tasks:
            if task_config.agent_role not in agents:
                raise HTTPException(status_code=400, detail=f"Agent role {task_config.agent_role} not found")
            
            db_task = DBTask(
                description=task_config.description,
                expected_output=task_config.expected_output,
                input_parameters=json.dumps(task_config.input_parameters) if task_config.input_parameters else None,
                context_variables=json.dumps(task_config.context_variables) if task_config.context_variables else None,
                output_variables=json.dumps(task_config.output_variables) if task_config.output_variables else None,
                dependencies=json.dumps(task_config.dependencies) if task_config.dependencies else None,
                crew_id=crew_id,
                agent_id=agents[task_config.agent_role].id
            )
            db.add(db_task)

        # Add agents to crew
        for agent in agents.values():
            await db.execute(
                text("INSERT INTO crew_agent_association (crew_id, agent_id) VALUES (:crew_id, :agent_id)"),
                {"crew_id": crew_id, "agent_id": agent.id}
            )

        await db.commit()
        return {"message": f"Crew {crew_config.name} updated successfully"}

    except Exception as e:
        print(f"Error updating crew: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 