from sqlmodel import SQLModel, Field, create_engine

class Bio(SQLModel, table=True):
    first_name: str = Field(primary_key=True)
    last_name: str = Field(primary_key=True)
    number: int | None = None
    position: str | None = None
    height: str | None = None
    weight: int | None = None
    age: int | None = None
    exp: int | None = None
    college: str | None = None

class Stats(SQLModel, table=True):
    # reference the lower‑case table name for Bio (SQLModel defaults to class name lowercase)
    first_name: str = Field(primary_key=True, foreign_key="bio.first_name")
    last_name: str = Field(primary_key=True, foreign_key="bio.last_name")
    ATT: int | None = None
    COMP: int | None = None
    YDS: int | None = None
    COMP_PER: float | None = None
    YDS_ATT: float | None = None
    TD: int | None = None
    TD_Per: float | None = None
    INT: int | None = None
    INT_Per: float | None = None
    LONG: int | None = None
    SCK: int | None = None
    SCK_LOST: int | None = None
    RATE: float | None = None
    REC: int | None = None
    ASSIST: int | None = None
    SFTY: int | None = None
    F: int | None = None

engine = create_engine('sqlite:///football.db')
SQLModel.metadata.create_all(engine)