from sqlalchemy import Column, Integer, String, ForeignKey, Table, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base

# Association table for crew-agent relationship
crew_agent_association = Table(
    'crew_agent_association',
    Base.metadata,
    Column('crew_id', Integer, ForeignKey('crews.id')),
    Column('agent_id', Integer, ForeignKey('agents.id')),
)

class Crew(Base):
    __tablename__ = "crews"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    
    # Relationships
    agents = relationship("Agent", secondary=crew_agent_association, back_populates="crews")
    tasks = relationship("Task", back_populates="crew")
    executions = relationship("Execution", back_populates="crew")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, index=True)
    goal = Column(Text)
    backstory = Column(Text)
    verbose = Column(Boolean, default=True)
    llm_provider = Column(String, default="anthropic")  # anthropic, openai, or openai_compatible
    llm_model = Column(String, default="claude-3-haiku-20240307")  # model name/version
    llm_base_url = Column(String, nullable=True)  # for OpenAI-compatible APIs
    llm_api_key = Column(String, nullable=True)  # for custom API keys
    llm_api_version = Column(String, nullable=True)  # for OpenAI API version
    
    # Relationships
    crews = relationship("Crew", secondary=crew_agent_association, back_populates="agents")
    tasks = relationship("Task", back_populates="agent")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)
    expected_output = Column(Text, nullable=True)
    input_parameters = Column(Text, nullable=True)  # JSON string of input parameters
    context_variables = Column(Text, nullable=True)  # JSON string of context variables
    dependencies = Column(Text, nullable=True)  # JSON array of task IDs this task depends on
    output_variables = Column(Text, nullable=True)  # JSON string of output variables this task will produce
    
    # Foreign keys
    crew_id = Column(Integer, ForeignKey("crews.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    
    # Relationships
    crew = relationship("Crew", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks")

class Execution(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    crew_id = Column(Integer, ForeignKey("crews.id"))
    status = Column(String)  # "completed", "failed", "in_progress"
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    input_variables = Column(Text, nullable=True)  # JSON string of input variables
    task_params = Column(Text, nullable=True)  # JSON string of task parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    crew = relationship("Crew", back_populates="executions") 