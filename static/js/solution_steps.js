document.addEventListener('DOMContentLoaded', function() {
    console.log("Document ready - initializing enhanced add steps functionality");
    
    // Set initial form count and update progress bar
    var initialFormCount = document.getElementById('id_form-TOTAL_FORMS').value;
    console.log("Initial form count:", initialFormCount);
    updateProgressBar();
    
    // Function to update progress bar
    function updateProgressBar() {
        var filledSteps = 0;
        var totalSteps = document.querySelectorAll('.step-form').length;
        
        document.querySelectorAll('.step-form').forEach(function(stepForm) {
            var title = stepForm.querySelector('input[name$="title"]').value;
            var content = stepForm.querySelector('textarea[name$="content"]').value;
            
            if (title && content) {
                filledSteps++;
            }
        });
        
        var progress = totalSteps > 0 ? (filledSteps / totalSteps) * 100 : 0;
        document.getElementById('progress-bar').style.width = progress + '%';
    }
    
    // Toggle debug panel
    document.getElementById('toggle-debug').addEventListener('click', function() {
        document.getElementById('debug-panel').classList.toggle('d-none');
    });
    
    // Add step button functionality
    document.getElementById('add-step').addEventListener('click', function(e) {
        e.preventDefault();
        console.log("Add step button clicked");
        
        // Get the current form count
        var formCount = parseInt(document.getElementById('id_form-TOTAL_FORMS').value);
        console.log("Current form count:", formCount);
        
        // Clone the first form as a template
        var firstForm = document.querySelector('.step-form');
        var newForm = firstForm.cloneNode(true);
        console.log("Form cloned");
        
        // Update form index in all input names and IDs
        newForm.querySelectorAll('input, textarea, select').forEach(function(input) {
            var name = input.getAttribute('name');
            if (name) {
                name = name.replace(/form-\d+-/g, 'form-' + formCount + '-');
                input.setAttribute('name', name);
            }
            
            var id = input.getAttribute('id');
            if (id) {
                id = id.replace(/id_form-\d+-/g, 'id_form-' + formCount + '-');
                input.setAttribute('id', id);
            }
            
            // Clear values
            if (input.type === 'text' || input.tagName === 'TEXTAREA') {
                input.value = '';
            } else if (input.type === 'checkbox') {
                input.checked = false;
            }
        });
        
        // Update step number in the badge and title
        newForm.querySelector('.step-badge').textContent = formCount + 1;
        newForm.querySelector('.step-header h4').textContent = 'Step ' + (formCount + 1);
        
        // Set the order field to the next number
        newForm.querySelector('input[name$="order"]').value = formCount + 1;
        
        // Clear image previews
        newForm.querySelector('.image-previews').innerHTML = '';
        
        // Reset file inputs
        var fileInputs = newForm.querySelectorAll('input[type="file"]');
        fileInputs.forEach(function(input, index) {
            if (index > 0) {
                input.parentNode.removeChild(input);
            } else {
                input.value = '';
                input.classList.remove('step-image-input-used');
                input.classList.add('step-image-input');
            }
        });
        
        // Make sure the delete checkbox is visible and unchecked
        newForm.querySelector('.form-check').style.display = 'block';
        newForm.querySelector('input[type="checkbox"]').checked = false;
        
        // Append the new form to the container
        document.getElementById('steps-container').appendChild(newForm);
        console.log("New form appended");
        
        // Update the total form count
        document.getElementById('id_form-TOTAL_FORMS').value = formCount + 1;
        console.log("Form count updated to:", formCount + 1);
        
        // Update management form data in debug panel
        document.getElementById('management-form-data').innerHTML = `TOTAL_FORMS: ${formCount + 1}
INITIAL_FORMS: ${document.getElementById('id_form-INITIAL_FORMS').value}
MIN_NUM_FORMS: ${document.getElementById('id_form-MIN_NUM_FORMS').value}
MAX_NUM_FORMS: ${document.getElementById('id_form-MAX_NUM_FORMS').value}`;
        
        // Update progress bar
        updateProgressBar();
        
        // Scroll to the new form with animation
        window.scrollTo({
            top: newForm.offsetTop - 100,
            behavior: 'smooth'
        });
        
        // Add a subtle highlight effect to the new form
        newForm.querySelector('.step-card').style.backgroundColor = 'rgba(13, 110, 253, 0.05)';
        setTimeout(function() {
            newForm.querySelector('.step-card').style.backgroundColor = '';
        }, 1000);
    });
    
    // Form validation before submit
    document.getElementById('solution-steps-form').addEventListener('submit', function(e) {
        // Enable all disabled inputs before submit
        document.querySelectorAll('.step-form input, .step-form textarea').forEach(function(input) {
            input.disabled = false;
        });
        
        var valid = true;
        var firstInvalid = null;
        
        document.querySelectorAll('.step-form').forEach(function(stepForm) {
            var isDeleted = stepForm.querySelector('input[type="checkbox"]').checked;
            if (!isDeleted) {
                var title = stepForm.querySelector('input[name$="title"]').value;
                var content = stepForm.querySelector('textarea[name$="content"]').value;
                var order = stepForm.querySelector('input[name$="order"]').value;
                
                if (!title || !content || !order) {
                    valid = false;
                    if (!firstInvalid) {
                        firstInvalid = stepForm;
                    }
                    
                    if (!title) {
                        stepForm.querySelector('input[name$="title"]').classList.add('is-invalid');
                    }
                    if (!content) {
                        stepForm.querySelector('textarea[name$="content"]').classList.add('is-invalid');
                    }
                    if (!order) {
                        stepForm.querySelector('input[name$="order"]').classList.add('is-invalid');
                    }
                }
            }
        });
        
        if (!valid) {
            e.preventDefault();
            
            // Show error message
            if (!document.getElementById('form-error-alert')) {
                var alertDiv = document.createElement('div');
                alertDiv.id = 'form-error-alert';
                alertDiv.className = 'alert alert-danger alert-dismissible fade show';
                alertDiv.role = 'alert';
                alertDiv.innerHTML = `
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Please fill in all required fields for each step.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                document.getElementById('solution-steps-form').prepend(alertDiv);
            }
            
            // Scroll to first invalid input
            if (firstInvalid) {
                window.scrollTo({
                    top: firstInvalid.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        }
    });
    
    // Set up event delegation for dynamically added elements
    document.addEventListener('click', function(e) {
        // Handle browse button click
        if (e.target.closest('.browse-btn')) {
            e.target.closest('.image-upload-area').querySelector('.step-image-input').click();
        }
        
        // Remove image functionality
        if (e.target.closest('.remove-image-btn')) {
            e.target.closest('.image-preview-container').remove();
        }
        
        // Add more images functionality
        if (e.target.closest('.add-more-images')) {
            e.preventDefault();
            e.target.closest('.image-upload-container').querySelector('.browse-btn').click();
        }
    });
    
    // Handle file input changes
    document.addEventListener('change', function(e) {
        // Image preview functionality
        if (e.target.classList.contains('step-image-input')) {
            var file = e.target.files[0];
            if (file) {
                var reader = new FileReader();
                var container = e.target.closest('.image-upload-container');
                var previewsContainer = container.querySelector('.image-previews');
                var stepIndex = Array.from(document.querySelectorAll('.step-form')).indexOf(e.target.closest('.step-form'));
                var imageCount = previewsContainer.children.length + 1;
                
                reader.onload = function(event) {
                    var previewContainer = document.createElement('div');
                    previewContainer.className = 'col-md-6 image-preview-container';
                    previewContainer.innerHTML = `
                        <div class="image-preview">
                            <img src="${event.target.result}" class="img-fluid" alt="Preview">
                            <div class="remove-image-btn">
                                <i class="fas fa-times"></i>
                            </div>
                        </div>
                        <div class="form-floating mt-2">
                            <input type="text" name="step_image_caption_${stepIndex}_${imageCount}" class="form-control image-caption-input" placeholder="Image caption (optional)">
                            <label>Image Caption (Optional)</label>
                        </div>
                    `;
                    
                    previewsContainer.appendChild(previewContainer);
                    
                    // Rename the file input and create a new one for the next upload
                    e.target.setAttribute('name', `step_image_${stepIndex}_${imageCount}`);
                    e.target.classList.remove('step-image-input');
                    e.target.classList.add('step-image-input-used');
                    
                    // Add a new file input for the next image
                    var newInput = document.createElement('input');
                    newInput.type = 'file';
                    newInput.name = `step_image_${stepIndex}_${imageCount + 1}`;
                    newInput.className = 'form-control step-image-input d-none';
                    newInput.accept = 'image/*';
                    container.querySelector('.image-upload-area').appendChild(newInput);
                };
                
                reader.readAsDataURL(file);
            }
        }
        
        // Handle delete checkbox changes
        if (e.target.type === 'checkbox' && e.target.closest('.step-form')) {
            var stepForm = e.target.closest('.step-form');
            
            if (e.target.checked) {
                stepForm.querySelector('.step-card').classList.add('opacity-50');
                stepForm.querySelectorAll('input, textarea').forEach(function(input) {
                    if (input.type !== 'checkbox') {
                        input.disabled = true;
                    }
                });
            } else {
                stepForm.querySelector('.step-card').classList.remove('opacity-50');
                stepForm.querySelectorAll('input, textarea').forEach(function(input) {
                    if (input.type !== 'checkbox') {
                        input.disabled = false;
                    }
                });
            }
            
            updateProgressBar();
        }
    });
    
    // Handle input changes for validation
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('is-invalid')) {
            e.target.classList.remove('is-invalid');
        }
        
        if ((e.target.name && e.target.name.endsWith('title')) || 
            (e.target.name && e.target.name.endsWith('content'))) {
            updateProgressBar();
        }
    });
    
    // Handle drag and drop
    document.querySelectorAll('.image-upload-area').forEach(function(uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('border-primary');
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('border-primary');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('border-primary');
            
            if (e.dataTransfer && e.dataTransfer.files.length) {
                var fileInput = this.querySelector('.step-image-input');
                fileInput.files = e.dataTransfer.files;
                
                // Trigger change event manually
                var event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        });
    });
});