// ==========================================================================
// CONFIGURATION & GLOBAL STATE
// ==========================================================================
const API_BASE = window.location.origin;
let restaurants = [];
let riders = [];
let currentPredictionContext = null;

// Leaflet Map Global references
let map = null;
let mapMarkers = {};
let mapRoutes = [];

// Chart.js references
let speedChart = null;
let trendChart = null;
let shareChart = null;

// Prediction Session Cache
let predictionHistory = [];
let trendCount = 0;

// ==========================================================================
// DOM ELEMENTS
// ==========================================================================
const apiStatusEl = document.getElementById("api-status");
const selectRestaurantEl = document.getElementById("select-restaurant");
const selectRiderEl = document.getElementById("select-rider");
const restInfoEl = document.getElementById("restaurant-info");
const restRatingEl = document.getElementById("rest-rating");
const restCapEl = document.getElementById("rest-cap");
const riderInfoEl = document.getElementById("rider-info");
const riderLoadEl = document.getElementById("rider-load");
const riderCompletedEl = document.getElementById("rider-completed");

const sliderOrderSize = document.getElementById("slider-order-size");
const sliderOrderValue = document.getElementById("slider-order-value");
const valOrderSize = document.getElementById("val-order-size");
const valOrderValue = document.getElementById("val-order-value");

const dropLatEl = document.getElementById("drop-lat");
const dropLonEl = document.getElementById("drop-lon");
const btnMockCoords = document.getElementById("btn-mock-coords");

const btnSubmit = document.getElementById("btn-submit");
const btnText = btnSubmit.querySelector(".btn-text");
const btnSpinner = btnSubmit.querySelector(".btn-spinner");
const simulatorForm = document.getElementById("simulator-form");

const resultsPlaceholder = document.getElementById("results-placeholder");
const resultsPanel = document.getElementById("results-panel");
const etaNumber = document.getElementById("eta-number");
const etaBounds = document.getElementById("eta-bounds");
const etaSummary = document.getElementById("eta-summary");

const metricDist = document.getElementById("metric-dist");
const metricTravel = document.getElementById("metric-travel");
const metricEfficiency = document.getElementById("metric-efficiency");
const metricRider = document.getElementById("metric-rider");

const barDist = document.getElementById("bar-dist");
const barPrep = document.getElementById("bar-prep");
const barTraffic = document.getElementById("bar-traffic");
const barLoad = document.getElementById("bar-load");

const valBarDist = document.getElementById("val-bar-dist");
const valBarPrep = document.getElementById("val-bar-prep");
const valBarTraffic = document.getElementById("val-bar-traffic");
const valBarLoad = document.getElementById("val-bar-load");

// Chat Drawer
const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const suggestBtns = document.querySelectorAll(".suggest-btn");

// Modals
const settingsModal = document.getElementById("settings-modal");
const btnSettings = document.getElementById("btn-settings");
const settingsClose = document.getElementById("settings-close");
const btnSaveSettings = document.getElementById("btn-save-settings");
const geminiKeyInput = document.getElementById("gemini-key-input");

// Tab controls
const tabButtons = document.querySelectorAll(".nav-tab");
const tabPanels = document.querySelectorAll(".tab-panel");

// KPI & Analytics Elements
const kpiRestaurants = document.getElementById("kpi-restaurants");
const kpiRiders = document.getElementById("kpi-riders");
const kpiAvgRating = document.getElementById("kpi-avg-rating");
const kpiCompletedOrders = document.getElementById("kpi-completed-orders");
const historyTbody = document.getElementById("history-tbody");
const btnExportCsv = document.getElementById("btn-export-csv");

// Leaderboards
const leaderboardRestaurantsTbody = document.getElementById("leaderboard-restaurants-tbody");
const leaderboardRidersTbody = document.getElementById("leaderboard-riders-tbody");

// Batch Simulation
const btnRunBatch = document.getElementById("btn-run-batch");
const batchTbody = document.getElementById("batch-tbody");

// ==========================================================================
// TOAST NOTIFICATIONS UTILITIES
// ==========================================================================
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let iconClass = "fa-circle-info text-teal";
    if (type === "success") iconClass = "fa-circle-check text-emerald";
    else if (type === "error") iconClass = "fa-triangle-exclamation text-crimson";

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Fade out and remove
    setTimeout(() => {
        toast.classList.add("fade-out");
        toast.addEventListener("animationend", () => {
            toast.remove();
        });
    }, 3700);
}

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener("DOMContentLoaded", async () => {
    // 1. Initial status checks
    checkServerHealth();
    
    // 2. Load primary lookup data
    await loadLookupData();

    // 3. Initialize interactive Leaflet map
    initMap();

    // 4. Initialize charts (Chart.js)
    initCharts();

    // 5. Setup event handlers
    setupEventListeners();

    // 6. Populate settings api key field if saved
    const savedKey = localStorage.getItem("gemini_api_key");
    if (savedKey) {
        geminiKeyInput.value = savedKey;
    }
});

// Check Health
async function checkServerHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
            apiStatusEl.className = "status-indicator healthy";
            apiStatusEl.querySelector(".status-label").textContent = "API Server Online";
        } else {
            apiStatusEl.className = "status-indicator offline";
            apiStatusEl.querySelector(".status-label").textContent = "API Server Error";
        }
    } catch (e) {
        apiStatusEl.className = "status-indicator offline";
        apiStatusEl.querySelector(".status-label").textContent = "Server Offline";
    }
}

// Fetch Restaurants and Riders to populate selectors
async function loadLookupData() {
    try {
        const [restRes, ridersRes] = await Promise.all([
            fetch(`${API_BASE}/api/restaurants`),
            fetch(`${API_BASE}/api/riders`)
        ]);

        if (restRes.ok && ridersRes.ok) {
            restaurants = await restRes.json();
            riders = await ridersRes.json();

            populateDropdowns();
            renderLeaderboards();
        }
    } catch (e) {
        console.error("Error loading lookup data:", e);
        showToast("Error loading catalog data. Check API connection.", "error");
    }
}

function populateDropdowns() {
    // Populate Restaurants
    selectRestaurantEl.innerHTML = '<option value="" disabled selected>Select a restaurant...</option>';
    restaurants.forEach(rest => {
        const opt = document.createElement("option");
        opt.value = rest.id;
        opt.textContent = `${rest.name} (${rest.cuisine})`;
        selectRestaurantEl.appendChild(opt);
    });

    // Populate Riders
    selectRiderEl.innerHTML = '<option value="" disabled selected>Select a rider...</option>';
    riders.forEach(rider => {
        const opt = document.createElement("option");
        opt.value = rider.id;
        opt.textContent = `${rider.rider_call_sign} (${rider.vehicle_type})`;
        selectRiderEl.appendChild(opt);
    });
}

// ==========================================================================
// INTERACTIVE MAP SERVICES (Leaflet.js)
// ==========================================================================
function initMap() {
    // Bangalore GPS coordinates
    const defaultCenter = [12.9715987, 77.5945627];
    
    // Initialize map
    map = L.map("route-map", {
        zoomControl: true,
        attributionControl: false
    }).setView(defaultCenter, 12);

    // Apply CartoDB Dark Matter tile layer for cohesive premium dark theme
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 20,
        subdomains: "abcd"
    }).addTo(map);

    // Add Attribution at bottom right in smaller font
    L.control.attribution({
        prefix: false
    }).addAttribution('&copy; <a href="https://carto.com/">CARTO</a> | &copy; <a href="https://openstreetmap.org">OSM</a>').addTo(map);
}

function clearMap() {
    // Remove all markers
    Object.keys(mapMarkers).forEach(key => {
        if (mapMarkers[key]) map.removeLayer(mapMarkers[key]);
    });
    mapMarkers = {};

    // Remove all route paths
    mapRoutes.forEach(route => {
        if (route) map.removeLayer(route);
    });
    mapRoutes = [];
}

function updateMap(restLat, restLon, riderLat, riderLon, dropLat, dropLon, restName, riderCallSign) {
    clearMap();

    // Custom FontAwesome Icons for Markers
    const restIcon = L.divIcon({
        html: '<div style="background-color: #6366f1; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #ffffff; box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);"><i class="fa-solid fa-store" style="color: white; font-size: 14px;"></i></div>',
        className: 'custom-map-icon',
        iconSize: [34, 34],
        iconAnchor: [17, 17]
    });

    const riderIcon = L.divIcon({
        html: '<div style="background-color: #ef4444; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #ffffff; box-shadow: 0 0 10px rgba(239, 68, 68, 0.6);"><i class="fa-solid fa-motorcycle" style="color: white; font-size: 14px;"></i></div>',
        className: 'custom-map-icon',
        iconSize: [34, 34],
        iconAnchor: [17, 17]
    });

    const customerIcon = L.divIcon({
        html: '<div style="background-color: #10b981; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #ffffff; box-shadow: 0 0 10px rgba(16, 185, 129, 0.6);"><i class="fa-solid fa-house" style="color: white; font-size: 14px;"></i></div>',
        className: 'custom-map-icon',
        iconSize: [34, 34],
        iconAnchor: [17, 17]
    });

    // Place Markers on Map
    mapMarkers.restaurant = L.marker([restLat, restLon], { icon: restIcon }).addTo(map)
        .bindPopup(`<strong>Restaurant: ${restName}</strong><br>GPS: ${restLat.toFixed(4)}, ${restLon.toFixed(4)}`);

    mapMarkers.rider = L.marker([riderLat, riderLon], { icon: riderIcon }).addTo(map)
        .bindPopup(`<strong>Rider: ${riderCallSign}</strong><br>GPS: ${riderLat.toFixed(4)}, ${riderLon.toFixed(4)}`);

    mapMarkers.customer = L.marker([dropLat, dropLon], { icon: customerIcon }).addTo(map)
        .bindPopup(`<strong>Customer Drop-off</strong><br>GPS: ${dropLat.toFixed(4)}, ${dropLon.toFixed(4)}`);

    // Draw Routes
    // Route 1: Rider -> Restaurant (Dashed Line)
    const riderToRestRoute = L.polyline([
        [riderLat, riderLon],
        [restLat, restLon]
    ], {
        color: '#ef4444',
        weight: 3,
        dashArray: '5, 8',
        opacity: 0.8
    }).addTo(map);
    mapRoutes.push(riderToRestRoute);

    // Route 2: Restaurant -> Customer (Solid teal line)
    const restToCustRoute = L.polyline([
        [restLat, restLon],
        [dropLat, dropLon]
    ], {
        color: '#06b6d4',
        weight: 4,
        opacity: 0.95
    }).addTo(map);
    mapRoutes.push(restToCustRoute);

    // Adjust Map view bounds to fit all markers nicely
    const bounds = L.latLngBounds([
        [restLat, restLon],
        [riderLat, riderLon],
        [dropLat, dropLon]
    ]);
    map.fitBounds(bounds.pad(0.15));
}

// ==========================================================================
// CHART.JS ANALYTICS SERVICE
// ==========================================================================
function initCharts() {
    const ctxSpeed = document.getElementById("chart-vehicle-speed").getContext("2d");
    const ctxTrend = document.getElementById("chart-session-trend").getContext("2d");
    const ctxShare = document.getElementById("chart-fleet-share").getContext("2d");

    // Chart 1: Bar Chart (Vehicle Speeds)
    speedChart = new Chart(ctxSpeed, {
        type: 'bar',
        data: {
            labels: ["Bicycle", "E-Bike", "Scooter", "Car"],
            datasets: [{
                label: 'Speed (km/h)',
                data: [15, 30, 35, 40],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.45)', // Emerald
                    'rgba(6, 182, 212, 0.45)',  // Teal
                    'rgba(99, 102, 241, 0.45)', // Indigo
                    'rgba(251, 191, 36, 0.45)'  // Gold
                ],
                borderColor: [
                    '#10b981', '#06b6d4', '#6366f1', '#fbbf24'
                ],
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Chart 2: Line Chart (Session Trend)
    trendChart = new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Predicted ETA (min)',
                data: [],
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#06b6d4'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Chart 3: Doughnut Chart (Fleet Vehicle Share)
    shareChart = new Chart(ctxShare, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    'rgba(99, 102, 241, 0.45)', // Indigo
                    'rgba(6, 182, 212, 0.45)',  // Teal
                    'rgba(16, 185, 129, 0.45)', // Emerald
                    'rgba(251, 191, 36, 0.45)'  // Gold
                ],
                borderColor: 'rgba(255, 255, 255, 0.08)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9ca3af', font: { size: 10 } }
                }
            }
        }
    });
}

// Fetch stats and update KPIs + Fleet Share chart
async function loadAnalyticsDashboard() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (res.ok) {
            const stats = await res.json();
            
            // Render KPI values
            kpiRestaurants.textContent = stats.total_restaurants.toLocaleString();
            kpiRiders.textContent = stats.total_riders.toLocaleString();
            kpiAvgRating.textContent = stats.avg_restaurant_rating.toFixed(2);
            kpiCompletedOrders.textContent = Math.round(stats.avg_rider_completed_orders).toLocaleString();

            // Render fleet shares chart
            const labels = Object.keys(stats.vehicle_counts).map(k => k.toUpperCase());
            const data = Object.values(stats.vehicle_counts);

            shareChart.data.labels = labels;
            shareChart.data.datasets[0].data = data;
            shareChart.update();
        }
    } catch (e) {
        console.error("Error loading stats:", e);
    }
}

// ==========================================================================
// EVENT HANDLERS & SIMULATOR LOGIC
// ==========================================================================
function setupEventListeners() {
    // Navigation Tabs Toggle
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const targetPanelId = btn.getAttribute("data-target");
            tabPanels.forEach(p => p.classList.remove("active"));
            document.getElementById(targetPanelId).classList.add("active");

            // Perform specific load triggers
            if (targetPanelId === "panel-analytics") {
                loadAnalyticsDashboard();
            }
            // Trigger Map recalculation when panel becomes visible
            if (targetPanelId === "panel-simulator" && map) {
                setTimeout(() => map.invalidateSize(), 150);
            }
        });
    });

    // Sliders
    sliderOrderSize.addEventListener("input", e => {
        valOrderSize.textContent = `${e.target.value} items`;
    });
    
    sliderOrderValue.addEventListener("input", e => {
        valOrderValue.textContent = `₹${e.target.value}`;
    });

    // Restaurant selector change
    selectRestaurantEl.addEventListener("change", () => {
        const restId = parseInt(selectRestaurantEl.value);
        const rest = restaurants.find(r => r.id === restId);
        if (rest) {
            restRatingEl.textContent = rest.avg_rating.toFixed(1);
            restCapEl.textContent = rest.prep_capacity;
            restInfoEl.classList.remove("hidden");

            // Auto-mock coords near restaurant if coordinates are empty
            if (!dropLatEl.value || !dropLonEl.value) {
                mockCoordsNear(rest.lat, rest.lon);
            }
        }
    });

    // Rider selector change
    selectRiderEl.addEventListener("change", () => {
        const riderId = parseInt(selectRiderEl.value);
        const rider = riders.find(r => r.id === riderId);
        if (rider) {
            riderLoadEl.textContent = rider.current_load;
            riderCompletedEl.textContent = rider.completed_orders;
            riderInfoEl.classList.remove("hidden");
        }
    });

    // Randomize Coords button
    btnMockCoords.addEventListener("click", () => {
        const restId = parseInt(selectRestaurantEl.value);
        if (restId) {
            const rest = restaurants.find(r => r.id === restId);
            mockCoordsNear(rest.lat, rest.lon);
            showToast("Drop-off coordinates updated near restaurant.", "success");
        } else {
            mockCoordsNear(12.9715987, 77.5945627);
            showToast("Coordinates randomized to city center.", "info");
        }
    });

    // Vehicle Cards toggle
    const vehicleCards = document.querySelectorAll(".vehicle-card");
    vehicleCards.forEach(card => {
        card.addEventListener("click", () => {
            vehicleCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
        });
    });

    // Settings Modal
    btnSettings.addEventListener("click", () => settingsModal.classList.remove("hidden"));
    settingsClose.addEventListener("click", () => settingsModal.classList.add("hidden"));
    settingsModal.addEventListener("click", e => {
        if (e.target === settingsModal) settingsModal.classList.add("hidden");
    });

    btnSaveSettings.addEventListener("click", () => {
        localStorage.setItem("gemini_api_key", geminiKeyInput.value.trim());
        settingsModal.classList.add("hidden");
        showToast("Gemini API Key saved!", "success");
        appendMessage("System", "Gemini API Key successfully updated! Conversational chatbot context synced.");
    });

    // Predict Form Submit
    simulatorForm.addEventListener("submit", handlePredict);

    // Chat Drawer Actions
    chatSend.addEventListener("click", handleChatSend);
    chatInput.addEventListener("keypress", e => {
        if (e.key === "Enter") handleChatSend();
    });

    suggestBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            let query = btn.getAttribute("data-q");
            if (query === "Why was this ETA predicted?" && currentPredictionContext) {
                query = `Why was this ETA of ${currentPredictionContext.predicted_eta} minutes predicted?`;
            }
            chatInput.value = query;
            handleChatSend();
        });
    });

    // Export CSV trigger
    btnExportCsv.addEventListener("click", handleExportCsv);

    // Run Batch Simulation trigger
    btnRunBatch.addEventListener("click", handleRunBatchSim);
}

function mockCoordsNear(lat, lon) {
    // Offset limit ~3.5km
    const latOffset = (Math.random() - 0.5) * 0.045;
    const lonOffset = (Math.random() - 0.5) * 0.045;
    
    dropLatEl.value = (lat + latOffset).toFixed(6);
    dropLonEl.value = (lon + lonOffset).toFixed(6);
}

// Predict call handler
async function handlePredict(e) {
    e.preventDefault();

    const restId = parseInt(selectRestaurantEl.value);
    const riderId = parseInt(selectRiderEl.value);
    const dropLat = parseFloat(dropLatEl.value);
    const dropLon = parseFloat(dropLonEl.value);
    const orderSize = parseInt(sliderOrderSize.value);
    const orderValue = parseFloat(sliderOrderValue.value);
    const promoCode = document.getElementById("select-promo").value;
    
    const customVehicleCard = document.querySelector('.vehicle-card.active input');
    const customVehicle = customVehicleCard ? customVehicleCard.value : "";

    if (!restId || !riderId || isNaN(dropLat) || isNaN(dropLon)) {
        showToast("Select restaurant, rider, and coords.", "error");
        return;
    }

    // Loader status
    btnSubmit.disabled = true;
    btnText.classList.add("hidden");
    btnSpinner.classList.remove("hidden");

    try {
        const payload = {
            restaurant_id: restId,
            rider_id: riderId,
            drop_lat: dropLat,
            drop_lon: dropLon,
            order_size: orderSize,
            vehicle_type: customVehicle || null,
            order_value: orderValue,
            promo_code_used: promoCode
        };

        const res = await fetch(`${API_BASE}/api/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            currentPredictionContext = data;

            displayResults(data);
            addPredictionToHistory(data, payload);
            
            // Map updates
            const rest = restaurants.find(r => r.id === restId);
            const rider = riders.find(r => r.id === riderId);
            updateMap(rest.lat, rest.lon, rider.lat, rider.lon, dropLat, dropLon, data.restaurant_name, data.rider_call_sign);
            
            showToast("Prediction run successfully with XGBoost model!", "success");
        } else {
            const err = await res.json();
            showToast(`Prediction error: ${err.detail || "API Failure"}`, "error");
        }
    } catch (e) {
        showToast(`Connection failed: ${e.message}`, "error");
    } finally {
        btnSubmit.disabled = false;
        btnText.classList.remove("hidden");
        btnSpinner.classList.add("hidden");
    }
}

function displayResults(data) {
    resultsPlaceholder.classList.add("hidden");
    resultsPlaceholder.classList.remove("active");
    resultsPanel.classList.remove("hidden");

    // ETA Cards
    etaNumber.textContent = data.predicted_eta.toFixed(1);
    etaBounds.textContent = `${data.confidence_lower.toFixed(1)} - ${data.confidence_upper.toFixed(1)}`;
    etaSummary.textContent = data.summary;

    // Badges
    metricDist.textContent = `${data.distance_km.toFixed(2)} km`;
    metricTravel.textContent = `${data.estimated_travel_time.toFixed(1)} mins`;
    
    const restEfficiencyVal = data.features_engineered.restaurant_efficiency;
    metricEfficiency.textContent = typeof restEfficiencyVal === 'number' ? restEfficiencyVal.toFixed(1) : restEfficiencyVal;
    metricRider.textContent = data.rider_call_sign;

    // Animate Key Factors Bars
    const distPercentage = Math.min(100, Math.round((data.distance_km / 12) * 100));
    barDist.style.width = `${distPercentage}%`;
    valBarDist.textContent = `${data.distance_km.toFixed(2)} km`;

    const prepCap = data.features_engineered.prep_capacity;
    const prepPercentage = Math.min(100, Math.round((prepCap / 25) * 100));
    barPrep.style.width = `${prepPercentage}%`;
    valBarPrep.textContent = `${prepCap} ord/hr`;

    // Traffic decode
    const trafficClasses = ["High", "Low", "Medium", "Very High"];
    const trafficVal = data.features_engineered.traffic;
    const trafficName = trafficClasses[trafficVal] || "Low";
    
    let trafficPercentage = 25;
    if (trafficName === "High") trafficPercentage = 75;
    else if (trafficName === "Very High") trafficPercentage = 95;
    else if (trafficName === "Medium") trafficPercentage = 50;

    barTraffic.style.width = `${trafficPercentage}%`;
    valBarTraffic.textContent = trafficName;

    const loadVal = data.features_engineered.current_load;
    const loadPercentage = Math.min(100, Math.round((loadVal / 4) * 100));
    barLoad.style.width = `${loadPercentage}%`;
    valBarLoad.textContent = `${loadVal} active`;

    appendMessage("System", `Prediction updated. Chat assistant synced with prediction context of **${data.predicted_eta.toFixed(1)} minutes**.`);
}

// Add prediction details to history cache & render in tab table
function addPredictionToHistory(data, payload) {
    const entry = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        restaurant_id: payload.restaurant_id,
        restaurant_name: data.restaurant_name,
        rider_id: payload.rider_id,
        rider_call_sign: data.rider_call_sign,
        distance_km: data.distance_km,
        vehicle_type: payload.vehicle_type || "default",
        predicted_eta: data.predicted_eta,
        confidence_lower: data.confidence_lower,
        confidence_upper: data.confidence_upper,
        drop_lat: payload.drop_lat,
        drop_lon: payload.drop_lon,
        order_size: payload.order_size,
        order_value: payload.order_value,
        promo_code_used: payload.promo_code_used
    };

    predictionHistory.unshift(entry);
    renderHistoryTable();

    // Update Line Chart Trend values
    trendCount++;
    trendChart.data.labels.push(`P-${trendCount}`);
    trendChart.data.datasets[0].data.push(data.predicted_eta);
    if (trendChart.data.labels.length > 10) {
        trendChart.data.labels.shift();
        trendChart.data.datasets[0].data.shift();
    }
    trendChart.update();
}

function renderHistoryTable() {
    if (predictionHistory.length === 0) {
        historyTbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="8">No predictions run in this session yet. Run a prediction in the Simulator tab.</td>
            </tr>
        `;
        return;
    }

    historyTbody.innerHTML = "";
    predictionHistory.forEach(entry => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${entry.timestamp}</td>
            <td><strong>${entry.restaurant_name}</strong></td>
            <td>${entry.rider_call_sign}</td>
            <td>${entry.distance_km.toFixed(2)} km</td>
            <td><code style="text-transform: uppercase;">${entry.vehicle_type}</code></td>
            <td style="color: var(--color-teal); font-weight: 600;">${entry.predicted_eta.toFixed(1)} mins</td>
            <td>${entry.confidence_lower.toFixed(1)} - ${entry.confidence_upper.toFixed(1)}</td>
            <td>
                <button class="btn-table-action" onclick="reloadHistoryPrediction(${entry.id})"><i class="fa-solid fa-rotate-left"></i> Reload</button>
            </td>
        `;
        historyTbody.appendChild(tr);
    });
}

// Reload a past prediction context into simulation form
window.reloadHistoryPrediction = function(id) {
    const entry = predictionHistory.find(e => e.id === id);
    if (!entry) return;

    selectRestaurantEl.value = entry.restaurant_id;
    // trigger change to render rating badges
    selectRestaurantEl.dispatchEvent(new Event("change"));

    selectRiderEl.value = entry.rider_id;
    selectRiderEl.dispatchEvent(new Event("change"));

    dropLatEl.value = entry.drop_lat;
    dropLonEl.value = entry.drop_lon;

    sliderOrderSize.value = entry.order_size;
    valOrderSize.textContent = `${entry.order_size} items`;

    sliderOrderValue.value = entry.order_value;
    valOrderValue.textContent = `₹${entry.order_value}`;

    document.getElementById("select-promo").value = entry.promo_code_used;

    // Toggle active vehicle cards
    const cards = document.querySelectorAll(".vehicle-card");
    cards.forEach(card => {
        const input = card.querySelector("input");
        if (input.value === (entry.vehicle_type === "default" ? "" : entry.vehicle_type)) {
            card.click();
        }
    });

    // Switch to simulator tab
    const tabSim = document.querySelector('[data-target="panel-simulator"]');
    if (tabSim) tabSim.click();

    // Trigger predict submit automatically
    simulatorForm.dispatchEvent(new Event("submit"));
    
    showToast("Re-loaded past simulation configuration!", "success");
};

// Export prediction history to CSV
function handleExportCsv() {
    if (predictionHistory.length === 0) {
        showToast("No history predictions to export.", "error");
        return;
    }

    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Timestamp,Restaurant,Rider,Distance (km),Vehicle,Predicted ETA (mins),Lower Bound,Upper Bound\n";

    predictionHistory.forEach(e => {
        csvContent += `"${e.timestamp}","${e.restaurant_name}","${e.rider_call_sign}",${e.distance_km.toFixed(3)},"${e.vehicle_type}",${e.predicted_eta.toFixed(2)},${e.confidence_lower.toFixed(2)},${e.confidence_upper.toFixed(2)}\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `eulerq_prediction_history_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast("CSV exported successfully!", "success");
}

// ==========================================================================
// LEADERBOARDS CALCULATOR
// ==========================================================================
function renderLeaderboards() {
    // 1. Restaurant Leaderboards (score = prep_capacity * avg_rating)
    if (restaurants.length > 0) {
        const scoredRestaurants = restaurants.map(r => ({
            ...r,
            score: r.prep_capacity * r.avg_rating
        })).sort((a, b) => b.score - a.score).slice(0, 10);

        leaderboardRestaurantsTbody.innerHTML = "";
        scoredRestaurants.forEach((rest, idx) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="rank-badge">${idx + 1}</span></td>
                <td><strong>${rest.name}</strong></td>
                <td>${rest.cuisine}</td>
                <td>${rest.avg_rating.toFixed(1)} <i class="fa-solid fa-star text-gold"></i></td>
                <td>${rest.prep_capacity}</td>
                <td style="color: var(--color-teal); font-weight:600;">${rest.score.toFixed(1)}</td>
            `;
            leaderboardRestaurantsTbody.appendChild(tr);
        });
    }

    // 2. Rider Leaderboards
    if (riders.length > 0) {
        const sortedRiders = [...riders].sort((a, b) => b.completed_orders - a.completed_orders).slice(0, 10);
        leaderboardRidersTbody.innerHTML = "";
        sortedRiders.forEach((rider, idx) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="rank-badge">${idx + 1}</span></td>
                <td><strong>${rider.rider_call_sign}</strong></td>
                <td style="text-transform: uppercase;">${rider.vehicle_type}</td>
                <td style="color: var(--color-emerald); font-weight:600;">${rider.completed_orders.toLocaleString()}</td>
                <td>${rider.shift_hours} hrs</td>
                <td>${rider.current_load} load</td>
            `;
            leaderboardRidersTbody.appendChild(tr);
        });
    }
}

// ==========================================================================
// BATCH SIMULATION RUNNER
// ==========================================================================
async function handleRunBatchSim() {
    if (restaurants.length === 0 || riders.length === 0) {
        showToast("Dataset catalogs not initialized.", "error");
        return;
    }

    btnRunBatch.disabled = true;
    btnRunBatch.querySelector(".btn-text").classList.add("hidden");
    btnRunBatch.querySelector(".btn-spinner").classList.remove("hidden");

    batchTbody.innerHTML = "";
    
    // Select 5 random configs
    const vehicles = ["scooter", "bike", "car", "bicycle"];
    const batchRequests = [];

    for (let i = 0; i < 5; i++) {
        const randRest = restaurants[Math.floor(Math.random() * restaurants.length)];
        const randRider = riders[Math.floor(Math.random() * riders.length)];
        const randVehicle = vehicles[Math.floor(Math.random() * vehicles.length)];

        // Random coords near the restaurant
        const latOffset = (Math.random() - 0.5) * 0.045;
        const lonOffset = (Math.random() - 0.5) * 0.045;
        const dropLat = randRest.lat + latOffset;
        const dropLon = randRest.lon + lonOffset;

        // Render placeholder row
        const tr = document.createElement("tr");
        tr.id = `batch-row-${i}`;
        tr.innerHTML = `
            <td>Sim #${i + 1}</td>
            <td><strong>${randRest.name}</strong></td>
            <td>${randRider.rider_call_sign}</td>
            <td><code style="text-transform: uppercase;">${randVehicle}</code></td>
            <td colspan="4" class="loading-text"><i class="fa-solid fa-circle-notch fa-spin"></i> Executing predict...</td>
            <td><span class="badge-status loading">RUNNING</span></td>
        `;
        batchTbody.appendChild(tr);

        // Formulate request promise
        const payload = {
            restaurant_id: randRest.id,
            rider_id: randRider.id,
            drop_lat: dropLat,
            drop_lon: dropLon,
            order_size: Math.floor(Math.random() * 8) + 1,
            vehicle_type: randVehicle,
            order_value: parseFloat((Math.random() * 1200 + 100).toFixed(0)),
            promo_code_used: "BLR10"
        };

        const reqPromise = fetch(`${API_BASE}/api/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(res => {
            if (res.ok) return res.json();
            throw new Error("Predict request failed");
        }).then(data => {
            // Update row on success
            const row = document.getElementById(`batch-row-${i}`);
            if (row) {
                row.innerHTML = `
                    <td>Sim #${i + 1}</td>
                    <td><strong>${data.restaurant_name}</strong></td>
                    <td>${data.rider_call_sign}</td>
                    <td><code style="text-transform: uppercase;">${randVehicle}</code></td>
                    <td>${data.distance_km.toFixed(2)} km</td>
                    <td>${data.estimated_travel_time.toFixed(1)} mins</td>
                    <td style="color: var(--color-teal); font-weight:600;">${data.predicted_eta.toFixed(1)} mins</td>
                    <td>${data.confidence_lower.toFixed(1)} - ${data.confidence_upper.toFixed(1)}</td>
                    <td><span class="badge-status success">SUCCESS</span></td>
                `;
            }
            return data;
        }).catch(err => {
            const row = document.getElementById(`batch-row-${i}`);
            if (row) {
                row.innerHTML = `
                    <td>Sim #${i + 1}</td>
                    <td><strong>${randRest.name}</strong></td>
                    <td>${randRider.rider_call_sign}</td>
                    <td><code style="text-transform: uppercase;">${randVehicle}</code></td>
                    <td colspan="4" style="color: var(--color-crimson);">Failed to fetch prediction details</td>
                    <td><span class="badge-status" style="background:rgba(239,68,68,0.15); color:var(--color-crimson);">FAILED</span></td>
                `;
            }
            return null;
        });

        batchRequests.push(reqPromise);
    }

    try {
        await Promise.all(batchRequests);
        showToast("Batch simulation completed!", "success");
    } catch(e) {
        showToast("One or more batch simulations failed.", "error");
    } finally {
        btnRunBatch.disabled = false;
        btnRunBatch.querySelector(".btn-text").classList.remove("hidden");
        btnRunBatch.querySelector(".btn-spinner").classList.add("hidden");
    }
}

// ==========================================================================
// CHAT BOT ASSISTANT SERVICES
// ==========================================================================
async function handleChatSend() {
    const question = chatInput.value.trim();
    if (!question) return;

    chatInput.value = "";
    appendMessage("User", question);

    const thinkingId = appendThinkingBubble();

    try {
        const key = localStorage.getItem("gemini_api_key") || "";
        const payload = {
            question: question,
            prediction_context: currentPredictionContext,
            api_key: key
        };

        const res = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        removeBubble(thinkingId);

        if (res.ok) {
            const data = await res.json();
            appendMessage("Assistant", data.answer);
        } else {
            const err = await res.json();
            appendMessage("SystemError", `AI Assistant Error: ${err.detail || "Unable to contact API"}`);
        }
    } catch (e) {
        removeBubble(thinkingId);
        appendMessage("SystemError", `Connection failed: ${e.message}`);
    }
}

function appendMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender.toLowerCase()}`;
    
    const formattedText = parseMarkdown(text);
    msgDiv.innerHTML = `<div class="msg-bubble">${formattedText}</div>`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendThinkingBubble() {
    const id = "thinking-" + Date.now();
    const msgDiv = document.createElement("div");
    msgDiv.className = "message assistant";
    msgDiv.id = id;
    msgDiv.innerHTML = `<div class="msg-bubble"><i class="fa-solid fa-spinner fa-pulse"></i> Assistant is analyzing...</div>`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeBubble(id) {
    const bubble = document.getElementById(id);
    if (bubble) bubble.remove();
}

function parseMarkdown(text) {
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
        
    html = html.replace(/<br>-\s(.*?)/g, '<br>&bull; $1');
    return html;
}
