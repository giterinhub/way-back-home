"""
Level 1: Local SQLite Star Catalog Setup

This script creates and populates a local SQLite star_catalog table
that will be used for offline astronomical triangulation.

It replicates the exact same schema and data as the BigQuery table,
allowing participants to write identical SQL queries completely locally!
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "star_catalog.db")

# Star catalog data mapping stellar features to biomes/quadrants
STAR_CATALOG_DATA = [
    # CRYO biome (Northwest quadrant)
    ("blue_giant", "ice_blue", "blue_white", "NW", "CRYO"),
    ("blue_giant", "crystalline", "blue_white", "NW", "CRYO"),
    ("blue_supergiant", "ice_blue", "cyan", "NW", "CRYO"),

    # VOLCANIC biome (Northeast quadrant)
    ("red_dwarf", "orange_red", "red_orange", "NE", "VOLCANIC"),
    ("red_dwarf_binary", "fire", "red_orange", "NE", "VOLCANIC"),
    ("red_giant", "orange_red", "deep_red", "NE", "VOLCANIC"),

    # BIOLUMINESCENT biome (Southwest quadrant)
    ("green_pulsar", "purple_magenta", "green_purple", "SW", "BIOLUMINESCENT"),
    ("pulsar", "purple", "green", "SW", "BIOLUMINESCENT"),
    ("magnetar", "bioluminescent", "cyan_purple", "SW", "BIOLUMINESCENT"),

    # FOSSILIZED biome (Southeast quadrant)
    ("yellow_sun", "golden", "yellow_gold", "SE", "FOSSILIZED"),
    ("yellow_dwarf", "amber", "warm_yellow", "SE", "FOSSILIZED"),
    ("orange_sun", "golden_brown", "amber", "SE", "FOSSILIZED"),
]


def main():
    print(f"Setting up local SQLite star catalog at: {DB_PATH}")
    print("=" * 50)

    # Connect to SQLite database (creates it if not exists)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing table if it exists to allow re-runs
    cursor.execute("DROP TABLE IF EXISTS star_catalog")

    # Create table with matching schema
    cursor.execute("""
        CREATE TABLE star_catalog (
            primary_star TEXT NOT NULL,
            nebula_type TEXT NOT NULL,
            stellar_color TEXT NOT NULL,
            quadrant TEXT NOT NULL,
            biome TEXT NOT NULL
        )
    """)
    print("[OK] Created SQLite table: star_catalog")

    # Insert data
    cursor.executemany("""
        INSERT INTO star_catalog (primary_star, nebula_type, stellar_color, quadrant, biome)
        VALUES (?, ?, ?, ?, ?)
    """, STAR_CATALOG_DATA)
    conn.commit()
    print(f"[OK] Inserted {len(STAR_CATALOG_DATA)} rows successfully")

    # Verify and summarize
    print("\n--- Local Star Catalog Summary ---")
    print("-" * 40)
    cursor.execute("""
        SELECT biome, quadrant, COUNT(*) as entries
        FROM star_catalog
        GROUP BY biome, quadrant
        ORDER BY quadrant
    """)
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[0]}): {row[2]} stellar patterns")

    print("-" * 40)
    print("[OK] Star catalog is ready for local triangulation queries")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
