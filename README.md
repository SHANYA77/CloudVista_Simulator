# CloudVista - Cloud Resource Simulation Platform

A full-stack web application for simulating cloud resource allocation with advanced scheduling algorithms, real-time cost analysis, and comprehensive reporting capabilities.

![CloudVista](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Flask](https://img.shields.io/badge/flask-2.0+-orange)

## Overview

CloudVista enables users to simulate cloud infrastructure management by configuring virtual machines, submitting computational tasks, and analyzing performance metrics across different scheduling strategies. The platform provides real-time visualization of resource utilization and detailed cost breakdowns in Indian Rupees (₹).

## Features

### Core Functionality
- **Virtual Machine Management**: Configure multiple VMs with customizable CPU, RAM, and storage specifications
- **Task Scheduling**: Three scheduling algorithms with real-time execution
  - First Come First Serve (FCFS)
  - Priority Scheduling
  - Round Robin (with configurable time quantum)
- **Cost Analysis**: Real-time cost calculation based on CPU and RAM usage in INR
- **Performance Metrics**: Track wait time, turnaround time, and resource utilization

### Visualization & Reporting
- **Real-time Charts**: Live CPU/RAM utilization graphs
- **Task Timeline**: Visual representation of task execution and wait times
- **Cost Breakdown**: Per-task cost analysis with interactive charts
- **PDF Reports**: Generate comprehensive simulation reports with ReportLab
- **Data Persistence**: SQLite database for storing simulation history

### User Interface
- Modern, responsive design with soft blue cloud-themed aesthetics
- Real-time status indicators
- Interactive dashboard with hover effects
- Smooth animations and transitions

## Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **Flask-CORS** - Cross-Origin Resource Sharing
- **SQLite3** - Database management
- **ReportLab** - PDF generation
- **Threading** - Multi-threaded simulation

### Frontend
- **HTML5**
- **CSS3** - Custom styling with gradients and animations
- **JavaScript (ES6)** - Client-side logic
- **Chart.js** - Data visualization

##  Project Structure

```
cloudvista/
│
├── app.py                    # Flask backend server
├── cloud_simulator.html      # Main HTML file
├── style.css                 # Stylesheet
├── script.js                 # JavaScript logic
│
├── cloudvista.db            # SQLite database (auto-created)
├── reports/                 # Generated PDF reports (auto-created)
│
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/cloudvista.git
cd cloudvista
```

### Step 2: Install Dependencies
```bash
pip install flask flask-cors reportlab
```

Or using requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python app.py
```

The server will start on `http://localhost:5000`

### Step 4: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage Guide

### 1. Initialize Virtual Machines
- Configure the number of VMs (1-10)
- Set CPU cores per VM (1-16)
- Set RAM per VM (1-64 GB)
- Set storage per VM (10-1000 GB)
- Click "Initialize VMs"

### 2. Configure Cost Parameters
- Set CPU cost (₹/core-hour)
- Set RAM cost (₹/GB-hour)
- Set storage cost (₹/GB-month)

### 3. Submit Tasks
- Enter task name
- Specify CPU requirements (cores)
- Specify RAM requirements (GB)
- Set execution time (seconds)
- Set priority (1-10, higher is more important)
- Click "Submit Task"

### 4. Select Scheduler
- Choose from FCFS, Priority, or Round Robin
- For Round Robin, configure time quantum (1-10 seconds)

### 5. Run Simulation
- Click "Start Simulation" to begin
- Monitor real-time statistics and charts
- Watch task status changes (pending → running → completed)

### 6. Generate Reports
- Click "Generate PDF Report" to create detailed analysis
- Click "Save Simulation" to store data in database
- Export JSON data for further analysis

## 🎯 Scheduling Algorithms

### First Come First Serve (FCFS)
- **Type**: Non-preemptive
- **Logic**: Tasks are executed in the order they arrive
- **Use Case**: Simple, fair scheduling for batch processing
- **Pros**: Easy to implement, no starvation
- **Cons**: Poor average waiting time, convoy effect

### Priority Scheduling
- **Type**: Non-preemptive
- **Logic**: Tasks with higher priority execute first
- **Use Case**: When certain tasks need preferential treatment
- **Pros**: Important tasks complete faster
- **Cons**: Lower priority tasks may starve

### Round Robin
- **Type**: Preemptive
- **Logic**: Each task gets a fixed time quantum, then rotates
- **Use Case**: Time-sharing systems, multi-user environments
- **Pros**: Fair CPU distribution, responsive
- **Cons**: Higher context switching overhead

##  API Endpoints

### VM Management
- `POST /api/vms/initialize` - Initialize virtual machines
- `GET /api/vms` - Get all VM configurations

### Task Management
- `POST /api/tasks/submit` - Submit a new task
- `GET /api/tasks` - Get all tasks (pending + completed)

### Simulation Control
- `POST /api/simulation/start` - Start simulation
- `POST /api/simulation/stop` - Stop simulation
- `POST /api/simulation/reset` - Reset simulation state
- `GET /api/simulation/status` - Get current simulation status

### Analytics & Reporting
- `GET /api/statistics` - Get performance statistics
- `POST /api/simulation/save` - Save simulation to database
- `POST /api/report/generate` - Generate PDF report

##  Database Schema

### Simulations Table
```sql
CREATE TABLE simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    scheduler TEXT,
    total_tasks INTEGER,
    completed_tasks INTEGER,
    avg_wait_time REAL,
    avg_turnaround_time REAL,
    total_cost REAL,
    cpu_utilization REAL,
    ram_utilization REAL
)
```

### Tasks Table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_id INTEGER,
    name TEXT,
    cpu_required INTEGER,
    ram_required INTEGER,
    execution_time REAL,
    priority INTEGER,
    wait_time REAL,
    turnaround_time REAL,
    cost REAL,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id)
)
```

## 📈 Performance Metrics

### Calculated Statistics
1. **Average Wait Time**: Time from task arrival to start execution
2. **Average Turnaround Time**: Time from arrival to completion
3. **CPU Utilization**: Percentage of CPU cores in use
4. **RAM Utilization**: Percentage of RAM in use
5. **Total Cost**: Sum of all task execution costs
6. **Cost per Task**: Average cost across all completed tasks

## 🔧 Configuration

### Cost Defaults (INR)
- CPU Cost: ₹4.00 per core-hour
- RAM Cost: ₹0.80 per GB-hour
- Storage Cost: ₹8.00 per GB-month

### VM Defaults
- VMs: 3
- CPU Cores: 4 per VM
- RAM: 8 GB per VM
- Storage: 100 GB per VM

### Simulation Parameters
- Time step: 0.1 seconds
- Round Robin quantum: 2 seconds (default)
- Chart data points: Last 50 entries


##  Authors

- Aanchal Singh - Backend and Scheduling(Partial)                - [YourGitHub](https://github.com/yourusername)
- Shanya        - Frontend simulation                            - [YourGitHub](https://github.com/SHANYA77)
- Shiwani       - Visualization and Scheduling(Partial)          - [YourGitHub](https://github.com/yourusername)
- Tanisha Rawat - Data Storage and Reporting Documentation       - [YourGitHub](https://github.com/yourusername)

##  Acknowledgments

- Chart.js for beautiful data visualizations
- Flask framework for robust backend
- ReportLab for PDF generation
- Cloud computing concepts from operating systems coursework


**Version**: 1.0.0  
**Last Updated**: November 2024  
**Status**: Active Development
