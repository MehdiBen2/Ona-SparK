document.addEventListener('DOMContentLoaded', function() {
    const toggleViewBtn = document.getElementById('toggleView');
    const cardView = document.getElementById('cardView');
    const listView = document.getElementById('listView');
    
    // Get the saved view preference
    let isListView = localStorage.getItem('incidentViewPreference') === 'list';

    function updateView() {
        if (isListView) {
            cardView.classList.add('d-none');
            listView.classList.remove('d-none');
            toggleViewBtn.innerHTML = '<i class="fas fa-th-large me-2"></i>Vue Cartes';
        } else {
            listView.classList.add('d-none');
            cardView.classList.remove('d-none');
            toggleViewBtn.innerHTML = '<i class="fas fa-list me-2"></i>Vue Liste';
        }
        // Save the preference
        localStorage.setItem('incidentViewPreference', isListView ? 'list' : 'card');
    }

    if (toggleViewBtn && cardView && listView) {
        // Set initial view
        updateView();

        toggleViewBtn.addEventListener('click', function() {
            isListView = !isListView;
            updateView();
        });
    }

    // Handle form submissions to maintain view
    document.querySelectorAll('form[action^="/delete_incident/"]').forEach(form => {
        form.addEventListener('submit', function() {
            // Store the current view preference before form submission
            localStorage.setItem('incidentViewPreference', isListView ? 'list' : 'card');
        });
    });
});
