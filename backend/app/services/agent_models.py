import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator

# FIX: Groq strict mode ke liye Flat Schema
class LLMDecisionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    tool: Literal["send_email", "assign_task", "update_database"]
    reason: str = Field(..., min_length=10)
    
    # FIX: Changed to Field(...) to make them required in JSON schema
    recipient: Optional[EmailStr] = Field(..., description="Required if tool=send_email, else null.")
    subject: Optional[str] = Field(..., description="Required if tool=send_email, else null.")
    body: Optional[str] = Field(..., description="Required if tool=send_email, else null.")
    
    role: Optional[str] = Field(..., description="Required if tool=assign_task, else null.")
    description: Optional[str] = Field(..., description="Required if tool=assign_task, else null.")
    
    field: Optional[str] = Field(..., description="Required if tool=update_database, else null.")
    new_value: Optional[str] = Field(..., description="Required if tool=update_database, else null.")
    
    @model_validator(mode="after")
    def validate_tool_params(self):
        if self.tool == "send_email":
            if not self.recipient or not self.subject or not self.body:
                raise ValueError("recipient, subject, and body are required for send_email")
        elif self.tool == "assign_task":
            if not self.role or not self.description:
                raise ValueError("role and description are required for assign_task")
        elif self.tool == "update_database":
            if not self.field or not self.new_value:
                raise ValueError("field and new_value are required for update_database")
        return self
# 3. Coordinator Schemas
class SubTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: Literal["info_request", "exception_handling"]
    description: str

class CoordinatorPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reasoning: str
    subtasks: list[SubTask]

# 4. Backend State Object
class ProposedAction(BaseModel):
    action_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    action: LLMDecisionOutput
    agent_source: str = Field(default="Coordinator")
    subtask_id: Optional[str] = None
    evidence: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)