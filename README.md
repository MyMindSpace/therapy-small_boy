# AI Therapy System MVP

A comprehensive therapy application using Gemini 2.5 Pro as the core AI engine.

## Setup

1. Install Python dependencies:
`ash
pip install -r requirements.txt
`

2. Set your Gemini API key:
`ash
export GEMINI_API_KEY=your-api-key-here
`

3. Run the application:
`ash
python main.py
`

## Features

- Multiple therapy modalities (CBT, DBT, ACT, Psychodynamic)
- Comprehensive assessment tools (PHQ-9, GAD-7, PCL-5)
- Goal setting and homework management
- Clinical documentation and progress tracking
- Crisis intervention protocols

## File Structure

- main.py - Entry point and CLI interface
- config.py - Configuration and therapy protocols
- database.py - SQLite database management
- models.py - Data models and validations
- gemini_client.py - Gemini AI integration
- session_manager.py - Session orchestration
- assessment_system.py - Assessment tools
- therapy_modules.py - Therapeutic interventions
- diagnosis_system.py - Diagnostic management
- goal_manager.py - Goal setting and tracking
- homework_system.py - Homework management
- documentation.py - Clinical documentation
- crisis_manager.py - Crisis intervention
- utils.py - Utilities and helpers
