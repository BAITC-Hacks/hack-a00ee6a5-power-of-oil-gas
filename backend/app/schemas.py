from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator

CARD_FIELDS = [
    "title",
    "context",
    "need",
    "users",
    "data_materials",
    "constraints",
    "expected_result",
    "success_criteria",
    "contact",
    "interaction_format",
]


class ChallengeCreate(BaseModel):
    raw_description: str = Field(min_length=10, max_length=4000)
    industry: str = Field(default="Other", min_length=2, max_length=120)


class AIAnalysis(BaseModel):
    extracted_fields: dict[str, Optional[str]] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[str] = Field(min_length=3)

    @field_validator("questions")
    @classmethod
    def at_least_three_questions(cls, value: list[str]):
        cleaned = [q.strip() for q in value if q and q.strip()]
        if len(cleaned) < 3:
            raise ValueError("AI must return at least 3 questions")
        return cleaned[:7]


class AnswerItem(BaseModel):
    question: str = Field(min_length=3, max_length=600)
    answer: str = Field(min_length=1, max_length=3000)


class BuildCardRequest(BaseModel):
    answers: list[AnswerItem] = Field(min_length=3)


class ChallengeCardDraft(BaseModel):
    title: Optional[str] = None
    context: Optional[str] = None
    need: Optional[str] = None
    users: Optional[str] = None
    data_materials: Optional[str] = None
    constraints: Optional[str] = None
    expected_result: Optional[str] = None
    success_criteria: Optional[str] = None
    contact: Optional[str] = None
    interaction_format: Optional[str] = None


class ChallengeConfirm(ChallengeCardDraft):
    confirmed: bool

    @field_validator("confirmed")
    @classmethod
    def must_be_confirmed(cls, value: bool):
        if value is not True:
            raise ValueError("Human confirmation is required")
        return value


class ProposalCreate(BaseModel):
    challenge_id: int
    team_id: Optional[int] = None
    team_name: str = Field(min_length=2, max_length=120)
    solution_idea: str = Field(min_length=10, max_length=4000)
    plan: str = Field(min_length=10, max_length=4000)
    deadline: str = Field(min_length=2, max_length=120)
    prototype_url: str = Field(min_length=3, max_length=600)


class ProposalDecision(BaseModel):
    decision: Literal["accepted", "rejected"]
