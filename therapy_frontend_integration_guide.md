# AI Therapy System - Frontend Integration Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture & Components](#architecture--components)
3. [API Reference](#api-reference)
4. [Real-time Features](#real-time-features)
5. [Data Models](#data-models)
6. [Session Flow](#session-flow)
7. [Frontend Implementation Guide](#frontend-implementation-guide)
8. [Authentication & Security](#authentication--security)
9. [Error Handling](#error-handling)
10. [Testing & Development](#testing--development)
11. [Production Deployment](#production-deployment)

---

## System Overview

The AI Therapy System is a comprehensive mental health platform that provides:
- **Interactive AI Therapy Sessions** with dynamic phase transitions
- **Automated Assessment Conducting** (PHQ9, GAD7, PCL5, ORS, SRS)
- **AI-Generated Treatment Plans** and homework assignments
- **Crisis Detection** and safety protocols
- **Real-time WebSocket Chat** with Text-to-Speech (TTS)
- **Content & Lifestyle Recommendations**
- **Progress Tracking** and analytics

### Core Features
- **6 Dynamic Session Phases**: Intake → Assessment → Therapy → Goal Setting → Homework → Closing
- **4 Therapy Modalities**: CBT, DBT, ACT, Psychodynamic
- **Real-time AI Responses** with contextual awareness
- **Automated Symptom Detection** and assessment triggering
- **Crisis Monitoring** with safety protocols
- **Session Transcripts** and insights export
- **Homework Management System** with completion tracking and compliance reporting

---

## Architecture & Components

### Backend Architecture
```
FastAPI Application (Port 8000)
├── Core Modules
│   ├── InteractiveTherapyAI - Main AI conversation engine
│   ├── AssessmentSystem - Automated assessments
│   ├── GoalManager - Treatment goal management
│   ├── HomeworkSystem - Assignment tracking
│   ├── CrisisManager - Safety monitoring
│   └── RecommendationEngine - Content suggestions
├── Database (SQLite)
│   ├── patients - Patient records
│   ├── interactive_sessions - Session data
│   ├── assessments - Assessment results
│   ├── treatment_goals - Goal tracking
│   ├── homework_assignments - Homework management
│   └── diagnoses - Clinical diagnoses
└── External Services
    ├── Google Gemini AI (AI responses)
    └── TTS WebSocket Server (Audio generation)
```

### Frontend Integration Points
- **REST API Endpoints** (31 endpoints)
- **WebSocket Connection** (`/ws/{session_id}`)
- **Real-time Audio Streaming** (TTS integration)
- **Session State Management**
- **Crisis Alert Handling**

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Core Session Management

#### 1. Start Interactive Session
```http
POST /sessions/start
Content-Type: application/json

{
  "patient_id": 1
}
```

**Response:**
```json
{
  "session_id": 123,
  "patient_name": "John Doe",
  "initial_message": "Hello John, I'm Dr. Maya. I'm so glad you're here today...",
  "phase": "intake"
}
```

#### 2. Continue Session Chat (HTTP)
```http
POST /sessions/{session_id}/chat
Content-Type: application/json

{
  "message": "I've been feeling really anxious lately and can't sleep"
}
```

**Response:**
```json
{
  "response": "I'm sorry to hear you've been struggling with anxiety and sleep...",
  "phase": "intake",
  "phase_changed": false,
  "conversation_count": 3,
  "detected_symptoms": ["anxiety", "sleep"],
  "session_completed": false,
  "crisis_alert": null
}
```

#### 3. Get Session Details
```http
GET /sessions/{session_id}
```

**Response:**
```json
{
  "id": 123,
  "patient_id": 1,
  "patient_name": "John Doe",
  "current_phase": "therapy",
  "session_completed": false,
  "conversation_count": 15,
  "detected_symptoms": ["anxiety", "depression"],
  "assessment_results": {
    "PHQ9": {
      "total_score": 12,
      "severity": "moderate",
      "interpretation": "Moderate depression symptoms"
    }
  },
  "goals": [
    {
      "id": 1,
      "goal_type": "symptom",
      "description": "Reduce anxiety symptoms",
      "current_progress": 25
    }
  ],
  "homework": [
    {
      "id": 1,
      "assignment_type": "thought_record",
      "description": "Daily thought record",
      "due_date": "2024-01-22"
    }
  ]
}
```

#### 4. End Session
```http
POST /sessions/{session_id}/end
```

#### 5. Get Active Session
```http
GET /sessions/active
```

### Patient Management

#### 6. Create Patient
```http
POST /patients
Content-Type: application/json

{
  "name": "John Doe",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "preferred_therapy_mode": "CBT"
}
```

#### 7. Get All Patients
```http
GET /patients
```

#### 8. Get Patient Dashboard
```http
GET /patients/{patient_id}/dashboard
```

### Assessment & Progress

#### 9. Complete Homework
```http
POST /homework/{homework_id}/complete
Content-Type: application/json

{
  "notes": "Completed 5 thought records this week. Very helpful!",
  "rating": 4
}
```

#### 10. Update Goal Progress
```http
GET /goals/{goal_id}/progress?progress=75
```

### Recommendations

#### 11. Get Content Recommendations
```http
POST /sessions/{session_id}/content-recommendations
```

#### 12. Get Lifestyle Recommendations
```http
POST /sessions/{session_id}/lifestyle-recommendations
```

### Analytics & Export

#### 13. Get Session Insights
```http
GET /sessions/{session_id}/insights
```

#### 14. Export Session Transcript
```http
GET /sessions/{session_id}/export
```

#### 15. System Analytics
```http
GET /analytics
```

#### 16. Health Check
```http
GET /health
```

---

## Real-time Features

### WebSocket Connection
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

ws.onopen = function(event) {
    console.log('WebSocket connected');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'ai_text':
            // Display AI response text
            displayAIResponse(data.data);
            break;
            
        case 'audio_chunk':
            // Handle audio streaming
            handleAudioChunk(data.data);
            break;
            
        case 'generation_complete':
            // TTS generation finished
            handleTTSComplete(data.data);
            break;
            
        case 'error':
            // Handle errors
            handleError(data.data);
            break;
    }
};

// Send message
ws.send(JSON.stringify({
    message: "I'm feeling anxious about my job interview tomorrow"
}));
```

### Audio Streaming Implementation
```javascript
let audioQueue = [];
let isPlaying = false;

function handleAudioChunk(audioData) {
    audioQueue.push(audioData);
    if (!isPlaying) {
        playNextInQueue();
    }
}

function playNextInQueue() {
    if (audioQueue.length === 0) return;
    
    isPlaying = true;
    const nextChunk = audioQueue.shift();
    playAudioChunk(nextChunk);
}

function playAudioChunk(audioData) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const audioBuffer = audioContext.createBuffer(1, audioData.length, 44100);
    audioBuffer.copyToChannel(audioData, 0);
    
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start();
    
    source.onended = () => {
        isPlaying = false;
        playNextInQueue();
    };
}
```

---

## Data Models

### Core Models

#### Patient
```typescript
interface Patient {
  id: number;
  name: string;
  date_of_birth: string;
  gender: 'male' | 'female' | 'non_binary' | 'other' | 'prefer_not_to_say';
  preferred_therapy_mode: 'CBT' | 'DBT' | 'ACT' | 'psychodynamic';
  created_date: string;
  last_updated: string;
}
```

#### Session
```typescript
interface Session {
  id: number;
  patient_id: number;
  patient_name: string;
  current_phase: 'intake' | 'assessment' | 'therapy' | 'goal_setting' | 'homework' | 'closing' | 'completed';
  session_completed: boolean;
  conversation_count: number;
  detected_symptoms: string[];
  session_insights: SessionInsight[];
  crisis_flags: string[];
  created_date: string;
  last_updated: string;
}
```

#### Assessment
```typescript
interface Assessment {
  id: number;
  patient_id: number;
  assessment_type: 'PHQ9' | 'GAD7' | 'PCL5' | 'ORS' | 'SRS';
  total_score: number;
  severity: 'minimal' | 'mild' | 'moderate' | 'moderately_severe' | 'severe';
  interpretation: string;
  responses: Record<string, any>;
  assessment_date: string;
}
```

#### Treatment Goal
```typescript
interface TreatmentGoal {
  id: number;
  patient_id: number;
  goal_type: 'symptom' | 'behavioral' | 'functional';
  goal_description: string;
  target_date: string;
  measurement_criteria: string;
  current_progress: number;
  status: 'active' | 'completed' | 'paused';
  created_date: string;
  last_updated: string;
}
```

#### Homework Assignment
```typescript
interface HomeworkAssignment {
  id: number;
  patient_id: number;
  assignment_type: string;
  description: string;
  instructions: string;
  assigned_date: string;
  due_date: string;
  completed: boolean;
  completion_notes?: string;
  rating?: number;
}
```

---

## Session Flow

### 1. Session Initialization
```javascript
// Start new session
const startSession = async (patientId) => {
    const response = await fetch('/sessions/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patientId })
    });
    
    const session = await response.json();
    
    // Connect WebSocket
    connectWebSocket(session.session_id);
    
    // Display initial message
    displayMessage('ai', session.initial_message);
    
    return session;
};
```

### 2. Phase Transitions
The system automatically transitions through phases based on conversation depth:

- **Intake** (0-8 exchanges): Initial conversation and symptom exploration
- **Assessment** (8-12 exchanges): Automated assessment conducting
- **Therapy** (12-18 exchanges): Therapeutic intervention
- **Goal Setting** (18-22 exchanges): Treatment goal establishment
- **Homework** (22-26 exchanges): Assignment distribution
- **Closing** (26+ exchanges): Session wrap-up

### 3. Crisis Detection
```javascript
function handleCrisisAlert(crisisData) {
    // Display crisis alert UI
    showCrisisModal({
        title: "Safety Concern Detected",
        message: "We've detected potential safety concerns. Please contact:",
        resources: [
            "988 - Suicide & Crisis Lifeline",
            "911 - Emergency Services",
            "Local Crisis Center"
        ]
    });
    
    // Log crisis event
    logCrisisEvent(crisisData);
}
```

---

## Homework Management System

### Overview
The homework system provides comprehensive assignment tracking, completion monitoring, and compliance reporting. It integrates seamlessly with the therapy session flow and provides real-time updates to both patients and therapists.

### Key Features
- **Automated Assignment Generation** based on therapy modality and patient needs
- **Real-time Completion Tracking** with progress updates
- **Compliance Reporting** with detailed analytics
- **Therapist Dashboard** for monitoring patient progress
- **Patient Interface** for assignment completion and feedback

### Homework Assignment Types
```javascript
const ASSIGNMENT_TYPES = {
    THOUGHT_RECORD: 'thought_record',           // CBT: Daily thought tracking
    MINDFULNESS_PRACTICE: 'mindfulness_practice', // DBT: Mindfulness exercises
    VALUES_EXPLORATION: 'values_exploration',   // ACT: Values-based activities
    REFLECTION_JOURNAL: 'reflection_journal',   // Psychodynamic: Pattern recognition
    BEHAVIORAL_ACTIVATION: 'behavioral_activation', // CBT: Activity scheduling
    DISTRESS_TOLERANCE: 'distress_tolerance'     // DBT: Crisis management
};
```

### API Endpoints for Homework

#### Get Patient Homework Assignments
```http
GET /patients/{patient_id}/homework
```
**Response:**
```json
{
    "assignments": [
        {
            "id": 1,
            "patient_id": 123,
            "assignment_type": "thought_record",
            "description": "Daily thought record for anxiety management",
            "instructions": "Track anxious thoughts daily using the thought record worksheet...",
            "assigned_date": "2024-01-15T10:00:00Z",
            "due_date": "2024-01-22T10:00:00Z",
            "completed": false,
            "completion_date": null,
            "completion_notes": null,
            "effectiveness_rating": null,
            "difficulty_rating": null
        }
    ],
    "compliance_rate": 75.5,
    "total_assignments": 8,
    "completed_assignments": 6,
    "pending_assignments": 2
}
```

#### Mark Homework as Complete
```http
POST /homework/{homework_id}/complete
```
**Request Body:**
```json
{
    "completion_notes": "Found this exercise very helpful for managing anxiety",
    "effectiveness_rating": 4,
    "difficulty_rating": 2,
    "time_spent": 15
}
```

#### Update Homework Progress
```http
POST /homework/{homework_id}/progress
```
**Request Body:**
```json
{
    "progress_notes": "Halfway through the assignment",
    "time_spent": 8,
    "barriers": ["difficulty concentrating", "time constraints"],
    "insights": ["noticed pattern in negative thoughts"],
    "completion_percentage": 50
}
```

#### Generate Homework Report
```http
GET /patients/{patient_id}/homework/report
```
**Response:**
```json
{
    "patient_id": 123,
    "report_period": "30_days",
    "compliance_metrics": {
        "total_assignments": 12,
        "completed_assignments": 9,
        "compliance_rate": 75.0,
        "average_completion_time": 2.3,
        "effectiveness_rating": 4.2
    },
    "assignment_breakdown": {
        "thought_record": {"assigned": 4, "completed": 3},
        "mindfulness_practice": {"assigned": 3, "completed": 2},
        "behavioral_activation": {"assigned": 5, "completed": 4}
    },
    "insights": [
        "Patient shows strong engagement with CBT techniques",
        "Mindfulness exercises need more support",
        "Consider adjusting difficulty level for future assignments"
    ]
}
```

### Frontend Implementation

#### Homework Dashboard Component
```javascript
// Homework Dashboard Component
class HomeworkDashboard {
    constructor(patientId) {
        this.patientId = patientId;
        this.assignments = [];
        this.compliance = {};
    }

    async loadAssignments() {
        try {
            const response = await fetch(`/api/patients/${this.patientId}/homework`);
            const data = await response.json();
            this.assignments = data.assignments;
            this.compliance = data.compliance_metrics;
            this.render();
        } catch (error) {
            console.error('Error loading homework:', error);
        }
    }

    render() {
        const container = document.getElementById('homework-dashboard');
        container.innerHTML = `
            <div class="homework-stats">
                <div class="stat-card">
                    <h3>Compliance Rate</h3>
                    <div class="stat-value">${this.compliance.compliance_rate}%</div>
                </div>
                <div class="stat-card">
                    <h3>Total Assignments</h3>
                    <div class="stat-value">${this.compliance.total_assignments}</div>
                </div>
                <div class="stat-card">
                    <h3>Completed</h3>
                    <div class="stat-value">${this.compliance.completed_assignments}</div>
                </div>
            </div>
            <div class="assignments-list">
                ${this.assignments.map(assignment => this.renderAssignment(assignment)).join('')}
            </div>
        `;
    }

    renderAssignment(assignment) {
        return `
            <div class="homework-item ${assignment.completed ? 'completed' : 'pending'}">
                <div class="assignment-header">
                    <h4>${assignment.description}</h4>
                    <span class="status-badge ${assignment.completed ? 'completed' : 'pending'}">
                        ${assignment.completed ? 'Completed' : 'Pending'}
                    </span>
                </div>
                <div class="assignment-details">
                    <p><strong>Type:</strong> ${assignment.assignment_type}</p>
                    <p><strong>Due:</strong> ${new Date(assignment.due_date).toLocaleDateString()}</p>
                    <p><strong>Instructions:</strong> ${assignment.instructions}</p>
                </div>
                <div class="assignment-actions">
                    ${!assignment.completed ? `
                        <button onclick="markComplete(${assignment.id})" class="btn btn-success">
                            Mark Complete
                        </button>
                        <button onclick="updateProgress(${assignment.id})" class="btn btn-secondary">
                            Update Progress
                        </button>
                    ` : `
                        <button onclick="viewDetails(${assignment.id})" class="btn btn-info">
                            View Details
                        </button>
                    `}
                </div>
            </div>
        `;
    }
}
```

#### Homework Completion Flow
```javascript
// Mark homework as complete
async function markHomeworkComplete(homeworkId) {
    const completionData = {
        completion_notes: prompt('Add completion notes (optional):'),
        effectiveness_rating: parseInt(prompt('Rate effectiveness (1-5):')) || 3,
        difficulty_rating: parseInt(prompt('Rate difficulty (1-5):')) || 3,
        time_spent: parseInt(prompt('Time spent (minutes):')) || 0
    };

    try {
        const response = await fetch(`/api/homework/${homeworkId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(completionData)
        });

        if (response.ok) {
            showSuccess('Homework marked as completed!');
            await loadHomeworkAssignments(); // Refresh the list
        } else {
            const error = await response.json();
            showError('Failed to complete homework: ' + error.detail);
        }
    } catch (error) {
        showError('Error completing homework: ' + error.message);
    }
}
```

### Integration with Therapy Sessions

#### Automatic Assignment Generation
The system automatically generates homework assignments based on:
- **Therapy Modality**: CBT, DBT, ACT, or Psychodynamic
- **Patient Symptoms**: Detected during sessions
- **Treatment Goals**: Set during goal-setting phase
- **Session Insights**: AI-analyzed conversation patterns

#### Real-time Updates
- **Session Integration**: Homework assignments appear immediately after sessions
- **Progress Tracking**: Real-time updates when patients complete assignments
- **Therapist Notifications**: Alerts when assignments are completed or overdue
- **Compliance Monitoring**: Automatic tracking of completion rates

### CSS Styling for Homework System
```css
/* Homework System Styles */
.homework-item {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid var(--secondary-color);
}

.homework-item.completed {
    border-left-color: var(--success-color);
    background: #f8fff8;
}

.homework-item.pending {
    border-left-color: var(--warning-color);
}

.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
    text-transform: uppercase;
}

.status-badge.completed {
    background: var(--success-color);
    color: white;
}

.status-badge.pending {
    background: var(--warning-color);
    color: white;
}
```

---

## Frontend Implementation Guide

### 1. Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── Session/
│   │   │   ├── SessionChat.tsx
│   │   │   ├── SessionStatus.tsx
│   │   │   └── PhaseIndicator.tsx
│   │   ├── Patient/
│   │   │   ├── PatientList.tsx
│   │   │   ├── PatientDashboard.tsx
│   │   │   └── PatientProfile.tsx
│   │   ├── Assessment/
│   │   │   ├── AssessmentDisplay.tsx
│   │   │   └── AssessmentHistory.tsx
│   │   ├── Goals/
│   │   │   ├── GoalList.tsx
│   │   │   └── GoalProgress.tsx
│   │   ├── Homework/
│   │   │   ├── HomeworkList.tsx
│   │   │   └── HomeworkCompletion.tsx
│   │   └── Crisis/
│   │       └── CrisisAlert.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── audio.ts
│   ├── hooks/
│   │   ├── useSession.ts
│   │   ├── useWebSocket.ts
│   │   └── useAudio.ts
│   ├── types/
│   │   └── therapy.ts
│   └── utils/
│       ├── sessionUtils.ts
│       └── crisisUtils.ts
```

### 2. API Service Layer
```typescript
// services/api.ts
class TherapyAPI {
    private baseURL = 'http://localhost:8000';
    
    async startSession(patientId: number): Promise<Session> {
        const response = await fetch(`${this.baseURL}/sessions/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: patientId })
        });
        return response.json();
    }
    
    async sendMessage(sessionId: number, message: string): Promise<ChatResponse> {
        const response = await fetch(`${this.baseURL}/sessions/${sessionId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        return response.json();
    }
    
    async getSession(sessionId: number): Promise<Session> {
        const response = await fetch(`${this.baseURL}/sessions/${sessionId}`);
        return response.json();
    }
    
    async endSession(sessionId: number): Promise<void> {
        await fetch(`${this.baseURL}/sessions/${sessionId}/end`, {
            method: 'POST'
        });
    }
    
    async getPatients(): Promise<Patient[]> {
        const response = await fetch(`${this.baseURL}/patients`);
        return response.json();
    }
    
    async createPatient(patient: PatientCreate): Promise<Patient> {
        const response = await fetch(`${this.baseURL}/patients`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(patient)
        });
        return response.json();
    }
}
```

### 3. WebSocket Service
```typescript
// services/websocket.ts
class WebSocketService {
    private ws: WebSocket | null = null;
    private sessionId: number | null = null;
    private onMessage: ((data: any) => void) | null = null;
    
    connect(sessionId: number): Promise<void> {
        return new Promise((resolve, reject) => {
            this.sessionId = sessionId;
            this.ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                resolve();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.onMessage?.(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
            };
        });
    }
    
    sendMessage(message: string): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ message }));
        }
    }
    
    setOnMessage(callback: (data: any) => void): void {
        this.onMessage = callback;
    }
    
    disconnect(): void {
        this.ws?.close();
        this.ws = null;
        this.sessionId = null;
    }
}
```

### 4. Audio Service
```typescript
// services/audio.ts
class AudioService {
    private audioContext: AudioContext | null = null;
    private audioQueue: ArrayBuffer[] = [];
    private isPlaying = false;
    
    async initialize(): Promise<void> {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    
    queueAudioChunk(audioData: string): void {
        // Convert base64 to ArrayBuffer
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        this.audioQueue.push(bytes.buffer);
        if (!this.isPlaying) {
            this.playNextInQueue();
        }
    }
    
    private async playNextInQueue(): Promise<void> {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        const audioBuffer = this.audioQueue.shift()!;
        
        try {
            const decodedBuffer = await this.audioContext!.decodeAudioData(audioBuffer);
            const source = this.audioContext!.createBufferSource();
            source.buffer = decodedBuffer;
            source.connect(this.audioContext!.destination);
            source.start();
            
            source.onended = () => {
                this.playNextInQueue();
            };
        } catch (error) {
            console.error('Audio playback error:', error);
            this.playNextInQueue();
        }
    }
}
```

### 5. React Hooks
```typescript
// hooks/useSession.ts
export const useSession = (sessionId: number) => {
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        const fetchSession = async () => {
            try {
                const sessionData = await api.getSession(sessionId);
                setSession(sessionData);
            } catch (err) {
                setError('Failed to load session');
            } finally {
                setLoading(false);
            }
        };
        
        fetchSession();
    }, [sessionId]);
    
    return { session, loading, error };
};

// hooks/useWebSocket.ts
export const useWebSocket = (sessionId: number) => {
    const [wsService] = useState(() => new WebSocketService());
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    
    useEffect(() => {
        wsService.connect(sessionId)
            .then(() => setConnected(true))
            .catch(console.error);
        
        wsService.setOnMessage((data) => {
            switch (data.type) {
                case 'ai_text':
                    setMessages(prev => [...prev, {
                        type: 'ai',
                        content: data.data,
                        timestamp: new Date().toISOString()
                    }]);
                    break;
                case 'error':
                    console.error('WebSocket error:', data.data);
                    break;
            }
        });
        
        return () => wsService.disconnect();
    }, [sessionId]);
    
    const sendMessage = (message: string) => {
        wsService.sendMessage(message);
        setMessages(prev => [...prev, {
            type: 'user',
            content: message,
            timestamp: new Date().toISOString()
        }]);
    };
    
    return { connected, messages, sendMessage };
};
```

### 6. Main Session Component
```typescript
// components/Session/SessionChat.tsx
export const SessionChat: React.FC<{ sessionId: number }> = ({ sessionId }) => {
    const { session, loading } = useSession(sessionId);
    const { connected, messages, sendMessage } = useWebSocket(sessionId);
    const [inputMessage, setInputMessage] = useState('');
    
    const handleSendMessage = () => {
        if (inputMessage.trim()) {
            sendMessage(inputMessage);
            setInputMessage('');
        }
    };
    
    if (loading) return <div>Loading session...</div>;
    
    return (
        <div className="session-chat">
            <div className="chat-header">
                <h2>Session with {session?.patient_name}</h2>
                <div className="session-status">
                    <span className={`phase ${session?.current_phase}`}>
                        {session?.current_phase?.toUpperCase()}
                    </span>
                    <span className={`connection ${connected ? 'connected' : 'disconnected'}`}>
                        {connected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
            </div>
            
            <div className="chat-messages">
                {messages.map((message, index) => (
                    <div key={index} className={`message ${message.type}`}>
                        <div className="message-content">{message.content}</div>
                        <div className="message-time">
                            {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                    </div>
                ))}
            </div>
            
            <div className="chat-input">
                <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type your message..."
                    disabled={!connected}
                />
                <button onClick={handleSendMessage} disabled={!connected || !inputMessage.trim()}>
                    Send
                </button>
            </div>
        </div>
    );
};
```

---

## Authentication & Security

### API Key Configuration
The system requires a Google Gemini API key for AI responses:

```typescript
// Environment configuration
const config = {
    GEMINI_API_KEY: process.env.REACT_APP_GEMINI_API_KEY,
    API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
    TTS_ENABLED: process.env.REACT_APP_TTS_ENABLED === 'true'
};
```

### CORS Configuration
The backend is configured with CORS middleware:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Error Handling

### API Error Handling
```typescript
class APIError extends Error {
    constructor(
        public status: number,
        public message: string,
        public details?: any
    ) {
        super(message);
    }
}

const handleAPIError = (error: any): APIError => {
    if (error.response) {
        return new APIError(
            error.response.status,
            error.response.data.detail || 'API Error',
            error.response.data
        );
    }
    return new APIError(500, 'Network Error');
};
```

### WebSocket Error Handling
```typescript
const handleWebSocketError = (error: any) => {
    console.error('WebSocket error:', error);
    
    // Attempt reconnection
    setTimeout(() => {
        if (wsService) {
            wsService.reconnect();
        }
    }, 5000);
};
```

### Crisis Handling
```typescript
const handleCrisisDetection = (crisisData: any) => {
    // Show crisis alert modal
    setCrisisAlert({
        type: 'crisis',
        message: 'Safety concerns detected. Please contact emergency services.',
        resources: [
            '988 - Suicide & Crisis Lifeline',
            '911 - Emergency Services'
        ]
    });
    
    // Log crisis event
    analytics.track('crisis_detected', {
        sessionId,
        timestamp: new Date().toISOString(),
        details: crisisData
    });
};
```

---

## Testing & Development

### Development Setup
```bash
# Backend setup
cd therapy-small_boy
pip install -r requirements.txt
python fast.py

# Frontend setup
npm create react-app therapy-frontend
cd therapy-frontend
npm install axios socket.io-client
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test session creation
curl -X POST http://localhost:8000/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 1}'
```

### WebSocket Testing
```javascript
// Test WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/1');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', event.data);
ws.send(JSON.stringify({ message: 'Hello' }));
```

---

## Production Deployment

### Environment Variables
```bash
# Backend
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite:///therapy.db
TTS_WS_URL=ws://your-tts-server:8002/ws/tts
TTS_ENABLED=true

# Frontend
REACT_APP_API_BASE_URL=https://your-api-domain.com
REACT_APP_TTS_ENABLED=true
```

### Docker Configuration
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "fast.py"]
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /var/www/therapy-frontend;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Security Considerations
1. **API Key Security**: Store Gemini API key securely
2. **CORS Configuration**: Restrict origins in production
3. **HTTPS**: Use SSL certificates for production
4. **Rate Limiting**: Implement API rate limiting
5. **Data Encryption**: Encrypt sensitive patient data
6. **Access Control**: Implement user authentication
7. **Audit Logging**: Log all therapy sessions

---

## Conclusion

This integration guide provides comprehensive documentation for frontend teams to integrate with the AI Therapy System. The system offers:

- **31 REST API endpoints** for complete functionality
- **Real-time WebSocket communication** with audio streaming
- **Dynamic session phases** with automated transitions
- **Crisis detection** and safety protocols
- **Comprehensive data models** and type safety
- **Production-ready architecture** with security considerations

For additional support or questions, refer to the Swagger UI documentation at `http://localhost:8000/docs` when the backend is running.

---

*Last Updated: January 2024*
*Version: 2.0.0*
