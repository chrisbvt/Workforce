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
from datetime import datetime

from app.database import get_db
from app.models import Crew as DBCrew, Agent as DBAgent, Task as DBTask, Execution as DBExecution

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

class ParameterDefinition(BaseModel):
    name: str
    description: str
    type: str = "string"  # string, number, boolean, etc.
    required: bool = True
    default: Optional[Any] = None

class TaskConfig(BaseModel):
    description: str
    agent_role: str
    expected_output: Optional[str] = None
    input_parameters: Optional[Dict[str, ParameterDefinition]] = None  # Task-specific input parameters
    context_variables: Optional[Dict[str, ParameterDefinition]] = None  # Task-specific context variables
    dependencies: Optional[List[int]] = None  # List of task IDs this task depends on
    output_variables: Optional[Dict[str, ParameterDefinition]] = None  # Variables this task will produce

class CrewConfig(BaseModel):
    name: str
    description: str
    agents: List[AgentConfig]
    tasks: List[TaskConfig]
    input_variables: Optional[Dict[str, ParameterDefinition]] = None  # Crew-level input variables
    output_variables: Optional[Dict[str, ParameterDefinition]] = None  # Crew-level output variables

class TaskExecutionParams(BaseModel):
    input_parameters: Optional[Dict[str, Any]] = None
    context_variables: Optional[Dict[str, Any]] = None

class CrewExecutionParams(BaseModel):
    input_variables: Optional[Dict[str, Any]] = None  # Crew-level input variables
    task_params: Optional[Dict[str, TaskExecutionParams]] = None  # Map of task_id to parameters

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
                llm_api_version=llm_config.api_version
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
                input_parameters=json.dumps({k: v.dict() for k, v in task_config.input_parameters.items()}) if task_config.input_parameters else None,
                context_variables=json.dumps({k: v.dict() for k, v in task_config.context_variables.items()}) if task_config.context_variables else None,
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
    
    return {
        "id": crew.id,
        "name": crew.name,
        "description": crew.description,
        "agents": [
            {
                "id": agent.id,
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
                }
            } for agent in crew.agents
        ],
        "tasks": [
            {
                "id": task.id,
                "description": task.description,
                "expected_output": task.expected_output,
                "agent_role": task.agent.role,
                "input_parameters": json.loads(task.input_parameters) if task.input_parameters else {},
                "context_variables": json.loads(task.context_variables) if task.context_variables else {},
                "dependencies": json.loads(task.dependencies) if task.dependencies else []
            } for task in crew.tasks
        ]
    }

@router.post("/{crew_id}/execute")
async def execute_crew(
    crew_id: int,
    execution_params: Optional[CrewExecutionParams] = None,
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
        input_variables=json.dumps(execution_params.input_variables) if execution_params and execution_params.input_variables else None,
        task_params=json.dumps({k: v.dict() for k, v in execution_params.task_params.items()}) if execution_params and execution_params.task_params else None
    )
    db.add(execution)
    await db.flush()
    
    try:
        # Create CrewAI agents with configured LLM
        agents = {}
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

            print(f"Creating agent with LLM: {llm}")
            agent = Agent(
                role=db_agent.role,
                goal=db_agent.goal,
                backstory=db_agent.backstory,
                verbose=db_agent.verbose,
                llm=llm
            )
            agents[db_agent.role] = agent

        # Create CrewAI tasks
        tasks = []
        task_outputs = {}  # Store outputs from each task
        
        # First pass: Create all tasks
        for db_task in crew.tasks:
            # Get task-specific parameters if provided
            task_params = None
            if execution_params and execution_params.task_params:
                task_params = execution_params.task_params.get(str(db_task.id))

            # Load parameter definitions
            input_param_defs = json.loads(db_task.input_parameters) if db_task.input_parameters else {}
            context_var_defs = json.loads(db_task.context_variables) if db_task.context_variables else {}
            output_var_defs = json.loads(db_task.output_variables) if db_task.output_variables else {}

            # Validate and prepare parameters
            validated_input_params = {}
            validated_context_vars = {}

            # Add crew-level input variables to context
            if execution_params and execution_params.input_variables:
                for var_name, var_value in execution_params.input_variables.items():
                    validated_context_vars[f"crew_{var_name}"] = var_value

            # Add outputs from dependent tasks to context
            if db_task.dependencies:
                for dep_id in db_task.dependencies:
                    if dep_id in task_outputs:
                        for var_name, var_value in task_outputs[dep_id].items():
                            validated_context_vars[f"task_{dep_id}_{var_name}"] = var_value

            if task_params:
                # Validate input parameters
                if task_params.input_parameters:
                    for param_name, param_value in task_params.input_parameters.items():
                        if param_name not in input_param_defs:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Unknown input parameter '{param_name}' for task {db_task.id}"
                            )
                        param_def = input_param_defs[param_name]
                        validated_input_params[param_name] = param_value

                # Validate context variables
                if task_params.context_variables:
                    for var_name, var_value in task_params.context_variables.items():
                        if var_name not in context_var_defs:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Unknown context variable '{var_name}' for task {db_task.id}"
                            )
                        var_def = context_var_defs[var_name]
                        validated_context_vars[var_name] = var_value

            # Use default values for missing required parameters
            for param_name, param_def in input_param_defs.items():
                if param_name not in validated_input_params:
                    if param_def.get("required", True) and "default" not in param_def:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Missing required input parameter '{param_name}' for task {db_task.id}"
                        )
                    validated_input_params[param_name] = param_def.get("default")

            for var_name, var_def in context_var_defs.items():
                if var_name not in validated_context_vars:
                    if var_def.get("required", True) and "default" not in var_def:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Missing required context variable '{var_name}' for task {db_task.id}"
                        )
                    validated_context_vars[var_name] = var_def.get("default")

            # Prepare task description with validated parameters
            description = db_task.description
            if validated_input_params:
                for param_name, param_value in validated_input_params.items():
                    description = description.replace(f"{{{param_name}}}", str(param_value))
            
            if validated_context_vars:
                for var_name, var_value in validated_context_vars.items():
                    description = description.replace(f"{{{var_name}}}", str(var_value))

            # Create the task with the enhanced description
            task = Task(
                description=description,
                agent=agents[db_task.agent.role],
                expected_output=db_task.expected_output,
                context=[f"{k}: {v}" for k, v in validated_context_vars.items()] if validated_context_vars else None
            )
            tasks.append((db_task.id, task, output_var_defs))

        # Second pass: Execute tasks in order of dependencies
        final_outputs = {}
        for task_id, task, output_vars in tasks:
            result = task.execute()
            
            # Parse and store task outputs
            if output_vars:
                task_outputs[task_id] = {}
                # Here you would parse the result to extract the output variables
                # This is a simple example - you might want more sophisticated parsing
                for var_name in output_vars:
                    # Look for the variable in the result
                    # This is a simple example - you might want more sophisticated parsing
                    if f"{var_name}:" in result:
                        value = result.split(f"{var_name}:")[1].split("\n")[0].strip()
                        task_outputs[task_id][var_name] = value
                        final_outputs[f"task_{task_id}_{var_name}"] = value

        # Update execution record with success
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        execution.result = json.dumps({
            "result": result,
            "outputs": final_outputs
        })
        await db.commit()

        return {
            "id": execution.id,
            "result": result,
            "outputs": final_outputs
        }
    except Exception as e:
        # Update execution record with error
        execution.status = "failed"
        execution.completed_at = datetime.utcnow()
        execution.error = str(e)
        await db.commit()
        print(f"Error executing crew: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{crew_id}/executions")
async def list_crew_executions(crew_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DBExecution)
        .where(DBExecution.crew_id == crew_id)
        .order_by(DBExecution.created_at.desc())
    )
    executions = result.scalars().all()
    
    return {
        "executions": [
            {
                "id": execution.id,
                "status": execution.status,
                "result": json.loads(execution.result) if execution.result else None,
                "error": execution.error,
                "input_variables": json.loads(execution.input_variables) if execution.input_variables else None,
                "task_params": json.loads(execution.task_params) if execution.task_params else None,
                "created_at": execution.created_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
            } for execution in executions
        ]
    }

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

@router.delete("/{crew_id}")
async def delete_crew(crew_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBCrew).where(DBCrew.id == crew_id))
    crew = result.scalar_one_or_none()
    
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    
    await db.delete(crew)
    await db.commit()
    return {"message": f"Crew {crew.name} deleted successfully"} 