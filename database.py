#!/usr/bin/env python3
"""
AI Therapy System - Database Management
SQLite database operations, schema management, and data integrity
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from contextlib import contextmanager
import threading
from pathlib import Path

from config import Config
from utils import log_action


class DatabaseManager:
    """Handles all database operations with thread safety and integrity checks"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.lock = threading.Lock()
        self._init_database()
        self._create_indexes()
    
    def _init_database(self):
        """Initialize database with complete schema"""
        with self.get_connection() as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Better performance
            
            self._create_all_tables(conn)
            self._insert_default_data(conn)
            
            log_action("Database initialized", "database")
    
    def _create_all_tables(self, conn: sqlite3.Connection):
        """Create all database tables"""
        
        # Patients table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT,
                contact_info TEXT,
                emergency_contact TEXT,
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_updated TEXT NOT NULL DEFAULT (datetime('now')),
                risk_level TEXT DEFAULT 'low' CHECK (risk_level IN ('low', 'moderate', 'high', 'imminent')),
                preferred_therapy_mode TEXT,
                notes TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Sessions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_date TEXT NOT NULL DEFAULT (datetime('now')),
                session_type TEXT CHECK (session_type IN ('CBT', 'DBT', 'ACT', 'Psychodynamic', 'Assessment', 'Crisis')),
                duration INTEGER DEFAULT 50,
                mood_before INTEGER CHECK (mood_before BETWEEN 1 AND 10),
                mood_after INTEGER CHECK (mood_after BETWEEN 1 AND 10),
                interventions_used TEXT DEFAULT '[]',
                homework_assigned TEXT,
                crisis_flags TEXT DEFAULT '[]',
                therapist_notes TEXT,
                patient_feedback TEXT,
                session_phase TEXT DEFAULT 'completed',
                completed BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Assessments table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                assessment_type TEXT NOT NULL CHECK (assessment_type IN ('PHQ9', 'GAD7', 'PCL5', 'ORS', 'SRS')),
                questions_responses TEXT NOT NULL DEFAULT '{}',
                total_score INTEGER NOT NULL DEFAULT 0,
                severity_level TEXT,
                assessment_date TEXT NOT NULL DEFAULT (datetime('now')),
                interpretation TEXT,
                administered_by TEXT DEFAULT 'AI_System',
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            )
        ''')
        
        # Diagnoses table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                diagnosis_code TEXT,
                diagnosis_name TEXT NOT NULL,
                severity TEXT CHECK (severity IN ('mild', 'moderate', 'severe', 'in_partial_remission', 'in_full_remission')),
                date_diagnosed TEXT NOT NULL DEFAULT (datetime('now')),
                date_resolved TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'in_remission', 'resolved', 'rule_out')),
                supporting_criteria TEXT DEFAULT '{}',
                notes TEXT,
                diagnosed_by TEXT DEFAULT 'AI_System',
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Treatment Goals table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS treatment_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                goal_type TEXT CHECK (goal_type IN ('symptom', 'functional', 'behavioral', 'interpersonal', 'cognitive')),
                goal_description TEXT NOT NULL,
                target_date TEXT,
                current_progress INTEGER DEFAULT 0 CHECK (current_progress BETWEEN 0 AND 100),
                measurement_criteria TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'achieved', 'modified', 'discontinued', 'on_hold')),
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_updated TEXT NOT NULL DEFAULT (datetime('now')),
                priority_level INTEGER DEFAULT 2 CHECK (priority_level BETWEEN 1 AND 3),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Homework Assignments table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS homework_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                assignment_type TEXT NOT NULL,
                description TEXT NOT NULL,
                instructions TEXT,
                due_date TEXT,
                assigned_date TEXT NOT NULL DEFAULT (datetime('now')),
                completed BOOLEAN DEFAULT FALSE,
                completion_date TEXT,
                completion_notes TEXT,
                effectiveness_rating INTEGER CHECK (effectiveness_rating BETWEEN 1 AND 5),
                difficulty_rating INTEGER CHECK (difficulty_rating BETWEEN 1 AND 5),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            )
        ''')
        
        # Progress Notes table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS progress_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                note_type TEXT DEFAULT 'SOAP' CHECK (note_type IN ('SOAP', 'progress', 'crisis', 'assessment', 'treatment_plan')),
                subjective TEXT,
                objective TEXT,
                assessment TEXT,
                plan TEXT,
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                created_by TEXT DEFAULT 'AI_Therapist',
                last_modified TEXT,
                signed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        ''')
        
        # Treatment Plans table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS treatment_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                primary_modality TEXT CHECK (primary_modality IN ('CBT', 'DBT', 'ACT', 'Psychodynamic', 'Integrative')),
                target_symptoms TEXT DEFAULT '[]',
                treatment_goals TEXT DEFAULT '[]',
                estimated_duration INTEGER,
                session_frequency TEXT DEFAULT 'weekly',
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_reviewed TEXT,
                next_review_date TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'modified', 'on_hold', 'discontinued')),
                created_by TEXT DEFAULT 'AI_System',
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Crisis Plans table  
        conn.execute('''
            CREATE TABLE IF NOT EXISTS crisis_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                warning_signs TEXT DEFAULT '[]',
                coping_strategies TEXT DEFAULT '[]',
                social_supports TEXT DEFAULT '[]',
                professional_contacts TEXT DEFAULT '[]',
                environmental_safety TEXT DEFAULT '[]',
                reasons_for_living TEXT DEFAULT '[]',
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                last_updated TEXT NOT NULL DEFAULT (datetime('now')),
                active BOOLEAN DEFAULT TRUE,
                reviewed_date TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Crisis Alerts table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS crisis_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                crisis_type TEXT NOT NULL CHECK (crisis_type IN ('suicide', 'self_harm', 'violence', 'psychosis', 'substance_abuse')),
                risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'imminent')),
                trigger_text TEXT,
                assessment_score INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                resolved BOOLEAN DEFAULT FALSE,
                resolution_date TEXT,
                interventions_used TEXT DEFAULT '[]',
                follow_up_required BOOLEAN DEFAULT TRUE,
                notes TEXT,
                created_by TEXT DEFAULT 'AI_System',
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')
        
        # Interventions Library table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS interventions_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intervention_name TEXT NOT NULL UNIQUE,
                modality TEXT NOT NULL CHECK (modality IN ('CBT', 'DBT', 'ACT', 'Psychodynamic', 'General')),
                category TEXT CHECK (category IN ('cognitive', 'behavioral', 'emotional', 'interpersonal', 'mindfulness')),
                description TEXT NOT NULL,
                instructions TEXT,
                target_symptoms TEXT DEFAULT '[]',
                contraindications TEXT,
                effectiveness_research TEXT,
                session_time INTEGER,
                difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Session Templates table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS session_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                modality TEXT CHECK (modality IN ('CBT', 'DBT', 'ACT', 'Psychodynamic', 'Standard')),
                session_structure TEXT DEFAULT '{}',
                required_assessments TEXT DEFAULT '[]',
                common_interventions TEXT DEFAULT '[]',
                homework_options TEXT DEFAULT '[]',
                total_duration INTEGER DEFAULT 50,
                created_date TEXT NOT NULL DEFAULT (datetime('now')),
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # System Logs table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_level TEXT NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                module TEXT NOT NULL,
                action TEXT NOT NULL,
                patient_id INTEGER,
                session_id INTEGER,
                message TEXT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                user_id TEXT,
                ip_address TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            )
        ''')
        
        # User Activity table (for audit trails)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                ip_address TEXT,
                session_token TEXT
            )
        ''')
        
        conn.commit()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        with self.get_connection() as conn:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name)",
                "CREATE INDEX IF NOT EXISTS idx_patients_active ON patients(active)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_patient_date ON sessions(patient_id, session_date)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(session_type)",
                "CREATE INDEX IF NOT EXISTS idx_assessments_patient_type ON assessments(patient_id, assessment_type)",
                "CREATE INDEX IF NOT EXISTS idx_assessments_date ON assessments(assessment_date)",
                "CREATE INDEX IF NOT EXISTS idx_diagnoses_patient ON diagnoses(patient_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_goals_patient ON treatment_goals(patient_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_homework_patient ON homework_assignments(patient_id, completed)",
                "CREATE INDEX IF NOT EXISTS idx_homework_due ON homework_assignments(due_date)",
                "CREATE INDEX IF NOT EXISTS idx_crisis_alerts_patient ON crisis_alerts(patient_id, resolved)",
                "CREATE INDEX IF NOT EXISTS idx_crisis_alerts_timestamp ON crisis_alerts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_logs_patient ON system_logs(patient_id)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            conn.commit()
    
    def _insert_default_data(self, conn: sqlite3.Connection):
        """Insert default interventions and templates"""
        
        # Check if default data already exists
        result = conn.execute("SELECT COUNT(*) FROM interventions_library").fetchone()
        if result[0] > 0:
            return  # Default data already inserted
        
        # Default CBT interventions
        cbt_interventions = [
            ('Thought Record', 'CBT', 'cognitive', 'Identify and challenge negative automatic thoughts', 
             'Record situation, thoughts, feelings, evidence for/against, alternative thoughts', 
             '["depression", "anxiety", "negative_thinking"]', None, 'Extensive research support', 15, 2),
            
            ('Behavioral Activation', 'CBT', 'behavioral', 'Increase engagement in meaningful activities',
             'Schedule pleasant and mastery activities, monitor mood changes',
             '["depression", "low_motivation", "anhedonia"]', None, 'Strong empirical support', 20, 2),
            
            ('Cognitive Restructuring', 'CBT', 'cognitive', 'Examine and modify cognitive distortions',
             'Identify distorted thinking patterns, examine evidence, develop balanced thoughts',
             '["depression", "anxiety", "cognitive_distortions"]', None, 'Gold standard treatment', 20, 3)
        ]
        
        # Default DBT skills
        dbt_skills = [
            ('Mindfulness Practice', 'DBT', 'mindfulness', 'Present-moment awareness without judgment',
             'Practice observe, describe, participate skills with non-judgmental stance',
             '["emotional_dysregulation", "impulsivity"]', None, 'Core DBT component', 15, 2),
            
            ('Distress Tolerance - TIPP', 'DBT', 'emotional', 'Crisis survival without making worse',
             'Temperature, Intense exercise, Paced breathing, Paired muscle relaxation',
             '["crisis_situations", "overwhelming_emotions"]', 'Avoid if medical conditions present', 'DBT research', 10, 2),
            
            ('Emotion Regulation - PLEASE', 'DBT', 'emotional', 'Reduce vulnerability to negative emotions',
             'Treat Physical illness, balance Eating, avoid Substances, balance Sleep, Exercise',
             '["emotional_dysregulation", "mood_swings"]', None, 'DBT skills training', 25, 3)
        ]
        
        # Default ACT processes
        act_interventions = [
            ('Values Clarification', 'ACT', 'cognitive', 'Identify core personal values',
             'Explore life domains, identify values, rate importance and current living',
             '["lack_of_direction", "meaninglessness"]', None, 'ACT research base', 30, 3),
            
            ('Cognitive Defusion', 'ACT', 'cognitive', 'Create distance from difficult thoughts',
             'Use metaphors, silly voices, "I am having the thought that..." techniques',
             '["cognitive_fusion", "rumination"]', None, 'ACT core process', 20, 2),
            
            ('Mindful Acceptance', 'ACT', 'mindfulness', 'Willingness to experience difficult emotions',
             'Practice acceptance exercises, mindfulness of internal experiences',
             '["experiential_avoidance", "emotional_suppression"]', None, 'Psychological flexibility', 25, 3)
        ]
        
        # Insert all default interventions
        all_interventions = cbt_interventions + dbt_skills + act_interventions
        
        conn.executemany('''
            INSERT INTO interventions_library 
            (intervention_name, modality, category, description, instructions, 
             target_symptoms, contraindications, effectiveness_research, session_time, difficulty_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', all_interventions)
        
        # Default session templates
        templates = [
            ('Standard CBT Session', 'CBT', 
             '{"opening": 5, "homework_review": 10, "agenda_setting": 5, "main_work": 20, "homework_assign": 5, "wrap_up": 5}',
             '["mood_check"]', '["thought_record", "behavioral_activation"]', '["thought_record", "activity_schedule"]', 50),
            
            ('DBT Skills Session', 'DBT',
             '{"mindfulness": 5, "homework_review": 10, "skills_training": 25, "practice": 7, "wrap_up": 3}',
             '["distress_level"]', '["mindfulness", "distress_tolerance"]', '["mindfulness_log", "skills_practice"]', 50),
            
            ('ACT Session', 'ACT',
             '{"check_in": 5, "values_connection": 10, "experiential_exercise": 20, "processing": 10, "commitment": 5}',
             '["values_living"]', '["values_work", "defusion_exercises"]', '["values_actions", "mindfulness_practice"]', 50)
        ]
        
        conn.executemany('''
            INSERT INTO session_templates 
            (template_name, modality, session_structure, required_assessments, 
             common_interventions, homework_options, total_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', templates)
        
        conn.commit()
        log_action("Default data inserted", "database")
    
    @contextmanager
    def get_connection(self):
        """Get thread-safe database connection with context manager"""
        conn = None
        try:
            with self.lock:
                conn = sqlite3.connect(
                    self.db_path, 
                    timeout=Config.DATABASE_TIMEOUT,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row  # Enable column access by name
                conn.execute("PRAGMA foreign_keys = ON")
                yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            log_action(f"Database error: {e}", "database", "ERROR")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dictionaries"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows or last insert ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            
            # Return last insert ID for INSERT statements, row count for others
            if query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            else:
                return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets"""
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        return self.execute_query(f"PRAGMA table_info({table_name})")
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key information for table"""
        return self.execute_query(f"PRAGMA foreign_key_list({table_name})")
    
    def validate_database_integrity(self) -> Dict[str, Any]:
        """Run comprehensive database integrity checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'integrity_check': None,
            'foreign_key_check': None,
            'table_counts': {},
            'orphaned_records': [],
            'issues_found': []
        }
        
        with self.get_connection() as conn:
            # Integrity check
            integrity = conn.execute("PRAGMA integrity_check").fetchall()
            results['integrity_check'] = [row[0] for row in integrity]
            
            # Foreign key check
            fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
            results['foreign_key_check'] = [dict(zip(['table', 'rowid', 'parent', 'fkid'], row)) for row in fk_check]
            
            # Get table counts
            tables = ['patients', 'sessions', 'assessments', 'diagnoses', 'treatment_goals', 
                     'homework_assignments', 'progress_notes', 'treatment_plans', 'crisis_plans', 
                     'crisis_alerts', 'interventions_library', 'session_templates', 'system_logs']
            
            for table in tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    results['table_counts'][table] = count
                except sqlite3.Error as e:
                    results['issues_found'].append(f"Error counting {table}: {e}")
            
            # Check for orphaned records
            orphan_queries = [
                ("Sessions without patients", 
                 "SELECT id FROM sessions WHERE patient_id NOT IN (SELECT id FROM patients)"),
                ("Assessments without patients", 
                 "SELECT id FROM assessments WHERE patient_id NOT IN (SELECT id FROM patients)"),
                ("Goals without patients", 
                 "SELECT id FROM treatment_goals WHERE patient_id NOT IN (SELECT id FROM patients)")
            ]
            
            for description, query in orphan_queries:
                try:
                    orphans = conn.execute(query).fetchall()
                    if orphans:
                        results['orphaned_records'].append({
                            'type': description,
                            'count': len(orphans),
                            'ids': [row[0] for row in orphans]
                        })
                except sqlite3.Error as e:
                    results['issues_found'].append(f"Error checking {description}: {e}")
        
        log_action("Database integrity check completed", "database")
        return results
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create database backup"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            log_action(f"Database backup created: {backup_path}", "database")
            return backup_path
        except Exception as e:
            log_action(f"Database backup failed: {e}", "database", "ERROR")
            raise
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create backup of current database first
            current_backup = self.backup_database(f"{self.db_path}.pre_restore")
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            # Verify restored database
            integrity = self.validate_database_integrity()
            if integrity['integrity_check'] != ['ok']:
                # Restore failed, revert to previous
                shutil.copy2(current_backup, self.db_path)
                raise Exception("Restored database failed integrity check")
            
            log_action(f"Database restored from: {backup_path}", "database")
            return True
            
        except Exception as e:
            log_action(f"Database restore failed: {e}", "database", "ERROR")
            raise
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old log entries and resolved alerts"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        cleanup_results = {}
        
        with self.get_connection() as conn:
            # Clean old system logs (keep warnings and errors longer)
            result = conn.execute(
                "DELETE FROM system_logs WHERE timestamp < ? AND log_level IN ('DEBUG', 'INFO')",
                (cutoff_date,)
            )
            cleanup_results['old_logs'] = result.rowcount
            
            # Clean resolved crisis alerts older than specified period
            result = conn.execute(
                "DELETE FROM crisis_alerts WHERE resolved = TRUE AND resolution_date < ?",
                (cutoff_date,)
            )
            cleanup_results['old_crisis_alerts'] = result.rowcount
            
            # Archive completed homework assignments older than specified period
            result = conn.execute(
                "UPDATE homework_assignments SET archived = TRUE WHERE completed = TRUE AND completion_date < ?",
                (cutoff_date,)
            )
            cleanup_results['archived_homework'] = result.rowcount
            
            conn.commit()
        
        log_action(f"Database cleanup completed: {cleanup_results}", "database")
        return cleanup_results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'file_size_mb': round(os.path.getsize(self.db_path) / (1024*1024), 2),
            'table_counts': {},
            'recent_activity': {},
            'storage_usage': {}
        }
        
        with self.get_connection() as conn:
            # Table counts
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            
            for table in tables:
                table_name = table[0]
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                stats['table_counts'][table_name] = count
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            recent_queries = [
                ('new_patients', "SELECT COUNT(*) FROM patients WHERE created_date > ?"),
                ('recent_sessions', "SELECT COUNT(*) FROM sessions WHERE session_date > ?"),
                ('recent_assessments', "SELECT COUNT(*) FROM assessments WHERE assessment_date > ?"),
                ('active_crises', "SELECT COUNT(*) FROM crisis_alerts WHERE resolved = FALSE")
            ]
            
            for key, query in recent_queries:
                if 'active_crises' in key:
                    count = conn.execute(query).fetchone()[0]
                else:
                    count = conn.execute(query, (week_ago,)).fetchone()[0]
                stats['recent_activity'][key] = count
            
            # Storage usage by table
            for table in tables:
                table_name = table[0]
                try:
                    size_query = f"""
                        SELECT SUM(LENGTH(CAST(* AS TEXT))) as size 
                        FROM {table_name}
                    """
                    size_result = conn.execute(size_query).fetchone()[0]
                    stats['storage_usage'][table_name] = size_result or 0
                except:
                    stats['storage_usage'][table_name] = 0
        
        return stats
    
    def export_patient_data(self, patient_id: int) -> Dict[str, Any]:
        """Export all data for a specific patient"""
        patient_data = {
            'export_timestamp': datetime.now().isoformat(),
            'patient_id': patient_id,
            'patient_info': {},
            'sessions': [],
            'assessments': [],
            'diagnoses': [],
            'treatment_goals': [],
            'homework_assignments': [],
            'progress_notes': [],
            'treatment_plans': [],
            'crisis_plans': [],
            'crisis_alerts': []
        }
        
        # Patient basic info
        patients = self.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if patients:
            patient_data['patient_info'] = patients[0]
        else:
            raise ValueError(f"Patient with ID {patient_id} not found")
        
        # All related data
        data_queries = [
            ('sessions', "SELECT * FROM sessions WHERE patient_id = ? ORDER BY session_date"),
            ('assessments', "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date"),
            ('diagnoses', "SELECT * FROM diagnoses WHERE patient_id = ? ORDER BY date_diagnosed"),
            ('treatment_goals', "SELECT * FROM treatment_goals WHERE patient_id = ? ORDER BY created_date"),
            ('homework_assignments', "SELECT * FROM homework_assignments WHERE patient_id = ? ORDER BY assigned_date"),
            ('progress_notes', "SELECT * FROM progress_notes WHERE patient_id = ? ORDER BY created_date"),
            ('treatment_plans', "SELECT * FROM treatment_plans WHERE patient_id = ? ORDER BY created_date"),
            ('crisis_plans', "SELECT * FROM crisis_plans WHERE patient_id = ? ORDER BY created_date"),
            ('crisis_alerts', "SELECT * FROM crisis_alerts WHERE patient_id = ? ORDER BY timestamp")
        ]
        
        for key, query in data_queries:
            results = self.execute_query(query, (patient_id,))
            patient_data[key] = results
        
        log_action(f"Patient data exported for ID {patient_id}", "database", patient_id=patient_id)
        return patient_data
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'database_accessible': True,
            'file_exists': os.path.exists(self.db_path),
            'file_size_mb': 0,
            'connection_test': False,
            'integrity_ok': False,
            'recent_errors': 0,
            'active_connections': 0,
            'performance_metrics': {}
        }
        
        try:
            # File size
            if health['file_exists']:
                health['file_size_mb'] = round(os.path.getsize(self.db_path) / (1024*1024), 2)
            
            # Connection test
            with self.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                health['connection_test'] = True
                
                # Quick integrity check
                integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
                health['integrity_ok'] = integrity == 'ok'
                
                # Recent errors (last hour)
                hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
                error_count = conn.execute(
                    "SELECT COUNT(*) FROM system_logs WHERE log_level = 'ERROR' AND timestamp > ?",
                    (hour_ago,)
                ).fetchone()[0]
                health['recent_errors'] = error_count
                
                # Performance test
                import time
                start_time = time.time()
                conn.execute("SELECT COUNT(*) FROM patients").fetchone()
                health['performance_metrics']['query_time_ms'] = round((time.time() - start_time) * 1000, 2)
                
        except Exception as e:
            health['database_accessible'] = False
            health['error'] = str(e)
            log_action(f"System health check failed: {e}", "database", "ERROR")
        
        return health
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance"""
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'actions_performed': [],
            'space_freed_mb': 0,
            'performance_improvement': {}
        }
        
        try:
            with self.get_connection() as conn:
                # Get initial file size
                initial_size = os.path.getsize(self.db_path)
                
                # Vacuum database
                conn.execute("VACUUM")
                optimization_results['actions_performed'].append('VACUUM')
                
                # Analyze tables for query optimizer
                conn.execute("ANALYZE")
                optimization_results['actions_performed'].append('ANALYZE')
                
                # Reindex all indexes
                conn.execute("REINDEX")
                optimization_results['actions_performed'].append('REINDEX')
                
                # Update table statistics
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                
                for table in tables:
                    conn.execute(f"ANALYZE {table[0]}")
                
                optimization_results['actions_performed'].append('UPDATE_STATISTICS')
                
                # Calculate space freed
                final_size = os.path.getsize(self.db_path)
                space_freed = (initial_size - final_size) / (1024 * 1024)
                optimization_results['space_freed_mb'] = round(space_freed, 2)
                
                # Performance test
                import time
                start_time = time.time()
                conn.execute("SELECT COUNT(*) FROM sessions WHERE patient_id IN (SELECT id FROM patients)").fetchone()
                query_time = (time.time() - start_time) * 1000
                optimization_results['performance_improvement']['complex_query_time_ms'] = round(query_time, 2)
                
            log_action("Database optimization completed", "database")
            
        except Exception as e:
            log_action(f"Database optimization failed: {e}", "database", "ERROR")
            optimization_results['error'] = str(e)
        
        return optimization_results
    
    def search_records(self, search_term: str, tables: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Search across multiple tables for a term"""
        if not tables:
            tables = ['patients', 'sessions', 'assessments', 'diagnoses', 'treatment_goals', 'progress_notes']
        
        search_results = {}
        search_term = f"%{search_term.lower()}%"
        
        search_queries = {
            'patients': "SELECT * FROM patients WHERE LOWER(name) LIKE ? OR LOWER(notes) LIKE ?",
            'sessions': "SELECT * FROM sessions WHERE LOWER(therapist_notes) LIKE ? OR LOWER(patient_feedback) LIKE ?",
            'assessments': "SELECT * FROM assessments WHERE LOWER(interpretation) LIKE ?",
            'diagnoses': "SELECT * FROM diagnoses WHERE LOWER(diagnosis_name) LIKE ? OR LOWER(notes) LIKE ?",
            'treatment_goals': "SELECT * FROM treatment_goals WHERE LOWER(goal_description) LIKE ?",
            'progress_notes': "SELECT * FROM progress_notes WHERE LOWER(subjective) LIKE ? OR LOWER(objective) LIKE ? OR LOWER(assessment) LIKE ? OR LOWER(plan) LIKE ?"
        }
        
        for table in tables:
            if table in search_queries:
                query = search_queries[table]
                # Determine number of parameters needed
                param_count = query.count('?')
                params = tuple([search_term] * param_count)
                
                try:
                    results = self.execute_query(query, params)
                    search_results[table] = results
                except Exception as e:
                    log_action(f"Search error in {table}: {e}", "database", "ERROR")
                    search_results[table] = []
        
        return search_results
    
    def get_patient_summary(self, patient_id: int) -> Dict[str, Any]:
        """Get comprehensive patient summary"""
        summary = {
            'patient_id': patient_id,
            'patient_info': {},
            'statistics': {},
            'recent_activity': {},
            'current_status': {},
            'alerts': []
        }
        
        try:
            # Basic patient info
            patients = self.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
            if not patients:
                raise ValueError(f"Patient {patient_id} not found")
            
            summary['patient_info'] = patients[0]
            
            # Statistics
            stats_queries = [
                ('total_sessions', "SELECT COUNT(*) FROM sessions WHERE patient_id = ?"),
                ('completed_assessments', "SELECT COUNT(*) FROM assessments WHERE patient_id = ?"),
                ('active_goals', "SELECT COUNT(*) FROM treatment_goals WHERE patient_id = ? AND status = 'active'"),
                ('pending_homework', "SELECT COUNT(*) FROM homework_assignments WHERE patient_id = ? AND completed = FALSE"),
                ('crisis_alerts', "SELECT COUNT(*) FROM crisis_alerts WHERE patient_id = ? AND resolved = FALSE")
            ]
            
            for key, query in stats_queries:
                result = self.execute_query(query, (patient_id,))
                summary['statistics'][key] = result[0][list(result[0].keys())[0]] if result else 0
            
            # Recent activity (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            recent_sessions = self.execute_query(
                "SELECT * FROM sessions WHERE patient_id = ? AND session_date > ? ORDER BY session_date DESC LIMIT 5",
                (patient_id, thirty_days_ago)
            )
            summary['recent_activity']['sessions'] = recent_sessions
            
            recent_assessments = self.execute_query(
                "SELECT * FROM assessments WHERE patient_id = ? AND assessment_date > ? ORDER BY assessment_date DESC LIMIT 3",
                (patient_id, thirty_days_ago)
            )
            summary['recent_activity']['assessments'] = recent_assessments
            
            # Current status
            active_diagnoses = self.execute_query(
                "SELECT * FROM diagnoses WHERE patient_id = ? AND status = 'active' ORDER BY date_diagnosed DESC",
                (patient_id,)
            )
            summary['current_status']['diagnoses'] = active_diagnoses
            
            active_treatment_plan = self.execute_query(
                "SELECT * FROM treatment_plans WHERE patient_id = ? AND status = 'active' ORDER BY created_date DESC LIMIT 1",
                (patient_id,)
            )
            summary['current_status']['treatment_plan'] = active_treatment_plan[0] if active_treatment_plan else None
            
            # Active alerts
            active_alerts = self.execute_query(
                "SELECT * FROM crisis_alerts WHERE patient_id = ? AND resolved = FALSE ORDER BY timestamp DESC",
                (patient_id,)
            )
            summary['alerts'] = active_alerts
            
        except Exception as e:
            log_action(f"Error generating patient summary: {e}", "database", "ERROR", patient_id=patient_id)
            summary['error'] = str(e)
        
        return summary
    
    def generate_report(self, report_type: str, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Generate various system reports"""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).isoformat()
        if not date_to:
            date_to = datetime.now().isoformat()
        
        report = {
            'report_type': report_type,
            'date_range': {'from': date_from, 'to': date_to},
            'generated_at': datetime.now().isoformat(),
            'data': {}
        }
        
        if report_type == 'session_summary':
            # Session statistics
            session_stats = self.execute_query('''
                SELECT 
                    session_type,
                    COUNT(*) as session_count,
                    AVG(duration) as avg_duration,
                    AVG(CAST(mood_before AS REAL)) as avg_mood_before,
                    AVG(CAST(mood_after AS REAL)) as avg_mood_after
                FROM sessions 
                WHERE session_date BETWEEN ? AND ?
                GROUP BY session_type
            ''', (date_from, date_to))
            
            report['data']['session_statistics'] = session_stats
            
        elif report_type == 'assessment_outcomes':
            # Assessment trends
            for assessment_type in ['PHQ9', 'GAD7', 'PCL5']:
                trends = self.execute_query('''
                    SELECT 
                        DATE(assessment_date) as date,
                        AVG(total_score) as avg_score,
                        COUNT(*) as count
                    FROM assessments 
                    WHERE assessment_type = ? AND assessment_date BETWEEN ? AND ?
                    GROUP BY DATE(assessment_date)
                    ORDER BY date
                ''', (assessment_type, date_from, date_to))
                
                report['data'][f'{assessment_type.lower()}_trends'] = trends
                
        elif report_type == 'crisis_summary':
            # Crisis statistics
            crisis_stats = self.execute_query('''
                SELECT 
                    crisis_type,
                    risk_level,
                    COUNT(*) as count,
                    AVG(CASE WHEN resolved THEN 1 ELSE 0 END) as resolution_rate
                FROM crisis_alerts 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY crisis_type, risk_level
            ''', (date_from, date_to))
            
            report['data']['crisis_statistics'] = crisis_stats
            
        elif report_type == 'patient_progress':
            # Goal achievement rates
            goal_progress = self.execute_query('''
                SELECT 
                    goal_type,
                    status,
                    AVG(current_progress) as avg_progress,
                    COUNT(*) as count
                FROM treatment_goals 
                WHERE last_updated BETWEEN ? AND ?
                GROUP BY goal_type, status
            ''', (date_from, date_to))
            
            report['data']['goal_progress'] = goal_progress
        
        return report
    
    def close(self):
        """Close database connections and cleanup"""
        # SQLite connections are closed automatically with context manager
        # This method exists for compatibility and future extensions
        log_action("Database manager closed", "database")


# Helper functions for common database operations
def get_or_create_patient(db: DatabaseManager, name: str, **kwargs) -> Dict[str, Any]:
    """Get existing patient or create new one"""
    existing = db.execute_query("SELECT * FROM patients WHERE name = ?", (name,))
    
    if existing:
        return existing[0]
    
    # Create new patient
    patient_data = {
        'name': name,
        'date_of_birth': kwargs.get('date_of_birth', ''),
        'gender': kwargs.get('gender', ''),
        'contact_info': kwargs.get('contact_info', ''),
        'emergency_contact': kwargs.get('emergency_contact', ''),
        'preferred_therapy_mode': kwargs.get('preferred_therapy_mode', 'CBT'),
        'notes': kwargs.get('notes', '')
    }
    
    patient_id = db.execute_update('''
        INSERT INTO patients (name, date_of_birth, gender, contact_info, emergency_contact, preferred_therapy_mode, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_data['name'], patient_data['date_of_birth'], patient_data['gender'],
        patient_data['contact_info'], patient_data['emergency_contact'],
        patient_data['preferred_therapy_mode'], patient_data['notes']
    ))
    
    patient_data['id'] = patient_id
    patient_data['created_date'] = datetime.now().isoformat()
    patient_data['last_updated'] = datetime.now().isoformat()
    patient_data['risk_level'] = 'low'
    patient_data['active'] = True
    
    return patient_data


def create_session_record(db: DatabaseManager, patient_id: int, session_type: str, **kwargs) -> int:
    """Create a new session record"""
    session_id = db.execute_update('''
        INSERT INTO sessions 
        (patient_id, session_type, duration, mood_before, mood_after, 
         interventions_used, homework_assigned, crisis_flags, therapist_notes, patient_feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_id,
        session_type,
        kwargs.get('duration', 50),
        kwargs.get('mood_before', 5),
        kwargs.get('mood_after', 5),
        json.dumps(kwargs.get('interventions_used', [])),
        kwargs.get('homework_assigned', ''),
        json.dumps(kwargs.get('crisis_flags', [])),
        kwargs.get('therapist_notes', ''),
        kwargs.get('patient_feedback', '')
    ))
    
    return session_id


def save_assessment_result(db: DatabaseManager, patient_id: int, assessment_type: str, 
                          responses: Dict, total_score: int, severity: str, interpretation: str,
                          session_id: int = None) -> int:
    """Save assessment result to database"""
    assessment_id = db.execute_update('''
        INSERT INTO assessments 
        (patient_id, session_id, assessment_type, questions_responses, total_score, severity_level, interpretation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_id, session_id, assessment_type, 
        json.dumps(responses), total_score, severity, interpretation
    ))
    
    return assessment_id


# Test and demonstration function
def main():
    """Test database functionality"""
    print("Testing Database Manager...")
    
    # Initialize database
    db = DatabaseManager(":memory:")  # Use in-memory database for testing
    
    # Test basic operations
    print("\n1. Testing patient creation...")
    patient_data = get_or_create_patient(db, "Test Patient", 
                                       date_of_birth="1990-01-01",
                                       gender="Other",
                                       preferred_therapy_mode="CBT")
    print(f"Created patient: {patient_data['name']} (ID: {patient_data['id']})")
    
    # Test session creation
    print("\n2. Testing session creation...")
    session_id = create_session_record(db, patient_data['id'], "CBT",
                                     mood_before=3, mood_after=7,
                                     interventions_used=["thought_record", "behavioral_activation"])
    print(f"Created session ID: {session_id}")
    
    # Test assessment saving
    print("\n3. Testing assessment saving...")
    assessment_id = save_assessment_result(
        db, patient_data['id'], "PHQ9",
        {"q1": {"answer": "Several days", "score": 1}, "q2": {"answer": "Not at all", "score": 0}},
        10, "Mild", "Mild depression indicated", session_id
    )
    print(f"Created assessment ID: {assessment_id}")
    
    # Test database statistics
    print("\n4. Database statistics...")
    stats = db.get_database_stats()
    print(f"Table counts: {stats['table_counts']}")
    
    # Test patient summary
    print("\n5. Patient summary...")
    summary = db.get_patient_summary(patient_data['id'])
    print(f"Patient has {summary['statistics']['total_sessions']} sessions")
    
    # Test integrity
    print("\n6. Integrity check...")
    integrity = db.validate_database_integrity()
    print(f"Integrity check: {integrity['integrity_check']}")
    
    print("\nDatabase testing completed successfully!")


if __name__ == "__main__":
    main()