from pydantic import BaseModel


class LibSettings(BaseModel):
    # Cant think of any library-specific properties lol
    test_prop: bool = False
