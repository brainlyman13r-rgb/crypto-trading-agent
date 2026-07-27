"""Module 5: Historical Memory & Self-Reflection System

Stores and learns from past trades using ChromaDB vector database and SQLite.
Implements post-trade reflection and pre-trade memory lookup.
"""

import logging
import json
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.validators import TradeReflection, MemoryInsight

logger = logging.getLogger(__name__)


class HistoricalMemory:
    """Memory system for storing and querying historical trades."""
    
    def __init__(self, db_path: str = "memory/trades.db", reflection_path: str = "memory/reflections.json"):
        """
        Initialize memory system.
        
        Args:
            db_path: Path to SQLite database
            reflection_path: Path to JSON reflections log
        """
        self.db_path = db_path
        self.reflection_path = reflection_path
        
        # Ensure directories exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(reflection_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Try to initialize ChromaDB (optional vector DB)
        try:
            import chromadb
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(
                name="trade_memory",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB vector database initialized")
        except ImportError:
            logger.warning("ChromaDB not installed; vector similarity search disabled")
            self.chroma_client = None
            self.collection = None
        
        logger.info(f"Historical Memory initialized with DB: {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                timestamp_entry TIMESTAMP,
                timestamp_exit TIMESTAMP,
                symbol TEXT,
                side TEXT,
                entry_price REAL,
                exit_price REAL,
                position_size REAL,
                pnl REAL,
                pnl_pct REAL,
                r_multiple REAL,
                holding_time_hours REAL,
                outcome TEXT,
                entry_regime TEXT,
                exit_regime TEXT,
                technical_triggers TEXT,
                why_won_or_lost TEXT,
                key_lessons TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_trade_reflection(self, reflection: TradeReflection) -> bool:
        """
        Store post-trade reflection.
        
        Args:
            reflection: TradeReflection object
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO trades VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                reflection.trade_id,
                reflection.timestamp_entry,
                reflection.timestamp_exit,
                reflection.symbol,
                reflection.side,
                reflection.entry_price,
                reflection.exit_price,
                reflection.position_size,
                reflection.pnl,
                reflection.pnl_pct,
                reflection.r_multiple,
                reflection.holding_time_hours,
                reflection.outcome,
                reflection.entry_regime,
                reflection.exit_regime,
                json.dumps(reflection.technical_triggers_fired),
                reflection.why_won_or_lost,
                json.dumps(reflection.key_lessons),
            ))
            
            conn.commit()
            conn.close()
            
            # Also store in JSON log
            self._append_reflection_log(reflection)
            
            # Add to vector DB if available
            if self.collection:
                self._embed_trade(reflection)
            
            logger.info(f"Trade reflection stored: {reflection.trade_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing trade reflection: {e}")
            return False
    
    def query_similar_setups(
        self,
        symbol: str,
        entry_regime: str,
        technical_triggers: List[str],
        days_back: int = 90,
        limit: int = 5,
    ) -> Optional[MemoryInsight]:
        """
        Query historical trades for similar setups.
        
        Args:
            symbol: Trading pair
            entry_regime: Market regime at entry
            technical_triggers: List of technical triggers that fired
            days_back: Look back window in days
            limit: Maximum results to return
        
        Returns:
            MemoryInsight with success rate and lessons
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Query for similar trades
            cursor.execute("""
                SELECT outcome, r_multiple, holding_time_hours, key_lessons
                FROM trades
                WHERE symbol = ?
                  AND entry_regime = ?
                  AND timestamp_entry > ?
                ORDER BY timestamp_entry DESC
                LIMIT ?
            """, (symbol, entry_regime, cutoff_date, limit * 3))  # Get more, then filter
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                logger.info(f"No similar setups found for {symbol} in {entry_regime} regime")
                return MemoryInsight(
                    similar_trades_count=0,
                    success_rate=0.0,
                    lessons=[],
                    risk_flag=None,
                )
            
            # Calculate stats
            wins = sum(1 for r in results if r[0] == "WIN")
            losses = sum(1 for r in results if r[0] == "LOSS")
            total = wins + losses
            
            success_rate = wins / total if total > 0 else 0.0
            avg_r_multiple_win = sum(r[1] for r in results if r[0] == "WIN") / max(wins, 1)
            avg_r_multiple_loss = abs(sum(r[1] for r in results if r[0] == "LOSS")) / max(losses, 1)
            avg_holding_time = sum(r[2] for r in results) / len(results) if results else 0.0
            
            # Aggregate lessons
            all_lessons = []
            for r in results:
                if r[3]:  # key_lessons column
                    try:
                        lessons = json.loads(r[3])
                        all_lessons.extend(lessons)
                    except:
                        pass
            
            # Most common lessons
            from collections import Counter
            lesson_counts = Counter(all_lessons)
            top_lessons = [lesson for lesson, count in lesson_counts.most_common(3)]
            
            # Risk flag if recent similar trades failed
            recent_trades = [r for r in results if r[0] == "LOSS"][:3]
            risk_flag = None
            if recent_trades and len(recent_trades) >= 2:
                risk_flag = "similar_setup_failed_recently"
            
            insight = MemoryInsight(
                similar_trades_count=len(results),
                success_rate=success_rate,
                lessons=top_lessons,
                risk_flag=risk_flag,
                avg_holding_time_hours=avg_holding_time,
                avg_win_r_multiple=avg_r_multiple_win,
                avg_loss_r_multiple=avg_r_multiple_loss,
            )
            
            logger.info(
                f"Memory lookup: {len(results)} similar trades, {success_rate:.1%} win rate",
                symbol=symbol,
                regime=entry_regime,
            )
            
            return insight
        
        except Exception as e:
            logger.error(f"Error querying memory: {e}")
            return None
    
    def get_success_rate_by_regime(self, symbol: str, regime: str) -> float:
        """Get success rate for trades in a specific regime."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM trades
                WHERE symbol = ? AND entry_regime = ?
            """, (symbol, regime))
            
            total, wins = cursor.fetchone()
            conn.close()
            
            if not total:
                return 0.5  # Default to 50% if no history
            
            return (wins or 0) / total
        
        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return 0.5
    
    def _embed_trade(self, reflection: TradeReflection):
        """Add trade to vector database for semantic search."""
        if not self.collection:
            return
        
        try:
            # Create embedding text
            embedding_text = f"""
            Symbol: {reflection.symbol}
            Side: {reflection.side}
            Regime: {reflection.entry_regime}
            Triggers: {', '.join(reflection.technical_triggers_fired)}
            Outcome: {reflection.outcome}
            R-Multiple: {reflection.r_multiple:.2f}
            Reasoning: {reflection.why_won_or_lost}
            Lessons: {', '.join(reflection.key_lessons)}
            """
            
            # Store in ChromaDB
            self.collection.add(
                ids=[reflection.trade_id],
                documents=[embedding_text],
                metadatas=[{
                    "symbol": reflection.symbol,
                    "side": reflection.side,
                    "regime": reflection.entry_regime,
                    "outcome": reflection.outcome,
                    "r_multiple": reflection.r_multiple,
                }]
            )
        except Exception as e:
            logger.warning(f"Could not embed trade in vector DB: {e}")
    
    def _append_reflection_log(self, reflection: TradeReflection):
        """Append reflection to JSON log file."""
        try:
            # Read existing log
            if Path(self.reflection_path).exists():
                with open(self.reflection_path, 'r') as f:
                    log = json.load(f)
            else:
                log = []
            
            # Append new reflection
            log.append({
                "trade_id": reflection.trade_id,
                "timestamp_entry": reflection.timestamp_entry.isoformat(),
                "timestamp_exit": reflection.timestamp_exit.isoformat(),
                "symbol": reflection.symbol,
                "side": reflection.side,
                "pnl": reflection.pnl,
                "pnl_pct": reflection.pnl_pct,
                "r_multiple": reflection.r_multiple,
                "outcome": reflection.outcome,
                "why_won_or_lost": reflection.why_won_or_lost,
                "key_lessons": reflection.key_lessons,
            })
            
            # Write back
            with open(self.reflection_path, 'w') as f:
                json.dump(log, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Could not append to reflection log: {e}")
    
    def get_statistics(self, days_back: int = 30) -> Dict:
        """Get trading statistics for a period."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    SUM(pnl) as total_pnl,
                    AVG(r_multiple) as avg_r_multiple,
                    AVG(holding_time_hours) as avg_hold_hours
                FROM trades
                WHERE timestamp_exit > ?
            """, (cutoff_date,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row[0] == 0:
                return {"total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0}
            
            total, wins, losses, pnl, avg_r, avg_hold = row
            
            return {
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "win_rate": wins / total if total > 0 else 0.0,
                "total_pnl": pnl or 0.0,
                "avg_r_multiple": avg_r or 0.0,
                "avg_holding_hours": avg_hold or 0.0,
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
