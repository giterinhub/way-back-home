"""
Survivor Network Database Setup Script (SQLite Version)
Run: python setup_data_sqlite.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "survivor_network.db")

DDL_STATEMENTS = [
    # Node Tables
    """CREATE TABLE IF NOT EXISTS Biomes (
        biome_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        quadrant TEXT,
        color TEXT,
        icon TEXT,
        description TEXT
    )""",
    
    """CREATE TABLE IF NOT EXISTS Skills (
        skill_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        icon TEXT,
        color TEXT,
        description TEXT
    )""",
    
    """CREATE TABLE IF NOT EXISTS Needs (
        need_id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        category TEXT,
        urgency TEXT,
        icon TEXT
    )""",
    
    """CREATE TABLE IF NOT EXISTS Resources (
        resource_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        icon TEXT,
        biome TEXT,
        description TEXT
    )""",
    
    """CREATE TABLE IF NOT EXISTS Survivors (
        survivor_id TEXT PRIMARY KEY,
        name TEXT,
        callsign TEXT,
        role TEXT,
        biome TEXT,
        quadrant TEXT,
        status TEXT,
        avatar_url TEXT,
        color TEXT,
        x_position REAL,
        y_position REAL,
        description TEXT,
        created_at TEXT
    )""",
    
    """CREATE TABLE IF NOT EXISTS Broadcasts (
        broadcast_id TEXT PRIMARY KEY,
        survivor_id TEXT NOT NULL,
        broadcast_type TEXT,
        title TEXT,
        gcs_uri TEXT,
        thumbnail_url TEXT,
        duration_seconds INTEGER,
        transcript TEXT,
        processed INTEGER,
        processed_at TEXT,
        created_at TEXT
    )""",
    
    # Edge Tables
    """CREATE TABLE IF NOT EXISTS SurvivorHasSkill (
        survivor_id TEXT NOT NULL,
        skill_id TEXT NOT NULL,
        proficiency TEXT,
        PRIMARY KEY (survivor_id, skill_id)
    )""",
    
    """CREATE TABLE IF NOT EXISTS SurvivorHasNeed (
        survivor_id TEXT NOT NULL,
        need_id TEXT NOT NULL,
        status TEXT,
        PRIMARY KEY (survivor_id, need_id)
    )""",
    
    """CREATE TABLE IF NOT EXISTS SurvivorFoundResource (
        survivor_id TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        found_at TEXT,
        PRIMARY KEY (survivor_id, resource_id)
    )""",
    
    """CREATE TABLE IF NOT EXISTS SurvivorInBiome (
        survivor_id TEXT NOT NULL,
        biome_id TEXT NOT NULL,
        PRIMARY KEY (survivor_id, biome_id)
    )""",
    
    """CREATE TABLE IF NOT EXISTS SurvivorCanHelp (
        helper_id TEXT NOT NULL,
        helpee_id TEXT NOT NULL,
        reason TEXT,
        match_score REAL,
        skill_id TEXT,
        need_id TEXT,
        PRIMARY KEY (helper_id, helpee_id)
    )""",
    
    """CREATE TABLE IF NOT EXISTS SkillTreatsNeed (
        skill_id TEXT NOT NULL,
        need_id TEXT NOT NULL,
        effectiveness TEXT,
        PRIMARY KEY (skill_id, need_id)
    )""",
]

NODE_DATA = {
    "Biomes": [
        ("biome_bioluminescent", "BIOLUMINESCENT", "SW", "#A78BFA", "B", "Glowing forest"),
        ("biome_cryo", "CRYO", "NW", "#60A5FA", "X", "Frozen tundra"),
        ("biome_fossilized", "FOSSILIZED", "SE", "#FBBF24", "F", "Fossil region"),
        ("biome_volcanic", "VOLCANIC", "NE", "#F87171", "V", "Volcanic region"),
    ],
    "Skills": [
        ("skill_botany", "Botany", "science", "B", "#8B5CF6", None),
        ("skill_cartography", "Cartography", "science", "C", "#8B5CF6", None),
        ("skill_engineering", "Engineering", "technical", "E", "#3B82F6", None),
        ("skill_first_aid", "First Aid", "medical", "F", "#EF4444", None),
        ("skill_foraging", "Foraging", "survival", "F", "#10B981", None),
        ("skill_leadership", "Leadership", "leadership", "L", "#F59E0B", None),
        ("skill_medical_training", "Medical Training", "medical", "M", "#EF4444", None),
        ("skill_navigation", "Navigation", "technical", "N", "#3B82F6", None),
        ("skill_pilot", "Pilot", "technical", "P", "#3B82F6", None),
        ("skill_xenobiology", "Xenobiology", "science", "X", "#8B5CF6", None),
    ],
    "Needs": [
        ("need_chen_food", "Need food", "survival", "medium", "F"),
        ("need_chen_materials", "Need materials", "technical", "low", "M"),
        ("need_frost_analysis", "Analyze specimens", "science", "low", "A"),
        ("need_frost_arm", "Arm injury", "medical", "low", "N"),
        ("need_park_ankle", "Sprained ankle", "medical", "low", "A"),
        ("need_park_samples", "Analyze samples", "science", "low", "S"),
        ("need_tanaka_burns", "Burns", "medical", "medium", "B"),
    ],
    "Resources": [
        ("resource_amber", "Amber Fuel", "power", "A", "FOSSILIZED", None),
        ("resource_fresh_water", "Fresh Water", "water", "W", "CRYO", None),
        ("resource_fungi", "Fungi", "tool", "F", "BIOLUMINESCENT", None),
        ("resource_geothermal", "Geothermal Power", "power", "G", "VOLCANIC", None),
        ("resource_hot_springs", "Hot Springs", "shelter", "H", "VOLCANIC", None),
        ("resource_ice_cave", "Ice Cave", "shelter", "I", "CRYO", None),
        ("resource_medicinal_plants", "Medicinal Plants", "medical", "M", "BIOLUMINESCENT", None),
        ("resource_salvaged_tools", "Salvaged Tools", "tool", "T", "FOSSILIZED", None),
    ],
    "Survivors": [
        ("survivor_chen", "David Chen", "Forge-4", "Engineer", "FOSSILIZED", "SE", "active", "/avatars/chen.png", "#FBBF24", 450.0, 350.0, "Engineer", "2026-01-09T11:51:58Z"),
        ("survivor_frost", "Dr. Elena Frost", "Frost-7", "Xenobiologist", "CRYO", "NW", "active", "/avatars/frost.png", "#60A5FA", 150.0, 100.0, "Xenobiologist", "2026-01-09T11:51:58Z"),
        ("survivor_park", "Lt. Sarah Park", "Glow-2", "Navigator", "BIOLUMINESCENT", "SW", "active", "/avatars/park.png", "#A78BFA", 150.0, 350.0, "Navigator", "2026-01-09T11:51:58Z"),
        ("survivor_tanaka", "Captain Yuki Tanaka", "Ember-1", "Pilot", "VOLCANIC", "NE", "active", "/avatars/tanaka.png", "#F87171", 450.0, 100.0, "Pilot", "2026-01-09T11:51:58Z"),
    ]
}

EDGE_DATA = {
    "SurvivorHasSkill": [
        ("survivor_chen", "skill_engineering", "expert"),
        ("survivor_chen", "skill_first_aid", "basic"),
        ("survivor_frost", "skill_medical_training", "proficient"),
        ("survivor_frost", "skill_xenobiology", "expert"),
        ("survivor_park", "skill_botany", "proficient"),
        ("survivor_park", "skill_cartography", "expert"),
        ("survivor_park", "skill_navigation", "expert"),
        ("survivor_tanaka", "skill_leadership", "expert"),
        ("survivor_tanaka", "skill_pilot", "expert"),
    ],
    "SurvivorHasNeed": [
        ("survivor_chen", "need_chen_food", "active"),
        ("survivor_chen", "need_chen_materials", "active"),
        ("survivor_frost", "need_frost_analysis", "active"),
        ("survivor_frost", "need_frost_arm", "active"),
        ("survivor_park", "need_park_ankle", "active"),
        ("survivor_park", "need_park_samples", "active"),
        ("survivor_tanaka", "need_tanaka_burns", "active"),
    ],
    "SurvivorFoundResource": [
        ("survivor_chen", "resource_amber", "2026-01-09T11:52:17Z"),
        ("survivor_chen", "resource_salvaged_tools", "2026-01-09T11:52:17Z"),
        ("survivor_frost", "resource_fresh_water", "2026-01-09T11:52:17Z"),
        ("survivor_frost", "resource_ice_cave", "2026-01-09T11:52:17Z"),
        ("survivor_park", "resource_fungi", "2026-01-09T11:52:17Z"),
        ("survivor_park", "resource_medicinal_plants", "2026-01-09T11:52:17Z"),
        ("survivor_tanaka", "resource_geothermal", "2026-01-09T11:52:17Z"),
        ("survivor_tanaka", "resource_hot_springs", "2026-01-09T11:52:17Z"),
    ],
    "SurvivorInBiome": [
        ("survivor_chen", "biome_fossilized"),
        ("survivor_frost", "biome_cryo"),
        ("survivor_park", "biome_bioluminescent"),
        ("survivor_tanaka", "biome_volcanic"),
    ],
    "SurvivorCanHelp": [
        ("survivor_chen", "survivor_tanaka", "Chen has first aid", 0.65, "skill_first_aid", "need_tanaka_burns"),
        ("survivor_frost", "survivor_park", "Frost can analyze samples", 0.9, "skill_xenobiology", "need_park_samples"),
        ("survivor_frost", "survivor_tanaka", "Frost can treat burns", 0.95, "skill_medical_training", "need_tanaka_burns"),
    ],
    "SkillTreatsNeed": [
        ("skill_engineering", "need_chen_materials", "high"),
        ("skill_first_aid", "need_park_ankle", "high"),
        ("skill_foraging", "need_chen_food", "high"),
        ("skill_medical_training", "need_frost_arm", "high"),
        ("skill_medical_training", "need_tanaka_burns", "high"),
        ("skill_xenobiology", "need_frost_analysis", "high"),
        ("skill_xenobiology", "need_park_samples", "high"),
    ]
}


def main():
    print(f"Setting up local SQLite database at: {DB_PATH}")
    print("=" * 50)
    
    # Connect
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    for ddl in DDL_STATEMENTS:
        cursor.execute(ddl)
        
    print("[OK] Created all relational node and edge tables")
    
    # Insert node data
    for table, rows in NODE_DATA.items():
        # Clear existing
        cursor.execute(f"DELETE FROM {table}")
        
        placeholders = ", ".join(["?" for _ in rows[0]])
        cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        print(f"  [OK] Seeded {len(rows)} nodes into {table}")
        
    # Insert edge data
    for table, rows in EDGE_DATA.items():
        cursor.execute(f"DELETE FROM {table}")
        placeholders = ", ".join(["?" for _ in rows[0]])
        cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        print(f"  [OK] Seeded {len(rows)} edges into {table}")
        
    conn.commit()
    cursor.close()
    conn.close()
    
    print("=" * 50)
    print("[OK] Local Survivor Network SQLite database seeded successfully!")


if __name__ == "__main__":
    main()
