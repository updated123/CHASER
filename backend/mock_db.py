"""
Mock database session - returns None, all data comes from MockDataService
"""
from typing import Generator

class MockSession:
    """Mock database session that does nothing"""
    def query(self, *args, **kwargs):
        return MockQuery()
    
    def add(self, *args, **kwargs):
        pass
    
    def commit(self, *args, **kwargs):
        pass
    
    def close(self, *args, **kwargs):
        pass

class MockQuery:
    """Mock query object"""
    def filter(self, *args, **kwargs):
        return self
    
    def filter_by(self, *args, **kwargs):
        return self
    
    def join(self, *args, **kwargs):
        return self
    
    def all(self):
        return []
    
    def first(self):
        return None
    
    def count(self):
        return 0

def get_db() -> Generator:
    """Mock database dependency - returns mock session"""
    db = MockSession()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Mock init - does nothing"""
    pass

