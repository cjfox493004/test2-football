import pandas as pd
from sqlmodel import Session, select
from models import engine, Bio, Stats

with Session(engine) as session:
    statement = (
        select(Bio.first_name, Bio.last_name, Bio.position, Bio.weight)
        .where(Bio.last_name.like('S%'))
    )
    records = session.exec(statement).all()

records_df = pd.DataFrame(records)
print(records_df)
