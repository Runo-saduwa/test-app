import uuid
from sqlalchemy import (
    Column, String, Text, ForeignKey, Boolean, Integer, DateTime, JSON, 
    DECIMAL, Float, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

# Users Table
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("TeamMembership", back_populates="user")

    __table_args__ = (
        Index('ix_users_created_at', 'created_at'),
    )

# Companies Table
class Company(Base):
    __tablename__ = "companies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="company")
    members = relationship("TeamMembership", back_populates="company")
    subscription = relationship('Subscription', back_populates="company", uselist=False)

    __table_args__ = (
        Index('ix_companies_created_at', 'created_at'),
    )

# Team Memberships Table
class TeamMembership(Base):
    __tablename__ = "team_memberships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memberships")
    company = relationship("Company", back_populates="members")
    role = relationship('Role', back_populates="members")

    __table_args__ = (
        Index('ix_team_memberships_user_company', 'user_id', 'company_id'),
        Index('ix_team_memberships_role_id', 'role_id'),
    )

# Roles Table
class Role(Base):
    __tablename__ = "roles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)

    permissions = relationship("RolePermission", back_populates="role")
    members = relationship('TeamMembership', back_populates="role")

# Role Permissions Table
class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission = Column(String, nullable=False)

    role = relationship("Role", back_populates="permissions")

    __table_args__ = (
        Index('ix_role_permissions_role_id', 'role_id'),
    )

# Subscription Plans Table
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    price = Column(DECIMAL, nullable=False)
    features = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subscriptions = relationship('Subscription', back_populates="subscription_plan")

    __table_args__ = (
        Index('ix_subscription_plans_name', 'name'),
    )

# Subscriptions Table
class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    subscription_plan_id = Column(UUID(as_uuid=True), ForeignKey('subscription_plans.id'), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    
    company = relationship('Company', back_populates="subscription")
    subscription_plan = relationship('SubscriptionPlan', back_populates="subscriptions")

    __table_args__ = (
        Index('ix_subscriptions_company_id', 'company_id'),
        Index('ix_subscriptions_subscription_plan_id', 'subscription_plan_id'),
    )

# Projects Table
class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    base_url = Column(String, nullable=False)  # Base URL for the project
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="projects")
    test_suites = relationship("TestSuite", back_populates="project")

    __table_args__ = (
        Index('ix_projects_company_id', 'company_id'),
    )

# Test Suites Table
class TestSuite(Base):
    __tablename__ = "test_suites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="test_suites")
    test_cases = relationship("TestCase", back_populates="suite")

    __table_args__ = (
        Index('ix_test_suites_project_id', 'project_id'),
    )

# Test Cases Table
class TestCase(Base):
    __tablename__ = "test_cases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_story = Column(Text, nullable=True)  # Original user story/requirements
    suite_id = Column(UUID(as_uuid=True), ForeignKey("test_suites.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Test configuration
    test_data = Column(JSON, nullable=True)  # Input data for the test
    environment_vars = Column(JSON, nullable=True)  # Environment-specific variables
    
    suite = relationship("TestSuite", back_populates="test_cases")
    steps = relationship("TestStep", back_populates="test_case", order_by="TestStep.order")
    runs = relationship("TestCaseRun", back_populates="test_case")

    __table_args__ = (
        Index('ix_test_cases_suite_id', 'suite_id'),
    )

# Test Steps Table
class TestStep(Base):
    __tablename__ = "test_steps"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False)
    order = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    step_type = Column(String, nullable=False)  # 'navigation', 'input', 'click', 'assertion', 'custom'
    
    # Step-specific code and data
    automation_code = Column(Text, nullable=False)  # Only this step's code
    input_data = Column(JSON, nullable=True)  # Step-specific input data
    expected_result = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    test_case = relationship("TestCase", back_populates="steps")
    results = relationship("TestStepResult", back_populates="step")

    __table_args__ = (
        Index('ix_test_steps_test_case_id', 'test_case_id'),
    )

# Test Case Runs Table
class TestCaseRun(Base):
    __tablename__ = "test_case_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False)
    status = Column(String, nullable=False, server_default='pending')  # 'pending', 'passed', 'failed'
    
    # Execution metrics
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_duration = Column(Float, nullable=True)  # in seconds
    total_steps = Column(Integer, nullable=False)
    passed_steps = Column(Integer, nullable=True)
    failed_steps = Column(Integer, nullable=True)
    
    # Environment info
    browser_info = Column(JSON, nullable=True)
    environment_info = Column(JSON, nullable=True)
    
    test_case = relationship("TestCase", back_populates="runs")
    step_results = relationship("TestStepResult", back_populates="test_run")

    __table_args__ = (
        Index('ix_test_case_runs_test_case_id', 'test_case_id'),
    )

# Test Step Results Table
class TestStepResult(Base):
    __tablename__ = "test_step_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_case_runs.id"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("test_steps.id"), nullable=False)
    status = Column(String, nullable=False)  # 'pending', 'passed', 'failed'
    
    # Execution details
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    
    # Results
    error_message = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    logs = Column(Text, nullable=True)
    
    test_run = relationship("TestCaseRun", back_populates="step_results")
    step = relationship("TestStep", back_populates="results")

    __table_args__ = (
        Index('ix_test_step_results_test_run_id', 'test_run_id'),
        Index('ix_test_step_results_step_id', 'step_id'),
    )