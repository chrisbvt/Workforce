"""update crew id to uuid

Revision ID: update_crew_id_to_uuid
Revises: 
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = 'update_crew_id_to_uuid'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create a new UUID column in crews table
    op.add_column('crews', sa.Column('uuid_id', UUID(as_uuid=True), nullable=True))
    
    # Generate UUIDs for existing rows
    connection = op.get_bind()
    crews = connection.execute('SELECT id FROM crews').fetchall()
    for crew in crews:
        connection.execute(
            'UPDATE crews SET uuid_id = %s WHERE id = %s',
            (uuid.uuid4(), crew[0])
        )
    
    # Make the UUID column not nullable
    op.alter_column('crews', 'uuid_id', nullable=False)
    
    # Drop the old primary key constraint
    op.drop_constraint('crews_pkey', 'crews', type_='primary')
    
    # Drop the old id column
    op.drop_column('crews', 'id')
    
    # Rename uuid_id to id
    op.alter_column('crews', 'uuid_id', new_column_name='id')
    
    # Add new primary key constraint
    op.create_primary_key('crews_pkey', 'crews', ['id'])
    
    # Update crew_agent_association table
    op.add_column('crew_agent_association', sa.Column('uuid_crew_id', UUID(as_uuid=True), nullable=True))
    
    # Copy crew IDs from crews table
    connection.execute('''
        UPDATE crew_agent_association 
        SET uuid_crew_id = crews.id 
        FROM crews 
        WHERE crew_agent_association.crew_id = crews.id::text
    ''')
    
    # Drop old foreign key constraint
    op.drop_constraint('crew_agent_association_crew_id_fkey', 'crew_agent_association', type_='foreignkey')
    
    # Drop old crew_id column
    op.drop_column('crew_agent_association', 'crew_id')
    
    # Rename uuid_crew_id to crew_id
    op.alter_column('crew_agent_association', 'uuid_crew_id', new_column_name='crew_id')
    
    # Add new foreign key constraint
    op.create_foreign_key(
        'crew_agent_association_crew_id_fkey',
        'crew_agent_association',
        'crews',
        ['crew_id'],
        ['id']
    )
    
    # Update tasks table
    op.add_column('tasks', sa.Column('uuid_crew_id', UUID(as_uuid=True), nullable=True))
    
    # Copy crew IDs from crews table
    connection.execute('''
        UPDATE tasks 
        SET uuid_crew_id = crews.id 
        FROM crews 
        WHERE tasks.crew_id = crews.id::text
    ''')
    
    # Drop old foreign key constraint
    op.drop_constraint('tasks_crew_id_fkey', 'tasks', type_='foreignkey')
    
    # Drop old crew_id column
    op.drop_column('tasks', 'crew_id')
    
    # Rename uuid_crew_id to crew_id
    op.alter_column('tasks', 'uuid_crew_id', new_column_name='crew_id')
    
    # Add new foreign key constraint
    op.create_foreign_key(
        'tasks_crew_id_fkey',
        'tasks',
        'crews',
        ['crew_id'],
        ['id']
    )

def downgrade():
    # This is a complex migration that changes primary keys and foreign keys
    # Downgrading would require careful handling of data and constraints
    # It's recommended to backup the database before running this migration
    pass 