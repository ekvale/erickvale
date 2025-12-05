// Global variables
const API_BASE = '/apps/emergency/api';
let map;
let riskMarkersCluster;
let podMarkers = [];
let podCircles = [];
let riskMarkers = [];
let activeScenario = null;
let pods = [];
let scenarios = [];

/**
 * Initialize Leaflet map
 */
function initMap() {
    try {
        const mapElement = document.getElementById('map');
        if (!mapElement) {
            console.error('Map container element not found');
            return;
        }
        
        // Check if map already exists
        if (mapElement._leaflet_id) {
            if (window.mapInstance && window.mapInstance._container) {
                map = window.mapInstance;
                map.invalidateSize();
                return;
            }
            if (window.map && window.map._container) {
                map = window.map;
                map.invalidateSize();
                return;
            }
        }
        
        if (typeof L === 'undefined') {
            console.error('Leaflet library not loaded');
            mapElement.innerHTML = '<div style="padding: 20px; text-align: center; color: #ef4444;"><strong>Error:</strong> Map library failed to load. Please refresh the page.</div>';
            return;
        }
        
        // Set map container dimensions
        const mapContainer = mapElement.parentElement;
        if (mapContainer) {
            mapContainer.style.height = '600px';
            mapContainer.style.width = '100%';
        }
        mapElement.style.width = '100%';
        mapElement.style.height = '600px';
        mapElement.style.position = 'absolute';
        mapElement.style.top = '0';
        mapElement.style.left = '0';
        mapElement.style.zIndex = '1';
        
        // Don't create if already initialized
        if (mapElement._leaflet_id) {
            return;
        }
        
        // Create map
        map = L.map('map', {
            center: [46.7296, -94.6859],
            zoom: 6,
            zoomControl: true
        });
        
        window.mapInstance = map;
        window.map = map;
        
        // Add tile layer if not already added
        let tileLayerExists = false;
        map.eachLayer((layer) => {
            if (layer instanceof L.TileLayer) {
                tileLayerExists = true;
            }
        });
        
        if (!tileLayerExists) {
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(map);
        }
        
        // Initialize marker clusters
        if (typeof L.markerClusterGroup !== 'undefined' && !riskMarkersCluster) {
            riskMarkersCluster = L.markerClusterGroup({
                chunkedLoading: true,
                maxClusterRadius: 50
            });
            map.addLayer(riskMarkersCluster);
        }
        
        // Force size recalculation
        setTimeout(() => {
            if (map) {
                map.invalidateSize();
            }
        }, 300);
        
    } catch (error) {
        console.error('Error initializing map:', error);
        const mapEl = document.getElementById('map');
        if (mapEl) {
            mapEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #ef4444;"><strong>Error:</strong> ' + error.message + '</div>';
        }
    }
}

// Make functions globally accessible
if (typeof window !== 'undefined') {
    window.initMap = initMap;
}

/**
 * Load risk data from API
 */
async function loadRiskData(scenarioId = null) {
    try {
        const url = scenarioId 
            ? `${API_BASE}/risk-data/?scenario_id=${scenarioId}`
            : `${API_BASE}/risk-data/`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Clear existing risk markers
        if (riskMarkersCluster) {
            riskMarkersCluster.clearLayers();
        }
        riskMarkers = [];
        
        // Add risk markers
        data.forEach(city => {
            const risk = city.risk_score;
            const color = getRiskColor(risk);
            
            const marker = L.circleMarker([city.lat, city.lon], {
                radius: 6,
                fillColor: color,
                color: '#fff',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.7
            });
            
            marker.bindPopup(`
                <strong>${city.name}</strong><br>
                Population: ${city.population.toLocaleString()}<br>
                Risk Score: ${risk.toFixed(3)}<br>
                County: ${city.county}
            `);
            
            riskMarkers.push(marker);
            if (riskMarkersCluster) {
                riskMarkersCluster.addLayer(marker);
            }
        });
    } catch (error) {
        console.error('Error loading risk data:', error);
    }
}

/**
 * Get color based on risk score
 */
function getRiskColor(risk) {
    if (risk < 0.2) return '#4CAF50';
    if (risk < 0.4) return '#8BC34A';
    if (risk < 0.6) return '#FFC107';
    if (risk < 0.8) return '#FF9800';
    return '#F44336';
}

/**
 * Load PODs from API
 */
async function loadPODs() {
    try {
        const response = await fetch(`${API_BASE}/pods/`);
        const data = await response.json();
        pods = data.results || data;
        
        updatePODsList();
        updatePODsOnMap();
    } catch (error) {
        console.error('Error loading PODs:', error);
    }
}

/**
 * Update PODs on map
 */
function updatePODsOnMap() {
    if (!map) return;
    
    // Remove existing POD markers and circles
    podMarkers.forEach(marker => map.removeLayer(marker));
    podCircles.forEach(circle => map.removeLayer(circle));
    podMarkers = [];
    podCircles = [];
    
    // Add POD markers and coverage circles
    pods.forEach((pod, index) => {
        const lat = parseFloat(pod.latitude);
        const lon = parseFloat(pod.longitude);
        
        // Color-code by infrastructure score if available
        let markerColor = '#667eea';
        if (pod.infrastructure_score !== undefined) {
            const score = pod.infrastructure_score;
            if (score >= 0.8) markerColor = '#4CAF50';
            else if (score >= 0.6) markerColor = '#8BC34A';
            else if (score >= 0.4) markerColor = '#FFC107';
            else markerColor = '#FF9800';
        }
        
        // Add marker
        const marker = L.marker([lat, lon], {
            icon: L.divIcon({
                className: 'pod-marker',
                html: `<div style="background: ${markerColor}; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);" title="Infrastructure: ${pod.infrastructure_score ? (pod.infrastructure_score * 100).toFixed(0) + '%' : 'N/A'}">${index + 1}</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        });
        
        let popupContent = `
            <strong>${pod.name}</strong><br>
            Status: ${pod.status}<br>
            Coverage Radius: ${pod.coverage_radius} km<br>
            Points Covered: ${pod.points_covered}<br>
            Population Covered: ${pod.total_population_covered.toLocaleString()}<br>
        `;
        
        if (pod.vulnerable_population_covered) {
            popupContent += `Vulnerable Population: ${pod.vulnerable_population_covered.toLocaleString()}<br>`;
        }
        if (pod.infrastructure_score !== undefined) {
            popupContent += `Infrastructure Score: ${(pod.infrastructure_score * 100).toFixed(1)}%<br>`;
        }
        if (pod.estimated_capacity) {
            popupContent += `Estimated Capacity: ${pod.estimated_capacity.toLocaleString()}/day<br>`;
        }
        if (pod.capacity_utilization !== undefined) {
            popupContent += `Capacity Utilization: ${(pod.capacity_utilization * 100).toFixed(1)}%<br>`;
        }
        if (pod.redundancy_score !== undefined) {
            popupContent += `Redundancy Score: ${(pod.redundancy_score * 100).toFixed(1)}%<br>`;
        }
        
        popupContent += `
            Avg Drive Time: ${pod.avg_drive_time.toFixed(1)} min<br>
            Max Drive Time: ${pod.max_drive_time.toFixed(1)} min<br>
            <button onclick="editPOD(${pod.id})" style="margin-top: 10px; padding: 5px 10px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">Edit</button>
            <button onclick="deletePOD(${pod.id})" style="margin-top: 10px; padding: 5px 10px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">Delete</button>
        `;
        
        marker.bindPopup(popupContent);
        podMarkers.push(marker);
        map.addLayer(marker);
        
        // Add coverage circle if enabled
        const showCoverage = document.getElementById('show-coverage');
        if (showCoverage && showCoverage.checked) {
            const circle = L.circle([lat, lon], {
                radius: pod.coverage_radius * 1000,
                color: '#667eea',
                fillColor: '#667eea',
                fillOpacity: 0.1,
                weight: 2
            });
            podCircles.push(circle);
            map.addLayer(circle);
        }
    });
    
    updateCoverageStats();
}

/**
 * Update coverage statistics in header
 */
function updateCoverageStats() {
    try {
        const totalPopulation = pods.reduce((sum, pod) => sum + (pod.total_population_covered || 0), 0);
        const totalPods = pods.length;
        const estimatedTotalPopulation = 5700000;
        const coveragePercentage = totalPopulation > 0 ? Math.min(100, (totalPopulation / estimatedTotalPopulation * 100)) : 0;
        
        const statsDiv = document.getElementById('coverage-stats');
        const coveragePercentEl = document.getElementById('coverage-percentage');
        const totalCoveredEl = document.getElementById('total-covered');
        const totalPodsEl = document.getElementById('total-pods-count');
        
        if (statsDiv && coveragePercentEl && totalCoveredEl && totalPodsEl) {
            coveragePercentEl.textContent = coveragePercentage.toFixed(1) + '%';
            totalCoveredEl.textContent = totalPopulation.toLocaleString();
            totalPodsEl.textContent = totalPods;
            statsDiv.style.display = totalPods > 0 ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error updating coverage stats:', error);
    }
}

/**
 * Update PODs list in sidebar
 */
function updatePODsList() {
    const list = document.getElementById('pods-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    pods.forEach(pod => {
        const item = document.createElement('div');
        item.className = 'pod-item';
        let itemHtml = `
            <h4>${pod.name}</h4>
            <p><strong>Status:</strong> ${pod.status}</p>
            <p><strong>Coverage:</strong> ${pod.points_covered} points, ${pod.total_population_covered.toLocaleString()} people</p>
        `;
        
        if (pod.vulnerable_population_covered) {
            itemHtml += `<p><strong>Vulnerable Population:</strong> ${pod.vulnerable_population_covered.toLocaleString()}</p>`;
        }
        if (pod.infrastructure_score !== undefined) {
            itemHtml += `<p><strong>Infrastructure:</strong> ${(pod.infrastructure_score * 100).toFixed(1)}%</p>`;
        }
        if (pod.estimated_capacity) {
            itemHtml += `<p><strong>Capacity:</strong> ${pod.estimated_capacity.toLocaleString()}/day`;
            if (pod.capacity_utilization !== undefined) {
                itemHtml += ` (${(pod.capacity_utilization * 100).toFixed(1)}% utilized)`;
            }
            itemHtml += `</p>`;
        }
        
        itemHtml += `
            <p><strong>Drive Time:</strong> ${pod.avg_drive_time.toFixed(1)} min avg, ${pod.max_drive_time.toFixed(1)} min max</p>
            <div class="item-actions">
                <button class="btn-edit" onclick="editPOD(${pod.id})">Edit</button>
                <button class="btn-delete" onclick="deletePOD(${pod.id})">Delete</button>
            </div>
        `;
        
        item.innerHTML = itemHtml;
        list.appendChild(item);
    });
}

/**
 * Load scenarios from API
 */
async function loadScenarios() {
    try {
        const response = await fetch(`${API_BASE}/scenarios/`);
        const data = await response.json();
        scenarios = data.results || data;
        
        updateScenariosList();
        updateScenarioDropdown();
    } catch (error) {
        console.error('Error loading scenarios:', error);
    }
}

/**
 * Update scenarios list in sidebar
 */
function updateScenariosList() {
    const list = document.getElementById('scenarios-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    scenarios.forEach(scenario => {
        const item = document.createElement('div');
        item.className = 'scenario-item';
        item.innerHTML = `
            <h4>${scenario.name}</h4>
            <p><strong>Type:</strong> ${scenario.type.replace('_', ' ')}</p>
            <p><strong>Severity:</strong> ${scenario.severity}</p>
            <p><strong>PODs:</strong> ${scenario.pods ? scenario.pods.length : 0}</p>
            <div class="item-actions">
                <button class="btn-edit" onclick="editScenario(${scenario.id})">Edit</button>
                <button class="btn-delete" onclick="deleteScenario(${scenario.id})">Delete</button>
            </div>
        `;
        list.appendChild(item);
    });
}

/**
 * Update scenario dropdown
 */
function updateScenarioDropdown() {
    const select = document.getElementById('active-scenario');
    if (!select) return;
    
    select.innerHTML = '<option value="">None</option>';
    
    scenarios.forEach(scenario => {
        const option = document.createElement('option');
        option.value = scenario.id;
        option.textContent = scenario.name;
        if (activeScenario && activeScenario.id === scenario.id) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

/**
 * Generate optimal PODs
 */
async function generateOptimalPODs() {
    try {
        const numPodsEl = document.getElementById('num-pods');
        const maxDriveTimeEl = document.getElementById('max-drive-time');
        const showGapAnalysisEl = document.getElementById('show-gap-analysis');
        
        if (!numPodsEl || !maxDriveTimeEl) {
            alert('Error: Form elements not found. Please refresh the page.');
            return;
        }
        
        if (!map) {
            alert('Error: Map is not initialized. Please wait for the map to load.');
            return;
        }
        
        const numPods = parseInt(numPodsEl.value) || 5;
        const maxDriveTime = parseFloat(maxDriveTimeEl.value) || 60;
        const scenarioId = activeScenario ? activeScenario.id : null;
        const showGapAnalysis = showGapAnalysisEl?.checked ?? true;
        
        let url = `${API_BASE}/pods/optimal/?num_pods=${numPods}&max_drive_time=${maxDriveTime}&analyze_gaps=${showGapAnalysis}`;
        if (scenarioId) {
            url += `&scenario_id=${scenarioId}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        const optimalPODs = result.pods || result;
        const summary = result.summary || null;
        const gapAnalysis = result.gap_analysis || null;
        
        // Create PODs from optimal locations
        for (const podData of optimalPODs) {
            await createPOD(podData);
        }
        
        await loadPODs();
        
        // Show summary
        let message = `Generated ${optimalPODs.length} optimal PODs!\n\n`;
        if (summary) {
            message += `Summary:\n`;
            message += `- Total Population Covered: ${summary.total_population_covered.toLocaleString()}\n`;
            message += `- Total Risk Covered: ${summary.total_risk_covered.toFixed(2)}\n`;
            message += `- Avg Infrastructure Score: ${(summary.avg_infrastructure_score * 100).toFixed(1)}%\n`;
        }
        if (gapAnalysis) {
            message += `\nCoverage Analysis:\n`;
            message += `- Coverage: ${gapAnalysis.coverage_percentage}%\n`;
            message += `- Uncovered Population: ${gapAnalysis.uncovered_population.toLocaleString()}\n`;
            if (gapAnalysis.critical_gaps && gapAnalysis.critical_gaps.length > 0) {
                message += `- Critical Gaps: ${gapAnalysis.gap_count} areas\n`;
            }
        }
        
        alert(message);
    } catch (error) {
        console.error('Error generating optimal PODs:', error);
        alert('Error generating optimal PODs: ' + (error.message || 'Unknown error'));
    }
}

// Make functions globally accessible
if (typeof window !== 'undefined') {
    window.generateOptimalPODs = generateOptimalPODs;
}

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Get CSRF token
 */
function getCSRFToken() {
    // Try to get from global variable first (set in template)
    if (typeof csrftoken !== 'undefined' && csrftoken) {
        console.log('Using CSRF token from global variable');
        return csrftoken;
    }
    
    // Try hidden input from {% csrf_token %} template tag
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput && csrfInput.value) {
        console.log('Using CSRF token from hidden input');
        return csrfInput.value;
    }
    
    // Fallback to cookie
    const cookieToken = getCookie('csrftoken');
    if (cookieToken) {
        console.log('Using CSRF token from cookie');
        return cookieToken;
    }
    
    console.error('CSRF token not found! Available cookies:', document.cookie);
    return null;
}

/**
 * Create POD
 */
async function createPOD(podData) {
    try {
        const csrfToken = getCSRFToken();
        
        if (!csrfToken) {
            throw new Error('CSRF token not found. Please refresh the page.');
        }
        
        console.log('Creating POD with CSRF token:', csrfToken.substring(0, 10) + '...');
        
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        };
        
        const response = await fetch(`${API_BASE}/pods/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(podData),
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            let error;
            try {
                error = JSON.parse(errorText);
            } catch {
                error = { detail: errorText };
            }
            console.error('POD creation failed:', error);
            throw new Error(error.detail || errorText || 'Failed to create POD');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error creating POD:', error);
        throw error;
    }
}

/**
 * Edit POD
 */
async function editPOD(id) {
    const pod = pods.find(p => p.id === id);
    if (!pod) return;
    
    document.getElementById('pod-id').value = pod.id;
    document.getElementById('pod-name').value = pod.name;
    document.getElementById('pod-lat').value = pod.latitude;
    document.getElementById('pod-lon').value = pod.longitude;
    document.getElementById('pod-radius').value = pod.coverage_radius;
    document.getElementById('pod-status').value = pod.status;
    document.getElementById('pod-occupancy').value = pod.occupancy || 0;
    document.getElementById('pod-parking').value = pod.parking_lot_size || 0;
    document.getElementById('pod-acreage').value = pod.acreage || 0;
    document.getElementById('pod-modal-title').textContent = 'Edit POD';
    document.getElementById('pod-modal').classList.add('show');
}

/**
 * Delete POD
 */
async function deletePOD(id) {
    if (!confirm('Are you sure you want to delete this POD?')) return;
    
    try {
        const csrfToken = getCSRFToken();
        const headers = {};
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch(`${API_BASE}/pods/${id}/`, {
            method: 'DELETE',
            headers: headers,
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            await loadPODs();
        } else {
            alert('Error deleting POD');
        }
    } catch (error) {
        console.error('Error deleting POD:', error);
        alert('Error deleting POD');
    }
}

/**
 * Edit Scenario
 */
async function editScenario(id) {
    const scenario = scenarios.find(s => s.id === id);
    if (!scenario) return;
    
    document.getElementById('scenario-id').value = scenario.id;
    document.getElementById('scenario-name').value = scenario.name;
    document.getElementById('scenario-description').value = scenario.description || '';
    document.getElementById('scenario-type').value = scenario.type;
    document.getElementById('scenario-severity').value = scenario.severity;
    document.getElementById('scenario-areas').value = Array.isArray(scenario.affected_areas) 
        ? scenario.affected_areas.join(', ') 
        : (scenario.affected_areas || '');
    
    updateScenarioPODsList(scenario.pods || []);
    document.getElementById('scenario-modal-title').textContent = 'Edit Scenario';
    document.getElementById('scenario-modal').classList.add('show');
}

/**
 * Update scenario PODs list
 */
function updateScenarioPODsList(selectedPODs) {
    const list = document.getElementById('scenario-pods-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    pods.forEach(pod => {
        const checked = selectedPODs.some(p => p.id === pod.id);
        const checkbox = document.createElement('div');
        checkbox.innerHTML = `
            <label>
                <input type="checkbox" value="${pod.id}" ${checked ? 'checked' : ''}>
                ${pod.name}
            </label>
        `;
        list.appendChild(checkbox);
    });
}

/**
 * Delete Scenario
 */
async function deleteScenario(id) {
    if (!confirm('Are you sure you want to delete this scenario?')) return;
    
    try {
        const csrfToken = getCSRFToken();
        const headers = {};
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch(`${API_BASE}/scenarios/${id}/`, {
            method: 'DELETE',
            headers: headers,
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            await loadScenarios();
            if (activeScenario && activeScenario.id === id) {
                activeScenario = null;
                document.getElementById('active-scenario').value = '';
                await loadRiskData();
            }
        } else {
            alert('Error deleting scenario');
        }
    } catch (error) {
        console.error('Error deleting scenario:', error);
        alert('Error deleting scenario');
    }
}

/**
 * Analyze scenario
 */
async function analyzeScenario() {
    const scenarioId = document.getElementById('active-scenario').value;
    if (!scenarioId) {
        alert('Please select a scenario first');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/scenarios/${scenarioId}/analyze/`);
        const analysis = await response.json();
        
        alert(`
Scenario Analysis: ${analysis.scenario_name}

Number of PODs: ${analysis.num_pods}
Points Covered: ${analysis.total_points_covered}
Population Covered: ${analysis.total_population_covered.toLocaleString()}
Coverage Percentage: ${analysis.coverage_percentage}%
Average Drive Time: ${analysis.avg_drive_time} minutes
Max Drive Time: ${analysis.max_drive_time} minutes
Cities Covered: ${analysis.cities_covered} / ${analysis.total_cities}
        `);
    } catch (error) {
        console.error('Error analyzing scenario:', error);
        alert('Error analyzing scenario');
    }
}

/**
 * Initialize app
 */
function initializeApp() {
    if (typeof L === 'undefined') {
        setTimeout(initializeApp, 500);
        return;
    }
    
    initMap();
    
    setTimeout(() => {
        if (map) {
            loadRiskData();
            loadPODs();
            loadScenarios();
        }
    }, 500);
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            const tabPane = document.getElementById(`${tab}-tab`);
            if (tabPane) {
                tabPane.classList.add('active');
            }
        });
    });
    
    // Generate optimal PODs
    const generateBtn = document.getElementById('generate-optimal');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateOptimalPODs);
    }
    
    // Add POD
    const addPodBtn = document.getElementById('add-pod');
    if (addPodBtn) {
        addPodBtn.addEventListener('click', () => {
            const podForm = document.getElementById('pod-form');
            const podId = document.getElementById('pod-id');
            const podModalTitle = document.getElementById('pod-modal-title');
            const podModal = document.getElementById('pod-modal');
            
            if (podForm) podForm.reset();
            if (podId) podId.value = '';
            if (podModalTitle) podModalTitle.textContent = 'Add POD';
            if (podModal) podModal.classList.add('show');
        });
    }
    
    // POD form submission
    const podForm = document.getElementById('pod-form');
    if (podForm) {
        podForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const podData = {
                name: document.getElementById('pod-name').value,
                latitude: parseFloat(document.getElementById('pod-lat').value),
                longitude: parseFloat(document.getElementById('pod-lon').value),
                coverage_radius: parseFloat(document.getElementById('pod-radius').value),
                status: document.getElementById('pod-status').value,
                occupancy: parseInt(document.getElementById('pod-occupancy').value) || 0,
                parking_lot_size: parseFloat(document.getElementById('pod-parking').value) || 0,
                acreage: parseFloat(document.getElementById('pod-acreage').value) || 0,
            };
            
            const podId = document.getElementById('pod-id').value;
            
            try {
                const url = podId ? `${API_BASE}/pods/${podId}/` : `${API_BASE}/pods/`;
                const method = podId ? 'PUT' : 'POST';
                const csrfToken = getCSRFToken();
                const headers = {
                    'Content-Type': 'application/json',
                };
                
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }
                
                const response = await fetch(url, {
                    method: method,
                    headers: headers,
                    body: JSON.stringify(podData),
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    document.getElementById('pod-modal').classList.remove('show');
                    await loadPODs();
                } else {
                    const error = await response.json();
                    alert('Error saving POD: ' + (error.detail || JSON.stringify(error)));
                }
            } catch (error) {
                console.error('Error saving POD:', error);
                alert('Error saving POD');
            }
        });
    }
    
    // Add Scenario
    const addScenarioBtn = document.getElementById('add-scenario');
    if (addScenarioBtn) {
        addScenarioBtn.addEventListener('click', () => {
            document.getElementById('scenario-form').reset();
            document.getElementById('scenario-id').value = '';
            document.getElementById('scenario-severity').value = '1.0';
            updateScenarioPODsList([]);
            const modalTitle = document.getElementById('scenario-modal-title');
            const modal = document.getElementById('scenario-modal');
            if (modalTitle) modalTitle.textContent = 'Add Scenario';
            if (modal) modal.classList.add('show');
        });
    }
    
    // Scenario form submission
    const scenarioForm = document.getElementById('scenario-form');
    if (scenarioForm) {
        scenarioForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const affectedAreas = document.getElementById('scenario-areas').value
                .split(',')
                .map(area => area.trim())
                .filter(area => area);
            
            const podCheckboxes = document.querySelectorAll('#scenario-pods-list input[type="checkbox"]:checked');
            const podIds = Array.from(podCheckboxes).map(cb => parseInt(cb.value));
            
            const scenarioData = {
                name: document.getElementById('scenario-name').value,
                description: document.getElementById('scenario-description').value,
                type: document.getElementById('scenario-type').value,
                severity: parseFloat(document.getElementById('scenario-severity').value),
                affected_areas: affectedAreas,
                pod_ids: podIds
            };
            
            const scenarioId = document.getElementById('scenario-id').value;
            
            try {
                const url = scenarioId ? `${API_BASE}/scenarios/${scenarioId}/` : `${API_BASE}/scenarios/`;
                const method = scenarioId ? 'PUT' : 'POST';
                const csrfToken = getCSRFToken();
                const headers = {
                    'Content-Type': 'application/json',
                };
                
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }
                
                const response = await fetch(url, {
                    method: method,
                    headers: headers,
                    body: JSON.stringify(scenarioData),
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    document.getElementById('scenario-modal').classList.remove('show');
                    await loadScenarios();
                } else {
                    const error = await response.json();
                    alert('Error saving scenario: ' + (error.detail || JSON.stringify(error)));
                }
            } catch (error) {
                console.error('Error saving scenario:', error);
                alert('Error saving scenario');
            }
        });
    }
    
    // Active scenario change
    const activeScenarioSelect = document.getElementById('active-scenario');
    if (activeScenarioSelect) {
        activeScenarioSelect.addEventListener('change', async (e) => {
            const scenarioId = e.target.value;
            if (scenarioId) {
                activeScenario = scenarios.find(s => s.id === parseInt(scenarioId));
                await loadRiskData(scenarioId);
            } else {
                activeScenario = null;
                await loadRiskData();
            }
        });
    }
    
    // Analyze scenario
    const analyzeBtn = document.getElementById('analyze-scenario');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeScenario);
    }
    
    // Toggle risk points
    const showRiskPoints = document.getElementById('show-risk-points');
    if (showRiskPoints) {
        showRiskPoints.addEventListener('change', (e) => {
            if (e.target.checked) {
                riskMarkers.forEach(marker => {
                    if (riskMarkersCluster) {
                        riskMarkersCluster.addLayer(marker);
                    }
                });
            } else {
                if (riskMarkersCluster) {
                    riskMarkersCluster.clearLayers();
                }
            }
        });
    }
    
    // Toggle coverage areas
    const showCoverage = document.getElementById('show-coverage');
    if (showCoverage) {
        showCoverage.addEventListener('change', () => {
            updatePODsOnMap();
        });
    }
    
    // Info button
    const infoBtn = document.getElementById('info-btn');
    if (infoBtn) {
        infoBtn.addEventListener('click', () => {
            const modal = document.getElementById('info-modal');
            if (modal) modal.classList.add('show');
        });
    }
    
    // Close modals
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) modal.classList.remove('show');
        });
    });
    
    const cancelPodBtn = document.getElementById('cancel-pod');
    if (cancelPodBtn) {
        cancelPodBtn.addEventListener('click', () => {
            const modal = document.getElementById('pod-modal');
            if (modal) modal.classList.remove('show');
        });
    }
    
    const cancelScenarioBtn = document.getElementById('cancel-scenario');
    if (cancelScenarioBtn) {
        cancelScenarioBtn.addEventListener('click', () => {
            const modal = document.getElementById('scenario-modal');
            if (modal) modal.classList.remove('show');
        });
    }
    
    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
        }
    });
    
    // Export PODs to CSV
    const exportPodsBtn = document.getElementById('export-pods');
    if (exportPodsBtn) {
        exportPodsBtn.addEventListener('click', () => {
            if (pods.length === 0) {
                alert('No PODs to export');
                return;
            }
            
            const headers = ['Name', 'Latitude', 'Longitude', 'Coverage Radius (km)', 'Status', 
                            'Points Covered', 'Population Covered', 'Avg Drive Time (min)', 
                            'Max Drive Time (min)', 'Infrastructure Score', 'Estimated Capacity'];
            const rows = pods.map(pod => [
                pod.name,
                pod.latitude,
                pod.longitude,
                pod.coverage_radius,
                pod.status,
                pod.points_covered,
                pod.total_population_covered,
                pod.avg_drive_time.toFixed(1),
                pod.max_drive_time.toFixed(1),
                pod.infrastructure_score ? (pod.infrastructure_score * 100).toFixed(1) + '%' : 'N/A',
                pod.estimated_capacity || 'N/A'
            ]);
            
            const csvContent = [
                headers.join(','),
                ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
            ].join('\n');
            
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `pods_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        });
    }
    
    // Clear all PODs
    const clearPodsBtn = document.getElementById('clear-pods');
    if (clearPodsBtn) {
        clearPodsBtn.addEventListener('click', async () => {
            if (pods.length === 0) {
                alert('No PODs to clear');
                return;
            }
            
            if (!confirm(`Are you sure you want to delete all ${pods.length} PODs?`)) {
                return;
            }
            
            for (const pod of pods) {
                try {
                    await fetch(`${API_BASE}/pods/${pod.id}/`, {
                        method: 'DELETE'
                    });
                } catch (error) {
                    console.error(`Error deleting POD ${pod.id}:`, error);
                }
            }
            
            await loadPODs();
            alert('All PODs cleared');
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setTimeout(initializeApp, 200);
});

// Also try on window load as fallback
window.addEventListener('load', () => {
    if (!map) {
        setTimeout(initializeApp, 300);
    }
    
    // Ensure functions are globally accessible
    if (typeof window !== 'undefined') {
        if (typeof generateOptimalPODs === 'function' && typeof window.generateOptimalPODs === 'undefined') {
            window.generateOptimalPODs = generateOptimalPODs;
        }
        if (typeof initMap === 'function' && typeof window.initMap === 'undefined') {
            window.initMap = initMap;
        }
    }
});
