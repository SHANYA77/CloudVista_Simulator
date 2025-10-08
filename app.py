from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time
from datetime import datetime
import threading
import json

app = Flask(__name__)
CORS(app)

# Global state
vms = []
tasks = []
completed_tasks = []
current_time = 0
is_simulating = False
simulation_thread = None
utilization_history = []

class VirtualMachine:
    def _init_(self, vm_id, cores, ram, storage):
        self.id = vm_id
        self.total_cores = cores
        self.available_cores = cores
        self.total_ram = ram
        self.available_ram = ram
        self.storage = storage
        self.current_task = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'total_cores': self.total_cores,
            'available_cores': self.available_cores,
            'total_ram': self.total_ram,
            'available_ram': self.available_ram,
            'storage': self.storage,
            'current_task': self.current_task.to_dict() if self.current_task else None
        }

class Task:
    def _init_(self, task_id, name, cpu, ram, exec_time, priority, arrival_time):
        self.id = task_id
        self.name = name
        self.cpu_required = cpu
        self.ram_required = ram
        self.execution_time = exec_time
        self.priority = priority
        self.arrival_time = arrival_time
        self.start_time = None
        self.end_time = None
        self.status = 'pending'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cpu_required': self.cpu_required,
            'ram_required': self.ram_required,
            'execution_time': self.execution_time,
            'priority': self.priority,
            'arrival_time': self.arrival_time,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status
        }

# API Endpoints

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/vms/initialize', methods=['POST'])
def initialize_vms():
    global vms
    data = request.json
    count = data.get('count', 3)
    cores = data.get('cores', 4)
    ram = data.get('ram', 8)
    storage = data.get('storage', 100)
    
    vms = []
    for i in range(count):
        vms.append(VirtualMachine(i + 1, cores, ram, storage))
    
    return jsonify({
        'success': True,
        'message': f'Initialized {count} VMs',
        'vms': [vm.to_dict() for vm in vms]
    })

@app.route('/api/vms', methods=['GET'])
def get_vms():
    return jsonify([vm.to_dict() for vm in vms])

@app.route('/api/tasks/submit', methods=['POST'])
def submit_task():
    global tasks, current_time
    data = request.json
    
    task_id = len(tasks) + 1
    task = Task(
        task_id,
        data.get('name', f'Task-{task_id}'),
        data.get('cpu', 2),
        data.get('ram', 4),
        data.get('execution_time', 10),
        data.get('priority', 5),
        current_time
    )
    
    tasks.append(task)
    
    return jsonify({
        'success': True,
        'task': task.to_dict()
    })

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    all_tasks = tasks + completed_tasks
    return jsonify([task.to_dict() for task in all_tasks])

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    global is_simulating, simulation_thread
    
    if not vms:
        return jsonify({'success': False, 'message': 'No VMs initialized'}), 400
    
    if not tasks:
        return jsonify({'success': False, 'message': 'No tasks to simulate'}), 400
    
    data = request.json
    scheduler = data.get('scheduler', 'fcfs')
    
    is_simulating = True
    simulation_thread = threading.Thread(target=run_simulation, args=(scheduler,))
    simulation_thread.start()
    
    return jsonify({'success': True, 'message': 'Simulation started'})

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    global is_simulating
    is_simulating = False
    return jsonify({'success': True, 'message': 'Simulation stopped'})

@app.route('/api/simulation/reset', methods=['POST'])
def reset_simulation():
    global tasks, completed_tasks, current_time, is_simulating, utilization_history
    
    is_simulating = False
    tasks = []
    completed_tasks = []
    current_time = 0
    utilization_history = []
    
    for vm in vms:
        vm.available_cores = vm.total_cores
        vm.available_ram = vm.total_ram
        vm.current_task = None
    
    return jsonify({'success': True, 'message': 'Simulation reset'})

@app.route('/api/simulation/status', methods=['GET'])
def get_simulation_status():
    return jsonify({
        'is_simulating': is_simulating,
        'current_time': current_time,
        'tasks': [task.to_dict() for task in tasks],
        'completed_tasks': [task.to_dict() for task in completed_tasks],
        'vms': [vm.to_dict() for vm in vms]
    })

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    total_tasks = len(tasks) + len(completed_tasks)
    completed = len(completed_tasks)
    
    avg_wait = 0
    avg_turnaround = 0
    
    if completed_tasks:
        avg_wait = sum((t.start_time - t.arrival_time) for t in completed_tasks) / len(completed_tasks)
        avg_turnaround = sum((t.end_time - t.arrival_time) for t in completed_tasks) / len(completed_tasks)
    
    cpu_util = 0
    ram_util = 0
    
    if vms:
        total_cpu = sum(vm.total_cores for vm in vms)
        used_cpu = sum((vm.total_cores - vm.available_cores) for vm in vms)
        total_ram = sum(vm.total_ram for vm in vms)
        used_ram = sum((vm.total_ram - vm.available_ram) for vm in vms)
        
        cpu_util = (used_cpu / total_cpu) * 100 if total_cpu > 0 else 0
        ram_util = (used_ram / total_ram) * 100 if total_ram > 0 else 0
    
    return jsonify({
        'total_tasks': total_tasks,
        'completed_tasks': completed,
        'avg_wait_time': round(avg_wait, 2),
        'avg_turnaround_time': round(avg_turnaround, 2),
        'cpu_utilization': round(cpu_util, 2),
        'ram_utilization': round(ram_util, 2),
        'utilization_history': utilization_history[-50:]  # Last 50 data points
    })

# Simulation Logic

def run_simulation(scheduler):
    global current_time, is_simulating, tasks, completed_tasks, utilization_history
    
    # Sort tasks based on scheduler
    pending_tasks = [t for t in tasks if t.status == 'pending']
    
    if scheduler == 'fcfs':
        pending_tasks.sort(key=lambda t: t.arrival_time)
    elif scheduler == 'priority':
        pending_tasks.sort(key=lambda t: -t.priority)
    
    while is_simulating:
        current_time += 0.1
        time.sleep(0.1)  # Real-time simulation
        
        # Check for completed tasks
        for vm in vms:
            if vm.current_task and current_time >= vm.current_task.end_time:
                task = vm.current_task
                task.status = 'completed'
                completed_tasks.append(task)
                tasks.remove(task)
                
                vm.available_cores += task.cpu_required
                vm.available_ram += task.ram_required
                vm.current_task = None
        
        # Assign pending tasks to available VMs
        for task in pending_tasks[:]:
            if task.status == 'pending':
                available_vm = next(
                    (vm for vm in vms 
                     if vm.current_task is None 
                     and vm.available_cores >= task.cpu_required 
                     and vm.available_ram >= task.ram_required),
                    None
                )
                
                if available_vm:
                    task.status = 'running'
                    task.start_time = current_time
                    task.end_time = current_time + task.execution_time
                    
                    available_vm.current_task = task
                    available_vm.available_cores -= task.cpu_required
                    available_vm.available_ram -= task.ram_required
        
        # Record utilization
        if vms:
            total_cpu = sum(vm.total_cores for vm in vms)
            used_cpu = sum((vm.total_cores - vm.available_cores) for vm in vms)
            total_ram = sum(vm.total_ram for vm in vms)
            used_ram = sum((vm.total_ram - vm.available_ram) for vm in vms)
            
            utilization_history.append({
                'time': round(current_time, 1),
                'cpu': round((used_cpu / total_cpu) * 100, 2) if total_cpu > 0 else 0,
                'ram': round((used_ram / total_ram) * 100, 2) if total_ram > 0 else 0
            })
        
        # Stop if all tasks completed
        if all(t.status == 'completed' for t in tasks) and not pending_tasks:
            is_simulating = False
            break

if __name__ == '_main_':
    app.run(debug=True, port=5000, threaded=True)