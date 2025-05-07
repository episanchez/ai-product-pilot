from pydantic import BaseModel, Field


class FeedbackResponse(BaseModel):
        id: str = Field(description="Titre concis de la user story")
        title: str = Field(description="Titre concis de la user story")
        description: str = Field(description="Titre concis de la user story")
        source: str = Field(description="Titre concis de la user story")
        file_path: str = Field(description="Titre concis de la user story")
        content: str = Field(description="Titre concis de la user story")
        status: str = Field(description="Titre concis de la user story")