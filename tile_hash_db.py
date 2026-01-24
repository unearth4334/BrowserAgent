#!/usr/bin/env python3
"""
SQLite database for persistent tile hash tracking.
Manages tile hashes to avoid re-processing unchanged tiles.
"""

import sqlite3
import hashlib
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class TileHashDatabase:
    """Database for tracking tile hashes and processing state."""
    
    def __init__(self, db_path: str = "tile_hashes.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        cursor = self.conn.cursor()
        
        # Tiles table: stores hash, position, and metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT NOT NULL UNIQUE,
                position INTEGER NOT NULL,
                thumbnail_url TEXT,
                has_video BOOLEAN,
                first_seen_timestamp REAL NOT NULL,
                last_seen_timestamp REAL NOT NULL,
                processed BOOLEAN DEFAULT 0
            )
        """)
        
        # Scan history: tracks when scans occurred
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                tiles_found INTEGER,
                new_tiles INTEGER,
                stopped_at_position INTEGER
            )
        """)
        
        # Create index for fast hash lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tiles_hash 
            ON tiles(hash)
        """)
        
        self.conn.commit()
    
    def compute_tile_hash(self, image_bytes: bytes) -> str:
        """
        Compute SHA-256 hash of tile thumbnail.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            12-character hex hash string
        """
        return hashlib.sha256(image_bytes).hexdigest()[:12]
    
    def get_tile_by_hash(self, tile_hash: str) -> Optional[Dict]:
        """
        Get tile info by hash.
        
        Args:
            tile_hash: Tile hash to look up
            
        Returns:
            Dict with tile data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tiles WHERE hash = ?",
            (tile_hash,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def add_or_update_tile(
        self,
        tile_hash: str,
        position: int,
        thumbnail_url: Optional[str] = None,
        has_video: bool = False,
        processed: bool = False
    ) -> int:
        """
        Add new tile or update existing one.
        If tile exists elsewhere, delete old entry and create new one.
        
        Args:
            tile_hash: Unique hash of tile
            position: Current position (1-based, 1 = most recent)
            thumbnail_url: URL of thumbnail
            has_video: Whether tile has video component
            processed: Whether tile has been processed
            
        Returns:
            Tile ID
        """
        cursor = self.conn.cursor()
        now = time.time()
        
        # Check if tile exists
        existing = self.get_tile_by_hash(tile_hash)
        
        if existing:
            # If tile moved position (modified and reappeared), delete old entry
            if existing['position'] != position:
                cursor.execute("DELETE FROM tiles WHERE hash = ?", (tile_hash,))
                # Insert as new tile
                cursor.execute("""
                    INSERT INTO tiles 
                    (hash, position, thumbnail_url, has_video, 
                     first_seen_timestamp, last_seen_timestamp, processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tile_hash, position, thumbnail_url, has_video, now, now, processed))
                tile_id = cursor.lastrowid
            else:
                # Same position, just update timestamp
                cursor.execute("""
                    UPDATE tiles
                    SET last_seen_timestamp = ?,
                        processed = ?
                    WHERE hash = ?
                """, (now, processed, tile_hash))
                tile_id = existing['id']
        else:
            # New tile
            cursor.execute("""
                INSERT INTO tiles 
                (hash, position, thumbnail_url, has_video, 
                 first_seen_timestamp, last_seen_timestamp, processed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tile_hash, position, thumbnail_url, has_video, now, now, processed))
            tile_id = cursor.lastrowid
        
        self.conn.commit()
        return tile_id
    
    def check_consecutive_unchanged(
        self,
        tile_hashes: List[Optional[str]],
        start_position: int,
        required_consecutive: int = 3
    ) -> bool:
        """
        Check if N consecutive tiles exist in DB and are in same relative order.
        
        Args:
            tile_hashes: List of current tile hashes in order (may contain None)
            start_position: 1-based position to start checking from
            required_consecutive: Number of consecutive unchanged tiles needed
            
        Returns:
            True if found required consecutive unchanged tiles
        """
        if start_position + required_consecutive - 1 > len(tile_hashes):
            return False
        
        cursor = self.conn.cursor()
        
        # Get the consecutive tiles to check
        check_hashes = tile_hashes[start_position - 1:start_position + required_consecutive - 1]
        
        # Skip if any are None (missing hash)
        if any(h is None for h in check_hashes):
            return False
        
        # Check each tile individually to ensure they exist at consecutive positions
        for i, tile_hash in enumerate(check_hashes):
            expected_position = start_position + i
            
            cursor.execute(
                "SELECT position FROM tiles WHERE hash = ?",
                (tile_hash,)
            )
            result = cursor.fetchone()
            
            # Tile must exist and be at the expected position
            if not result or result['position'] != expected_position:
                return False
        
        return True
    
    def find_stop_position(
        self,
        tile_hashes: List[Optional[str]],
        required_consecutive: int = 3
    ) -> Optional[int]:
        """
        Find position where we encounter N consecutive unchanged tiles.
        
        Args:
            tile_hashes: List of all tile hashes in current order
            required_consecutive: Number of consecutive unchanged tiles to find
            
        Returns:
            1-based position where to stop (after the consecutive unchanged tiles),
            or None if should process all tiles
        """
        # Check starting from position 1
        for start_pos in range(1, len(tile_hashes) - required_consecutive + 2):
            if self.check_consecutive_unchanged(tile_hashes, start_pos, required_consecutive):
                # Found N consecutive unchanged tiles starting at start_pos
                # Stop after them (at position start_pos + required_consecutive - 1)
                return start_pos + required_consecutive - 1
        
        return None  # Process all tiles
    
    def record_scan(
        self,
        tiles_found: int,
        new_tiles: int,
        stopped_at_position: Optional[int] = None
    ):
        """
        Record a scan in history.
        
        Args:
            tiles_found: Total number of tiles found
            new_tiles: Number of new/modified tiles
            stopped_at_position: Position where scan stopped (if early stop)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scan_history 
            (timestamp, tiles_found, new_tiles, stopped_at_position)
            VALUES (?, ?, ?, ?)
        """, (time.time(), tiles_found, new_tiles, stopped_at_position))
        self.conn.commit()
    
    def mark_tile_processed(self, tile_hash: str):
        """Mark a tile as processed."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE tiles SET processed = 1 WHERE hash = ?",
            (tile_hash,)
        )
        self.conn.commit()
    
    def get_unprocessed_tiles(self) -> List[Dict]:
        """Get all tiles that haven't been processed yet."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tiles WHERE processed = 0 ORDER BY position"
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM tiles")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as processed FROM tiles WHERE processed = 1")
        processed = cursor.fetchone()['processed']
        
        cursor.execute("SELECT COUNT(*) as scans FROM scan_history")
        scans = cursor.fetchone()['scans']
        
        return {
            'total_tiles': total,
            'processed_tiles': processed,
            'unprocessed_tiles': total - processed,
            'total_scans': scans
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def demo():
    """Demo usage of TileHashDatabase."""
    print("=== Tile Hash Database Demo ===\n")
    
    with TileHashDatabase("demo_tiles.db") as db:
        # Simulate first scan
        print("First scan: 5 new tiles")
        hashes_scan1 = ["abc123", "def456", "ghi789", "jkl012", "mno345"]
        for i, h in enumerate(hashes_scan1, 1):
            db.add_or_update_tile(h, i, processed=True)
        
        # Simulate second scan: 2 new tiles at front, rest unchanged
        print("\nSecond scan: 2 new tiles, 3 unchanged")
        hashes_scan2 = ["new001", "new002", "abc123", "def456", "ghi789", "jkl012", "mno345"]
        
        # Find stop position
        stop_pos = db.find_stop_position(hashes_scan2, required_consecutive=3)
        print(f"Should stop at position: {stop_pos}")
        
        if stop_pos:
            print(f"Processing tiles 1-{stop_pos}")
            for i in range(1, stop_pos + 1):
                h = hashes_scan2[i - 1]
                db.add_or_update_tile(h, i)
        
        # Show stats
        stats = db.get_stats()
        print(f"\nDatabase stats: {stats}")


if __name__ == '__main__':
    demo()
