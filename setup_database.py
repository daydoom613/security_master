"""
Database setup script for AlfaGrow Security Service
"""
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import settings

logger = logging.getLogger(__name__)


def setup_database():
    """Setup database tables and indexes"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read and execute SQL file
        with open('migrations/init_security_table.sql', 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script
        cursor.execute(sql_script)
        
        logger.info("✅ Database setup completed successfully")
        
        # Test the setup
        cursor.execute("SELECT COUNT(*) FROM securities")
        count = cursor.fetchone()[0]
        logger.info(f"✅ Securities table created with {count} records")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if setup_database():
        print("✅ Database setup completed successfully")
    else:
        print("❌ Database setup failed")
        exit(1)
