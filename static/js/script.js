document.addEventListener('DOMContentLoaded', function() {
    // Symptom search functionality
    const symptomSearch = document.getElementById('symptomSearch');
    const symptomTags = document.querySelectorAll('.symptom-tag');
    
    if (symptomSearch) {
        symptomSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            symptomTags.forEach(tag => {
                const label = tag.querySelector('label').textContent.toLowerCase();
                if (label.includes(searchTerm)) {
                    tag.style.display = 'flex';
                } else {
                    tag.style.display = 'none';
                }
            });
        });
    }
    
    // Disease search functionality
    const diseaseSearchBtn = document.getElementById('diseaseSearchBtn');
    const diseaseSearchInput = document.getElementById('diseaseSearch');
    const diseaseResults = document.getElementById('diseaseResults');
    
    if (diseaseSearchBtn && diseaseSearchInput) {
        diseaseSearchBtn.addEventListener('click', searchDiseases);
        diseaseSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchDiseases();
            }
        });
    }
    
    function searchDiseases() {
        const query = diseaseSearchInput.value.trim();
        if (query === '') return;
        
        fetch(`/search_disease?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displayDiseaseResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                diseaseResults.innerHTML = '<p>Error loading disease information. Please try again.</p>';
            });
    }
    
    function displayDiseaseResults(results) {
        if (!results || results.length === 0) {
            diseaseResults.innerHTML = '<p>No diseases found matching your search.</p>';
            return;
        }
        
        let html = '';
        results.forEach(disease => {
            html += `
                <div class="disease-item">
                    <h3>${disease.name}</h3>
                    <p>${disease.description}</p>
                    <h4>Prevention:</h4>
                    <ul>
                        ${disease.prevention.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        });
        
        diseaseResults.innerHTML = html;
    }
    
    // Animation for symptom tags
    if (symptomTags.length > 0) {
        symptomTags.forEach((tag, index) => {
            tag.style.animationDelay = `${index * 0.05}s`;
        });
    }
    
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navMenu = document.querySelector('nav ul');
    
    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
});