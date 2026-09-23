from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator, ConfigDict

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


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')


class ChallengeCreate(InputModel):
    raw_description: str = Field(min_length=10, max_length=4000)
    industry: str = Field(default="Other", min_length=2, max_length=120)


class Clarification(InputModel):
    language: Literal['kk','ru','en'] = 'ru'
    question_translations: dict[str,str] = Field(default_factory=dict)
    field: str
    question: str
    hint: str = ''
    reason: str = ''
    points: int = 0


class AIAnalysis(BaseModel):
    extracted_fields: dict[str, Optional[str]] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[Clarification] = Field(min_length=3, max_length=10)


class AnswerItem(InputModel):
    field: Optional[str] = None
    question: str = Field(min_length=3, max_length=600)
    answer: str = Field(min_length=1, max_length=3000)


class BuildCardRequest(InputModel):
    answers: list[AnswerItem] = Field(min_length=3, max_length=10)


class ChallengeCardDraft(InputModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid', str_max_length=4000)
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
    assessment_id: int
    title: str = Field(min_length=3, max_length=180)
    confirmed: bool

    @field_validator("confirmed")
    @classmethod
    def must_be_confirmed(cls, value: bool):
        if value is not True:
            raise ValueError("Human confirmation is required")
        return value


class ProposalCreate(InputModel):
    challenge_id: int
    team_id: Optional[int] = None
    team_name: str = Field(min_length=2, max_length=120)
    solution_idea: str = Field(min_length=10, max_length=4000)
    plan: str = Field(min_length=10, max_length=4000)
    deadline: str = Field(min_length=2, max_length=120)
    prototype_url: str = Field(min_length=3, max_length=600)

    @field_validator('prototype_url')
    @classmethod
    def safe_url(cls, value):
        return str(HttpUrl(value))


class ProposalDecision(BaseModel):
    decision: Literal["accepted", "rejected"]


class MilestoneConfirm(InputModel):
    stage: Literal['discovery', 'prototype', 'validation']
    points: int = Field(strict=True, ge=0, le=50)
    evidence: str = Field(min_length=10, max_length=2000)
    confirmed: Literal[True]

    @model_validator(mode='after')
    def stage_score_limit(self):
        maximum = {'discovery':20, 'prototype':30, 'validation':50}[self.stage]
        if self.points > maximum:
            raise ValueError(f'Score must be between 0 and {maximum}')
        return self
