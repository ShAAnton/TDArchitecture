import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_tables import metadata

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)