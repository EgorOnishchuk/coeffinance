"""Person table created
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS person (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            gender VARCHAR(6) CHECK (gender IN ('male', 'female', 'other')) NOT NULL,
            birthdate DATE CHECK (birthdate < CURRENT_DATE) NOT NULL
        )
        """,
        "DROP TABLE IF EXISTS person",
    ),
]
