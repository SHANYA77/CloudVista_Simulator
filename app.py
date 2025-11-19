/* script.js - full JS for CloudVista frontend */

/* Global state */
var vms = [];
var tasks = [];
var completedTasks = [];
var currentTime = 0;
var isSimulating = false;
var simulationInterval = null;
var utilizationChart = null;
var timelineChart = null;
var costChart = null;
var taskQueue = [];
var timeQuantum = 2;

/* UI helpers */
function toggleQuantum() {
    var scheduler = document.getElementById('scheduler').value;
    var quantumGroup = document.getElementById('quantumGroup');
    quantumGroup.style.display = scheduler === 'roundrobin' ? 'block' : 'none';
}

/* Charts initialization */
function initCharts() {
    var ctxUtil = document.getElementById('utilizationChart').getContext('2d');
    utilizationChart = new Chart(ctxUtil, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU Utilization (%)',
                data: [],
                borderColor: '#5a9fd4',
                backgroundColor: 'rgba(90, 159, 212, 0.1)',
                tension: 0.4,
                borderWidth: 2,
                fill: true
            }, {
                label: 'RAM Utilization (%)',
                data: [],
                borderColor: '#7db9e8',
                backgroundColor: 'rgba(125, 185, 232, 0.1)',
                tension: 0.4,
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#b8d8ff' } } },
            scales: {
                y: { beginAtZero: true, max: 100, ticks: { color: '#7db9e8' }, grid: { color: 'rgba(90, 159, 212, 0.1)' } },
                x: { ticks: { color: '#7db9e8' }, grid: { color: 'rgba(90, 159, 212, 0.1)' } }
            }
        }
    });

    var ctxTimeline = document.getElementById('timelineChart').getContext('2d');
    timelineChart = new Chart(ctxTimeline, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Wait Time',
                data: [],
                backgroundColor: '#4a8fc7'
            }, {
                label: 'Execution Time',
                data: [],
                backgroundColor: '#5a9fd4'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#b8d8ff' } } },
            scales: {
                x: { stacked: true, ticks: { color: '#7db9e8' }, grid: { color: 'rgba(90, 159, 212, 0.1)' } },
                y: { stacked: true, beginAtZero: true, ticks: { color: '#7db9e8' }, grid: { color: 'rgba(90, 159, 212, 0.1)' } }
            }
        }
    });

    var ctxCost = document.getElementById('costChart').getContext('2d');
    costChart = new Chart(ctxCost, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Task Cost (₹)',
                data: [],
                backgroundColor: '#5a9fd4'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#b8d8ff' } } },
            scales: {
                x: { ticks: { color: '#7db9e8' }, grid: { color: 'rgba(90, 159, 212, 0.1)' } },
                y: { beginAtZero: true, ticks: { color: '#7db9e8' }, grid: { color: 'rgba(90, 159, 212, 0.1)' } }
            }
        }
    });
}

/* VM initialization */
function initializeVMs() {
    var count = parseInt(document.getElementById('vmCount').value);
    var cores = parseInt(document.getElementById('vmCores').value);
    var ram = parseInt(document.getElementById('vmRam').value);
    var storage = parseInt(document.getElementById('vmStorage').value);

    vms = [];
    for (var i = 0; i < count; i++) {
        vms.push({
            id: i + 1,
            totalCores: cores,
            availableCores: cores,
            totalRam: ram,
            availableRam: ram,
            storage: storage,
            currentTask: null
        });
    }
    alert('Initialized ' + count + ' VMs with ' + cores + ' cores and ' + ram + 'GB RAM each');
    updateStats();
}

/* cost calculation (based on CPU & RAM hourly rates) */
function calculateTaskCost(task) {
    var cpuCost = parseFloat(document.getElementById('cpuCost').value) || 0;
    var ramCost = parseFloat(document.getElementById('ramCost').value) || 0;
    var hours = (task.executionTime || 0) / 3600.0;
    var cost = (task.cpuRequired * cpuCost * hours) + (task.ramRequired * ramCost * hours);
    return cost;
}

/* submit a task from UI */
function submitTask() {
    var name = document.getElementById('taskName').value || 'Task-' + (tasks.length + completedTasks.length + 1);
    var cpu = parseInt(document.getElementById('taskCpu').value) || 1;
    var ram = parseInt(document.getElementById('taskRam').value) || 1;
    var time = parseInt(document.getElementById('taskTime').value) || 1;
    var priority = parseInt(document.getElementById('taskPriority').value) || 5;

    var task = {
        id: tasks.length + completedTasks.length + 1,
        name: name,
        cpuRequired: cpu,
        ramRequired: ram,
        executionTime: time,
        remainingTime: time,
        priority: priority,
        arrivalTime: currentTime,
        startTime: null,
        endTime: null,
        status: 'pending',
        quantumUsed: 0,
        cost: 0
    };

    tasks.push(task);
    updateTaskList();
    updateStats();
    document.getElementById('taskName').value = '';
}

/* render task list */
function updateTaskList() {
    var listDiv = document.getElementById('taskList');
    if ((tasks.length === 0) && (completedTasks.length === 0)) {
        listDiv.innerHTML = '<p style="color: #7db9e8;">No tasks submitted yet</p>';
        return;
    }

    var html = '';
    for (var i = 0; i < tasks.length; i++) {
        var task = tasks[i];
        var statusClass = task.status === 'completed' ? 'status-completed' :
                          task.status === 'running' ? 'status-running' : 'status-pending';
        html += '<div class="task-item">' +
            '<div class="task-info">' +
            '<strong>' + task.name + '</strong> - CPU: ' + task.cpuRequired + ' cores, RAM: ' + task.ramRequired + 'GB, Time: ' + task.executionTime + 's, Priority: ' + task.priority +
            '</div>' +
            '<span class="task-status ' + statusClass + '">' + task.status + '</span>' +
            '</div>';
    }
    listDiv.innerHTML = html;
}

/* simulation control */
function startSimulation() {
    if (vms.length === 0) {
        alert('Please initialize VMs first!');
        return;
    }
    var pendingCount = tasks.filter(function(t) { return t.status === 'pending'; }).length;
    if (pendingCount === 0) {
        alert('No pending tasks to simulate!');
        return;
    }

    isSimulating = true;
    document.getElementById('simStatus').textContent = 'Running';

    var scheduler = document.getElementById('scheduler').value;
    timeQuantum = scheduler === 'roundrobin' ? parseFloat(document.getElementById('timeQuantum').value) || 2 : 0;

    var pendingTasks = tasks.filter(function(t) { return t.status === 'pending'; });

    if (scheduler === 'fcfs') {
        pendingTasks.sort(function(a, b) { return a.arrivalTime - b.arrivalTime; });
    } else if (scheduler === 'priority') {
        pendingTasks.sort(function(a, b) { return b.priority - a.priority; });
    } else if (scheduler === 'roundrobin') {
        taskQueue = pendingTasks.slice();
    }

    simulationInterval = setInterval(function() {
        if (scheduler === 'roundrobin') {
            simulateRoundRobin();
        } else {
            simulateStep(pendingTasks);
        }
    }, 100);
}

/* FCFS & Priority step simulation */
function simulateStep(pendingTasks) {
    currentTime += 0.1;

    // finish tasks
    for (var i = 0; i < vms.length; i++) {
        var vm = vms[i];
        if (vm.currentTask) {
            var t = vm.currentTask;
            if (currentTime >= t.endTime) {
                t.status = 'completed';
                t.cost = calculateTaskCost(t);
                completedTasks.push(t);
                vm.availableCores += t.cpuRequired;
                vm.availableRam += t.ramRequired;
                vm.currentTask = null;
            }
        }
    }

    // schedule pending tasks onto available VMs
    for (var j = 0; j < pendingTasks.length; j++) {
        var task = pendingTasks[j];
        if (task.status === 'pending') {
            var availableVM = null;
            for (var k = 0; k < vms.length; k++) {
                var vm2 = vms[k];
                if (vm2.currentTask === null &&
                    vm2.availableCores >= task.cpuRequired &&
                    vm2.availableRam >= task.ramRequired) {
                    availableVM = vm2;
                    break;
                }
            }

            if (availableVM) {
                task.status = 'running';
                task.startTime = task.startTime || currentTime;
                task.endTime = currentTime + task.executionTime;
                availableVM.currentTask = task;
                availableVM.availableCores -= task.cpuRequired;
                availableVM.availableRam -= task.ramRequired;
            }
        }
    }

    updateTaskList();
    updateStats();
    updateCharts();

    var allCompleted = tasks.every(function(x) { return x.status === 'completed'; });
    if (allCompleted) {
        stopSimulation();
    }
}

/* Round robin simulation */
function simulateRoundRobin() {
    currentTime += 0.1;

    for (var i = 0; i < vms.length; i++) {
        var vm = vms[i];
        if (vm.currentTask) {
            var t = vm.currentTask;
            t.quantumUsed += 0.1;
            t.remainingTime -= 0.1;

            if (t.remainingTime <= 0.01) {
                t.status = 'completed';
                t.endTime = currentTime;
                t.remainingTime = 0;
                t.cost = calculateTaskCost(t);
                completedTasks.push(t);
                vm.availableCores += t.cpuRequired;
                vm.availableRam += t.ramRequired;
                vm.currentTask = null;
            } else if (t.quantumUsed >= timeQuantum) {
                t.status = 'pending';
                t.quantumUsed = 0;
                vm.availableCores += t.cpuRequired;
                vm.availableRam += t.ramRequired;
                vm.currentTask = null;
                taskQueue.push(t);
            }
        }
    }

    while (taskQueue.length > 0) {
        var qtask = taskQueue[0];
        if (qtask.status === 'completed') {
            taskQueue.shift();
            continue;
        }

        var avail = null;
        for (var j = 0; j < vms.length; j++) {
            var v = vms[j];
            if (v.currentTask === null &&
                v.availableCores >= qtask.cpuRequired &&
                v.availableRam >= qtask.ramRequired) {
                avail = v;
                break;
            }
        }

        if (avail) {
            taskQueue.shift();
            qtask.status = 'running';
            qtask.startTime = qtask.startTime || currentTime;
            qtask.quantumUsed = 0;
            avail.currentTask = qtask;
            avail.availableCores -= qtask.cpuRequired;
            avail.availableRam -= qtask.ramRequired;
        } else {
            break;
        }
    }

    updateTaskList();
    updateStats();
    updateCharts();

    var allCompleted = tasks.every(function(x) { return x.status === 'completed'; });
    if (allCompleted && taskQueue.length === 0) {
        stopSimulation();
    }
}

/* stop simulation */
function stopSimulation() {
    isSimulating = false;
    clearInterval(simulationInterval);
    document.getElementById('simStatus').textContent = 'Completed';
    // ensure final stats & charts updated
    updateStats();
    updateCharts();
}

/* reset everything */
function resetSimulation() {
    stopSimulation();
    tasks = [];
    completedTasks = [];
    currentTime = 0;
    taskQueue = [];
    for (var i = 0; i < vms.length; i++) {
        vms[i].availableCores = vms[i].totalCores;
        vms[i].availableRam = vms[i].totalRam;
        vms[i].currentTask = null;
    }
    document.getElementById('simStatus').textContent = 'Idle';
    updateTaskList();
    updateStats();

    if (utilizationChart) {
        utilizationChart.data.labels = [];
        utilizationChart.data.datasets[0].data = [];
        utilizationChart.data.datasets[1].data = [];
        utilizationChart.update();
    }
    if (timelineChart) {
        timelineChart.data.labels = [];
        timelineChart.data.datasets[0].data = [];
        timelineChart.data.datasets[1].data = [];
        timelineChart.update();
    }
    if (costChart) {
        costChart.data.labels = [];
        costChart.data.datasets[0].data = [];
        costChart.update();
    }
}

/* update stats shown in UI */
function updateStats() {
    // total tasks includes pending + completed
    var totalTasks = tasks.length;
    var completed = completedTasks.length;

    var avgWait = 0;
    var avgTurnaround = 0;
    var totalCost = 0;

    if (completedTasks.length > 0) {
        avgWait = completedTasks.reduce(function(acc, t) {
            return acc + ((t.startTime || 0) - (t.arrivalTime || 0));
        }, 0) / completedTasks.length;

        avgTurnaround = completedTasks.reduce(function(acc, t) {
            return acc + ((t.endTime || t.startTime || 0) - (t.arrivalTime || 0));
        }, 0) / completedTasks.length;

        totalCost = completedTasks.reduce(function(acc, t) {
            return acc + (t.cost || 0);
        }, 0);
    }

    // CPU & RAM utilization
    var cpuUtil = 0;
    var ramUtil = 0;
    if (vms.length > 0) {
        var totalCpu = vms.reduce(function(acc, vm) { return acc + vm.totalCores; }, 0);
        var usedCpu = vms.reduce(function(acc, vm) { return acc + (vm.totalCores - vm.availableCores); }, 0);
        var totalRam = vms.reduce(function(acc, vm) { return acc + vm.totalRam; }, 0);
        var usedRam = vms.reduce(function(acc, vm) { return acc + (vm.totalRam - vm.availableRam); }, 0);

        cpuUtil = totalCpu > 0 ? (usedCpu / totalCpu) * 100 : 0;
        ramUtil = totalRam > 0 ? (usedRam / totalRam) * 100 : 0;
    }

    document.getElementById('totalTasks').textContent = totalTasks;
    document.getElementById('completedTasks').textContent = completed;
    document.getElementById('avgWaitTime').textContent = (avgWait).toFixed(1) + 's';
    document.getElementById('avgTurnaround').textContent = (avgTurnaround).toFixed(1) + 's';
    document.getElementById('cpuUtilization').textContent = cpuUtil.toFixed(1) + '%';
    document.getElementById('ramUtilization').textContent = ramUtil.toFixed(1) + '%';
    document.getElementById('totalCost').textContent = '₹' + totalCost.toFixed(2);
    document.getElementById('avgCostPerTask').textContent = completed > 0 ? '₹' + (totalCost / completed).toFixed(2) : '₹0.00';
}

/* update charts (utilization, timeline, cost) */
function updateCharts() {
    // add a utilization sample
    if (utilizationChart) {
        var label = (currentTime).toFixed(1) + 's';
        var totalCpu = vms.reduce(function(acc, vm) { return acc + vm.totalCores; }, 0);
        var usedCpu = vms.reduce(function(acc, vm) { return acc + (vm.totalCores - vm.availableCores); }, 0);
        var totalRam = vms.reduce(function(acc, vm) { return acc + vm.totalRam; }, 0);
        var usedRam = vms.reduce(function(acc, vm) { return acc + (vm.totalRam - vm.availableRam); }, 0);

        var cpuPct = totalCpu > 0 ? (usedCpu / totalCpu) * 100 : 0;
        var ramPct = totalRam > 0 ? (usedRam / totalRam) * 100 : 0;

        // push samples (keep last 60)
        utilizationChart.data.labels.push(label);
        utilizationChart.data.datasets[0].data.push(cpuPct.toFixed(2));
        utilizationChart.data.datasets[1].data.push(ramPct.toFixed(2));
        if (utilizationChart.data.labels.length > 60) {
            utilizationChart.data.labels.shift();
            utilizationChart.data.datasets[0].data.shift();
            utilizationChart.data.datasets[1].data.shift();
        }
        utilizationChart.update();
    }

    // timeline: for completed tasks, show wait vs exec
    if (timelineChart) {
        var names = completedTasks.map(function(t) { return t.name; });
        var waits = completedTasks.map(function(t) { return ((t.startTime || 0) - (t.arrivalTime || 0)).toFixed(2); });
        var execs = completedTasks.map(function(t) { return (t.executionTime || 0).toFixed(2); });

        timelineChart.data.labels = names;
        timelineChart.data.datasets[0].data = waits;
        timelineChart.data.datasets[1].data = execs;
        timelineChart.update();
    }

    // cost chart
    if (costChart) {
        var labels = completedTasks.map(function(t) { return t.name; });
        var costs = completedTasks.map(function(t) { return (t.cost || 0).toFixed(2); });

        costChart.data.labels = labels;
        costChart.data.datasets[0].data = costs;
        costChart.update();
    }
}

/* client-side PDF generation using html2canvas + jsPDF
   NOTE: index.html must include:
   <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
   <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
*/
function generatePDF() {
    if (completedTasks.length === 0) {
        alert('No completed tasks to report.');
        return;
    }

    var reportArea = document.querySelector('.container');
    if (!reportArea) {
        alert('Report area not found.');
        return;
    }

    // show a quick status
    document.getElementById('simStatus').textContent = 'Generating PDF...';

    html2canvas(reportArea, { scale: 2 }).then(function(canvas) {
        var imgData = canvas.toDataURL('image/png');
        var pdf = new jspdf.jsPDF('p', 'mm', 'a4');
        var imgProps = pdf.getImageProperties(imgData);
        var pdfWidth = pdf.internal.pageSize.getWidth();
        var pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        var filename = 'cloudvista_report_' + (new Date()).toISOString().replace(/[:.]/g, '-') + '.pdf';
        pdf.save(filename);
        document.getElementById('simStatus').textContent = 'Completed';
    }).catch(function(err) {
        console.error(err);
        alert('Failed to generate PDF: ' + err);
        document.getElementById('simStatus').textContent = 'Completed';
    });
}

/* save simulation to backend (POST to /api/simulation/save)
   Backend expects completed tasks & scheduler info; minimal payload below.
*/
function saveSimulation() {
    if (completedTasks.length === 0) {
        alert('No completed tasks to save.');
        return;
    }

    var scheduler = document.getElementById('scheduler').value || 'unknown';

    // build payload
    var payload = {
        scheduler: scheduler,
        completedTasks: completedTasks.map(function(t) {
            return {
                id: t.id,
                name: t.name,
                cpu_required: t.cpuRequired,
                ram_required: t.ramRequired,
                execution_time: t.executionTime,
                priority: t.priority,
                start_time: t.startTime,
                end_time: t.endTime,
                cost: t.cost
            };
        })
    };

    fetch('/api/simulation/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(function(res) {
        return res.json();
    }).then(function(js) {
        if (js.success) {
            alert('Simulation saved, id: ' + (js.simulation_id || 'unknown'));
        } else {
            alert('Save failed: ' + (js.message || JSON.stringify(js)));
        }
    }).catch(function(err) {
        console.error('Save error:', err);
        alert('Failed to save simulation. Is backend running?');
    });
}

/* initialize charts & basic UI on load */
window.addEventListener('load', function() {
    initCharts();
    updateTaskList();
    updateStats();
});
