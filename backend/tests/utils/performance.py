"""Performance monitoring utilities for testing purposes."""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlmodel import Session, text


class QueryPerformanceMonitor:
    """Monitor and log database query performance for testing."""

    def __init__(self, session: Session):
        self.session = session

    @asynccontextmanager
    async def monitor_query(self, query_name: str) -> AsyncGenerator[dict[str, Any], None]:
        """Context manager to monitor query execution time."""
        start_time = time.time()
        result = {"query_name": query_name, "start_time": start_time}

        try:
            yield result
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            result.update(
                {"end_time": end_time, "execution_time": execution_time, "execution_time_ms": execution_time * 1000}
            )

    async def explain_query(self, query: str, params: dict[str, Any] | None = None) -> str:
        """Get PostgreSQL EXPLAIN ANALYZE output for a query."""
        explain_query = f"EXPLAIN ANALYZE {query}"

        try:
            result = self.session.exec(text(explain_query), params or {})
            return "\n".join([row[0] for row in result])
        except Exception as e:
            return f"Error executing EXPLAIN: {str(e)}"

    async def get_index_usage_stats(self, table_name: str) -> list[dict[str, Any]]:
        """Get index usage statistics for a table."""
        query = """
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_tup_read,
            idx_tup_fetch,
            idx_scan
        FROM pg_stat_user_indexes
        WHERE tablename = :table_name
        ORDER BY idx_scan DESC;
        """

        try:
            result = self.session.exec(text(query), {"table_name": table_name})
            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "tuples_read": row[3],
                    "tuples_fetched": row[4],
                    "scans": row[5],
                }
                for row in result
            ]
        except Exception as e:
            return [{"error": f"Error getting index stats: {str(e)}"}]

    async def get_table_stats(self, table_name: str) -> dict[str, Any]:
        """Get table statistics including size and row count."""
        queries = {
            "row_count": f"SELECT COUNT(*) FROM {table_name}",
            "table_size": f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))",
            "index_size": f"SELECT pg_size_pretty(pg_indexes_size('{table_name}'))",
        }

        stats = {}
        for stat_name, query in queries.items():
            try:
                result = self.session.exec(text(query))
                stats[stat_name] = result.first()
            except Exception as e:
                stats[stat_name] = f"Error: {str(e)}"

        return stats


class PaginationOptimizer:
    """Utilities for optimizing pagination queries in tests."""

    @staticmethod
    def calculate_optimal_page_size(total_rows: int, target_response_time_ms: float = 100) -> int:
        """Calculate optimal page size based on total rows and target response time."""
        # Simple heuristic: smaller pages for larger datasets
        if total_rows < 1000:
            return min(50, total_rows)
        elif total_rows < 10000:
            return 30
        elif total_rows < 100000:
            return 20
        else:
            return 10

    @staticmethod
    def is_cursor_pagination_beneficial(page: int, per_page: int, total_rows: int) -> bool:
        """Determine if cursor-based pagination would be more efficient than offset-based."""
        offset = (page - 1) * per_page

        # Cursor pagination is beneficial when offset is large relative to total rows
        # or when we're accessing pages beyond the first few
        return offset > 1000 or (offset / total_rows) > 0.1

    @staticmethod
    def suggest_pagination_strategy(page: int, per_page: int, total_rows: int) -> dict[str, Any]:
        """Suggest optimal pagination strategy based on query parameters."""
        offset = (page - 1) * per_page

        return {
            "current_strategy": "offset",
            "offset": offset,
            "efficiency_score": max(0, 1 - (offset / max(total_rows, 1))),
            "recommended_strategy": "cursor"
            if PaginationOptimizer.is_cursor_pagination_beneficial(page, per_page, total_rows)
            else "offset",
            "optimal_page_size": PaginationOptimizer.calculate_optimal_page_size(total_rows),
            "performance_warning": offset > 10000,
        }


async def benchmark_query(session: Session, query_func, *args, iterations: int = 5, **kwargs) -> dict[str, Any]:
    """Benchmark a query function by running it multiple times."""
    times = []

    for _ in range(iterations):
        start_time = time.time()
        await query_func(session, *args, **kwargs)
        end_time = time.time()
        times.append(end_time - start_time)

    return {
        "iterations": iterations,
        "times": times,
        "min_time": min(times),
        "max_time": max(times),
        "avg_time": sum(times) / len(times),
        "total_time": sum(times),
        "min_time_ms": min(times) * 1000,
        "max_time_ms": max(times) * 1000,
        "avg_time_ms": (sum(times) / len(times)) * 1000,
    }
