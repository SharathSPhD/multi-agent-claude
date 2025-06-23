"""
Test database models and schema
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from models import Base, Agent, Task, Execution, AgentCommunication
from datetime import datetime


class TestDatabaseModels:
    """Test database model creation and relationships"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_agent_model_creation(self, db_session):
        """Test Agent model creation"""
        agent = Agent(
            name="Test Agent",
            role="tester",
            system_prompt="You are a test agent",
            capabilities=["testing", "validation"],
            tools=["pytest", "unittest"],
            constraints=["test environment only"]
        )
        
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)
        
        assert agent.id is not None
        assert agent.name == "Test Agent"
        assert agent.role == "tester"
        assert agent.capabilities == ["testing", "validation"]
        assert agent.tools == ["pytest", "unittest"]
        assert agent.constraints == ["test environment only"]
        assert agent.created_at is not None

    def test_task_model_creation(self, db_session):
        """Test Task model creation"""
        task = Task(
            name="Test Task",
            description="A test task for validation",
            requirements=["requirement 1", "requirement 2"],
            expected_output="Test output",
            success_criteria=["criteria 1", "criteria 2"],
            priority=1
        )
        
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        assert task.id is not None
        assert task.name == "Test Task"
        assert task.description == "A test task for validation"
        assert task.requirements == ["requirement 1", "requirement 2"]
        assert task.expected_output == "Test output"
        assert task.success_criteria == ["criteria 1", "criteria 2"]
        assert task.priority == 1
        assert task.created_at is not None

    def test_execution_model_creation(self, db_session):
        """Test Execution model creation with enhanced fields"""
        # Create agent and task first
        agent = Agent(
            name="Test Agent",
            role="tester",
            system_prompt="Test prompt"
        )
        task = Task(
            name="Test Task",
            description="Test description"
        )
        
        db_session.add(agent)
        db_session.add(task)
        db_session.commit()
        
        execution = Execution(
            agent_id=agent.id,
            task_id=task.id,
            status="pending",
            work_directory="/tmp/test",
            agent_response={"result": "test", "status": "completed"},
            needs_interaction=False
        )
        
        db_session.add(execution)
        db_session.commit()
        db_session.refresh(execution)
        
        assert execution.id is not None
        assert execution.agent_id == agent.id
        assert execution.task_id == task.id
        assert execution.status == "pending"
        assert execution.work_directory == "/tmp/test"
        assert execution.agent_response == {"result": "test", "status": "completed"}
        assert execution.needs_interaction is False
        assert execution.created_at is not None

    def test_agent_communication_model_creation(self, db_session):
        """Test AgentCommunication model creation"""
        # Create agents first
        sender = Agent(name="Sender Agent", role="sender", system_prompt="Sender")
        receiver = Agent(name="Receiver Agent", role="receiver", system_prompt="Receiver")
        
        db_session.add(sender)
        db_session.add(receiver)
        db_session.commit()
        
        communication = AgentCommunication(
            sender_id=sender.id,
            receiver_id=receiver.id,
            message="Test message",
            message_type="info",
            context={"test": "context"}
        )
        
        db_session.add(communication)
        db_session.commit()
        db_session.refresh(communication)
        
        assert communication.id is not None
        assert communication.sender_id == sender.id
        assert communication.receiver_id == receiver.id
        assert communication.message == "Test message"
        assert communication.message_type == "info"
        assert communication.context == {"test": "context"}
        assert communication.timestamp is not None

    def test_agent_execution_relationship(self, db_session):
        """Test Agent-Execution relationship"""
        agent = Agent(
            name="Test Agent",
            role="tester",
            system_prompt="Test prompt"
        )
        task = Task(
            name="Test Task",
            description="Test description"
        )
        
        db_session.add(agent)
        db_session.add(task)
        db_session.commit()
        
        execution = Execution(
            agent_id=agent.id,
            task_id=task.id,
            status="pending"
        )
        
        db_session.add(execution)
        db_session.commit()
        
        # Test relationship access
        assert execution.agent.name == "Test Agent"
        assert execution.task.name == "Test Task"

    def test_execution_status_updates(self, db_session):
        """Test execution status updates"""
        agent = Agent(name="Test Agent", role="tester", system_prompt="Test")
        task = Task(name="Test Task", description="Test")
        
        db_session.add(agent)
        db_session.add(task)
        db_session.commit()
        
        execution = Execution(
            agent_id=agent.id,
            task_id=task.id,
            status="pending"
        )
        
        db_session.add(execution)
        db_session.commit()
        
        # Update status
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        db_session.commit()
        
        assert execution.status == "running"
        assert execution.started_at is not None
        
        # Complete execution
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        execution.agent_response = {"result": "success"}
        db_session.commit()
        
        assert execution.status == "completed"
        assert execution.completed_at is not None
        assert execution.agent_response["result"] == "success"

    def test_json_field_serialization(self, db_session):
        """Test JSON field serialization/deserialization"""
        agent = Agent(
            name="JSON Test Agent",
            role="tester",
            system_prompt="Test",
            capabilities=["json", "testing"],
            tools=["tool1", "tool2"],
            constraints=["constraint1"]
        )
        
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)
        
        # Test that JSON fields are properly serialized
        assert isinstance(agent.capabilities, list)
        assert agent.capabilities == ["json", "testing"]
        assert isinstance(agent.tools, list)
        assert agent.tools == ["tool1", "tool2"]

    def test_execution_error_handling(self, db_session):
        """Test execution with error information"""
        agent = Agent(name="Error Agent", role="tester", system_prompt="Test")
        task = Task(name="Error Task", description="Test")
        
        db_session.add(agent)
        db_session.add(task)
        db_session.commit()
        
        execution = Execution(
            agent_id=agent.id,
            task_id=task.id,
            status="failed",
            error_message="Test error occurred",
            agent_response={"error": "JSON parsing failed", "partial_result": "Some data"}
        )
        
        db_session.add(execution)
        db_session.commit()
        db_session.refresh(execution)
        
        assert execution.status == "failed"
        assert execution.error_message == "Test error occurred"
        assert "error" in execution.agent_response
        assert "partial_result" in execution.agent_response

    def test_work_directory_field(self, db_session):
        """Test work_directory field functionality"""
        agent = Agent(name="Dir Agent", role="tester", system_prompt="Test")
        task = Task(name="Dir Task", description="Test")
        
        db_session.add(agent)
        db_session.add(task)
        db_session.commit()
        
        execution = Execution(
            agent_id=agent.id,
            task_id=task.id,
            status="pending",
            work_directory="/custom/work/directory"
        )
        
        db_session.add(execution)
        db_session.commit()
        db_session.refresh(execution)
        
        assert execution.work_directory == "/custom/work/directory"

    def test_needs_interaction_field(self, db_session):
        """Test needs_interaction field functionality"""
        agent = Agent(name="Interactive Agent", role="tester", system_prompt="Test")
        task = Task(name="Interactive Task", description="Test")
        
        db_session.add(agent)
        db_session.add(task)
        db_session.commit()
        
        execution = Execution(
            agent_id=agent.id,
            task_id=task.id,
            status="waiting_for_input",
            needs_interaction=True
        )
        
        db_session.add(execution)
        db_session.commit()
        db_session.refresh(execution)
        
        assert execution.needs_interaction is True
        assert execution.status == "waiting_for_input"