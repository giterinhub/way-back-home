import os
import sqlite3
import re
from typing import List, Dict, Any, Optional

class MockField:
    def __init__(self, name: str):
        self.name = name

class MockResults:
    def __init__(self, rows: List[tuple], columns: List[str]):
        self.rows = rows
        self.fields = [MockField(col) for col in columns]
        
    def __iter__(self):
        return iter(self.rows)

class MockSnapshot:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None, param_types: Optional[Dict[str, Any]] = None):
        # Spanner parameters: @param_name -> SQLite parameters: :param_name
        translated_sql = sql
        
        # Translate parameters: @name -> :name, @limit -> :limit, etc.
        translated_sql = re.sub(r'@([a-zA-Z0-9_]+)', r':\1', translated_sql)
        
        cursor = self.conn.cursor()
        
        # Convert params to sqlite3 format
        sqlite_params = {}
        if params:
            for k, v in params.items():
                if hasattr(v, 'isoformat'):
                    sqlite_params[k] = v.isoformat()
                else:
                    sqlite_params[k] = v
                    
        cursor.execute(translated_sql, sqlite_params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else []
        cursor.close()
        return MockResults(rows, columns)

class MockTransaction(MockSnapshot):
    def insert(self, table: str, columns: List[str], values: List[List[Any]]):
        cursor = self.conn.cursor()
        placeholders = ", ".join(["?" for _ in columns])
        col_str = ", ".join(columns)
        
        converted_values = []
        for row in values:
            converted_row = []
            for val in row:
                if hasattr(val, 'isoformat'):
                    converted_row.append(val.isoformat())
                else:
                    converted_row.append(val)
            converted_values.append(converted_row)
            
        cursor.executemany(f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})", converted_values)
        cursor.close()

    def execute_update(self, sql: str, params: Optional[Dict[str, Any]] = None, param_types: Optional[Dict[str, Any]] = None):
        translated_sql = re.sub(r'@([a-zA-Z0-9_]+)', r':\1', sql)
        cursor = self.conn.cursor()
        sqlite_params = {}
        if params:
            for k, v in params.items():
                if hasattr(v, 'isoformat'):
                    sqlite_params[k] = v.isoformat()
                else:
                    sqlite_params[k] = v
        cursor.execute(translated_sql, sqlite_params)
        cursor.close()

class MockDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def snapshot(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return MockSnapshot(conn)

    def run_in_transaction(self, func, *args, **kwargs):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        transaction = MockTransaction(conn)
        try:
            conn.execute("BEGIN TRANSACTION")
            result = func(transaction, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class SpannerService:
    def __init__(self):
        self.graph_name = os.getenv('GRAPH_NAME', 'SurvivorGraph')
        # Point to the local SQLite database
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "survivor_network.db")
        self.database = MockDatabase(self.db_path)

    def execute_gql(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a GQL (Graph Query Language) query against SQLite database using basic regex matching.
        """
        try:
            # Match node GQL: MATCH (n) WHERE n.id = '{node_id}' RETURN n
            node_match = re.search(r"n\.id\s*=\s*'([^']+)'", query)
            if node_match:
                node_id = node_match.group(1)
                node_data = self._fetch_node_by_id(node_id)
                if node_data:
                    return [{"n": node_data}]
                return []

            # Match edge GQL: MATCH ()-[e]->() WHERE e.id = '{edge_id}' RETURN e
            edge_match = re.search(r"e\.id\s*=\s*'([^']+)'", query)
            if edge_match:
                edge_id = edge_match.group(1)
                edge_data = self._fetch_edge_by_id(edge_id)
                if edge_data:
                    return [{"e": edge_data}]
                return []

            # General query or fallback
            return []
        except Exception as e:
            print(f"Error executing GQL query: {e}")
            raise

    def execute_update(self, query: str) -> None:
        """Execute a DML update query against Spanner Graph."""
        pass

    def parse_node(self, node_data: Any) -> Dict[str, Any]:
        if isinstance(node_data, dict):
            return node_data
        return {}

    def parse_edge(self, edge_data: Any) -> Dict[str, Any]:
        if isinstance(edge_data, dict):
            return edge_data
        return {}

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        try:
            query = f"MATCH (n) WHERE n.id = '{node_id}' RETURN n"
            results = self.execute_gql(query)
            return results[0]["n"] if results else None
        except Exception as e:
            print(f"Error getting node: {e}")
            return None

    async def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        try:
            query = f"MATCH ()-[e]->() WHERE e.id = '{edge_id}' RETURN e"
            results = self.execute_gql(query)
            return results[0]["e"] if results else None
        except Exception as e:
            print(f"Error getting edge: {e}")
            return None

    def _fetch_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if node_id.startswith("survivor_"):
                cursor.execute("SELECT * FROM Survivors WHERE survivor_id = ?", (node_id,))
                row = cursor.fetchone()
                if row:
                    cols = [c[0] for c in cursor.description]
                    res = dict(zip(cols, row))
                    return {"id": res["survivor_id"], "type": "SURVIVOR", "label": res["name"], "role": res["role"], "biome": res["biome"]}
            elif node_id.startswith("skill_"):
                cursor.execute("SELECT * FROM Skills WHERE skill_id = ?", (node_id,))
                row = cursor.fetchone()
                if row:
                    cols = [c[0] for c in cursor.description]
                    res = dict(zip(cols, row))
                    return {"id": res["skill_id"], "type": "SKILL", "label": res["name"], "category": res["category"]}
            elif node_id.startswith("need_"):
                cursor.execute("SELECT * FROM Needs WHERE need_id = ?", (node_id,))
                row = cursor.fetchone()
                if row:
                    cols = [c[0] for c in cursor.description]
                    res = dict(zip(cols, row))
                    return {"id": res["need_id"], "type": "NEED", "label": res["description"], "category": res["category"]}
            elif node_id.startswith("resource_"):
                cursor.execute("SELECT * FROM Resources WHERE resource_id = ?", (node_id,))
                row = cursor.fetchone()
                if row:
                    cols = [c[0] for c in cursor.description]
                    res = dict(zip(cols, row))
                    return {"id": res["resource_id"], "type": "RESOURCE", "label": res["name"], "biome": res["biome"]}
            elif node_id.startswith("biome_"):
                cursor.execute("SELECT * FROM Biomes WHERE biome_id = ?", (node_id,))
                row = cursor.fetchone()
                if row:
                    cols = [c[0] for c in cursor.description]
                    res = dict(zip(cols, row))
                    return {"id": res["biome_id"], "type": "BIOME", "label": res["name"]}
            return None
        finally:
            cursor.close()
            conn.close()

    def _fetch_edge_by_id(self, edge_id: str) -> Optional[Dict[str, Any]]:
        parts = edge_id.split("-")
        if len(parts) != 2:
            return None
        src, tgt = parts[0], parts[1]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if src.startswith("survivor_") and tgt.startswith("skill_"):
                cursor.execute("SELECT * FROM SurvivorHasSkill WHERE survivor_id = ? AND skill_id = ?", (src, tgt))
                row = cursor.fetchone()
                if row:
                    return {"id": edge_id, "source": src, "target": tgt, "type": "HAS_SKILL", "proficiency": row[2]}
            elif src.startswith("survivor_") and tgt.startswith("need_"):
                cursor.execute("SELECT * FROM SurvivorHasNeed WHERE survivor_id = ? AND need_id = ?", (src, tgt))
                row = cursor.fetchone()
                if row:
                    return {"id": edge_id, "source": src, "target": tgt, "type": "HAS_NEED", "status": row[2]}
            elif src.startswith("skill_") and tgt.startswith("need_"):
                cursor.execute("SELECT * FROM SkillTreatsNeed WHERE skill_id = ? AND need_id = ?", (src, tgt))
                row = cursor.fetchone()
                if row:
                    return {"id": edge_id, "source": src, "target": tgt, "type": "TREATS", "effectiveness": row[2]}
            return None
        finally:
            cursor.close()
            conn.close()

