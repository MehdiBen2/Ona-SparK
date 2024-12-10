// Initialize map variables
let incidentMap = null;
let incidentMarker = null;

// Function to show location on map
function showLocationMap(wilaya, commune, localite) {
    // Show the map modal
    const mapModal = new bootstrap.Modal(document.getElementById('mapModal'));
    mapModal.show();

    // Initialize map if not already initialized
    if (!incidentMap) {
        incidentMap = L.map('incident-map').setView([36.7538, 3.0588], 13); // Default to Algeria's center
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(incidentMap);
    }

    // Combine location details for geocoding
    const locationQuery = `${wilaya}, ${commune}, ${localite}, Algeria`;

    // Clear existing marker
    if (incidentMarker) {
        incidentMap.removeLayer(incidentMarker);
    }

    // Use Nominatim for geocoding
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationQuery)}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                
                // Update map view and add marker
                incidentMap.setView([lat, lon], 13);
                incidentMarker = L.marker([lat, lon]).addTo(incidentMap);
                
                // Add popup with location info
                incidentMarker.bindPopup(`
                    <strong>${wilaya}</strong><br>
                    ${commune}<br>
                    ${localite}
                `).openPopup();
            } else {
                console.error('Location not found');
                // Show a default view of Algeria
                incidentMap.setView([36.7538, 3.0588], 6);
            }
        })
        .catch(error => {
            console.error('Error fetching location:', error);
            // Show a default view of Algeria
            incidentMap.setView([36.7538, 3.0588], 6);
        });

    // Invalidate map size when modal is shown
    mapModal.shown.subscribe(() => {
        setTimeout(() => {
            incidentMap.invalidateSize();
        }, 10);
    });
}
