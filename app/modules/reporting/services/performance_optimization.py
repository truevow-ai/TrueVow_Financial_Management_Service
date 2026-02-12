"""Performance Optimization Service - Indexing Review"""
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from app.core.database import engine


class PerformanceOptimizationService:
    """Service for performance optimization and indexing review"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.engine = engine
    
    async def review_indexes(self) -> Dict:
        """Review database indexes and suggest optimizations"""
        # Get all tables
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        index_review = {
            "tables_reviewed": len(tables),
            "indexes": {},
            "recommendations": []
        }
        
        for table in tables:
            indexes = inspector.get_indexes(table)
            index_review["indexes"][table] = indexes
            
            # Check for common missing indexes
            columns = inspector.get_columns(table)
            column_names = [col["name"] for col in columns]
            
            # Check for foreign keys without indexes
            foreign_keys = inspector.get_foreign_keys(table)
            for fk in foreign_keys:
                fk_column = fk["constrained_columns"][0]
                has_index = any(
                    idx["column_names"][0] == fk_column
                    for idx in indexes
                )
                if not has_index:
                    index_review["recommendations"].append({
                        "table": table,
                        "type": "missing_index",
                        "column": fk_column,
                        "reason": "Foreign key column should be indexed"
                    })
            
            # Check for common query patterns
            if "created_at" in column_names:
                has_created_at_index = any(
                    "created_at" in idx["column_names"]
                    for idx in indexes
                )
                if not has_created_at_index:
                    index_review["recommendations"].append({
                        "table": table,
                        "type": "missing_index",
                        "column": "created_at",
                        "reason": "Commonly used for date range queries"
                    })
            
            if "status" in column_names:
                has_status_index = any(
                    "status" in idx["column_names"]
                    for idx in indexes
                )
                if not has_status_index:
                    index_review["recommendations"].append({
                        "table": table,
                        "type": "missing_index",
                        "column": "status",
                        "reason": "Commonly used for filtering"
                    })
        
        return index_review
    
    async def analyze_slow_queries(self) -> Dict:
        """Analyze slow queries (requires PostgreSQL pg_stat_statements)"""
        try:
            # Check if pg_stat_statements is enabled
            result = await self.session.execute(
                text("SELECT COUNT(*) FROM pg_stat_statements")
            )
            count = result.scalar()
            
            if count is None:
                return {
                    "enabled": False,
                    "message": "pg_stat_statements extension not enabled"
                }
            
            # Get slow queries
            query = text("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > 100  -- Queries taking > 100ms on average
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """)
            
            result = await self.session.execute(query)
            rows = result.fetchall()
            
            slow_queries = [
                {
                    "query": row[0][:200],  # Truncate for readability
                    "calls": row[1],
                    "total_time_ms": float(row[2]),
                    "mean_time_ms": float(row[3]),
                    "max_time_ms": float(row[4])
                }
                for row in rows
            ]
            
            return {
                "enabled": True,
                "slow_queries": slow_queries,
                "count": len(slow_queries)
            }
        except Exception as e:
            return {
                "enabled": False,
                "error": str(e),
                "message": "Could not analyze slow queries"
            }
    
    async def get_table_statistics(self) -> Dict:
        """Get table statistics for optimization"""
        query = text("""
            SELECT 
                schemaname,
                tablename,
                n_live_tup as row_count,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        tables = [
            {
                "schema": row[0],
                "table": row[1],
                "row_count": row[2],
                "dead_rows": row[3],
                "last_vacuum": row[4].isoformat() if row[4] else None,
                "last_autovacuum": row[5].isoformat() if row[5] else None,
                "last_analyze": row[6].isoformat() if row[6] else None,
                "last_autoanalyze": row[7].isoformat() if row[7] else None
            }
            for row in rows
        ]
        
        return {
            "tables": tables,
            "total_tables": len(tables)
        }
