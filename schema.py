# schema.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class AppResearchResult(BaseModel):
    app_name: str = Field(..., description="The standard name of the application")
    category: str = Field(..., description="The target marketplace classification category")
    one_liner: str = Field(..., description="A clear, precise one-line definition of what the app does")
    auth_methods: List[Literal["OAuth2", "API Key", "Basic", "Token", "Other", "None"]] = Field(
        ..., description="List of supported developer authentication methods"
    )
    accessibility: Literal["Self-Serve", "Gated"] = Field(
        ..., description="Self-Serve (instant free access/trial credentials) vs Gated (needs sales team, paid setup, or manual approval)"
    )
    api_surface: str = Field(..., description="Details on the footprint: e.g., 'Public REST API', 'GraphQL API', 'No Public API'")
    has_mcp_server: bool = Field(..., description="True if a public MCP server is known to exist for this application")
    buildability_verdict: Literal["Immediate Win", "Blocked"] = Field(
        ..., description="Can an engineer turn this into an automated agent toolkit today?"
    )
    primary_blocker: Optional[str] = Field(None, description="The primary blocker if marked as Blocked")
    evidence_url: str = Field(..., description="The direct URL link targeting the developer documentation page used as source truth")
    pass1_accuracy_delta: Optional[bool] = Field(False, description="True if the Pass 2 Verification loop had to correct errors from Pass 1")