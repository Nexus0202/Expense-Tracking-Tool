from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

# Single shared dependency — injects a DB session into any route that needs it
DbDep = Annotated[Session, Depends(get_db)]
