import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator


class LLMDecisionOutput(BaseModel):
    """
    Flat schema that Groq can easily validate.
    All fields are required in the JSON schema, but we enforce logic via model_validator.
    """
    model_config = ConfigDict(extra="forbid")
    
    tool: Literal["send_email", "assign_task", "update_database"]
    reason: str = Field(..., min_length=10, description="Why this action was chosen")
    
    # Email params
    recipient: EmailStr | None = Field(..., description="Valid email address. Required if tool=send_email, else null.")
    subject: str | None = Field(..., description="Email subject. Required if tool=send_email, else null.")
    body: str | None = Field(..., description="Email body. Required if tool=send_email, else null.")
    
    # Task params
    role: str | None = Field(..., description="Role to assign. Required if tool=assign_task, else null.")
    description: str | None = Field(..., description="Task description. Required if tool=assign_task, else null.")
    
    # DB params
    field: str | None = Field(..., description="Field to update. Required if tool=update_database, else null.")
    new_value: str | None = Field(..., description="New value. Required if tool=update_database, else null.")
    
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


class ProposedAction(BaseModel):
    """
    Created by the BACKEND. Wraps the LLM decision with a unique action_id.
    """
    action_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    action: LLMDecisionOutput
    created_at: datetime = Field(default_factory=datetime.utcnow)