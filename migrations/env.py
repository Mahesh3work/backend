from alembic import context
from sqlalchemy import create_engine

db_url = context.get_x_argument(as_dictionary=True).get('db_url', 'mysql+mysqlconnector://root:demo123!@127.0.0.1:3306/demo_pmd')

engine = create_engine(db_url)

with engine.connect() as connection:
    context.configure(connection=connection)

    with context.begin_transaction():
        context.run_migrations()