// Debug script to test signup button functionality
// Run this in browser console on signup page

console.log('🔍 Debugging signup button...');

// Check if the form exists
const form = document.querySelector('form');
console.log('Form found:', !!form);

// Check if submit button exists
const submitBtn = document.querySelector('button[type="submit"]');
console.log('Submit button found:', !!submitBtn);

// Check form state
if (window.React && window.React.useState) {
    console.log('React component detected');
}

// Add click listener to debug
if (submitBtn) {
    submitBtn.addEventListener('click', (e) => {
        console.log('🔍 Submit button clicked!', e);
        console.log('Form data:', {
            citizenType: document.querySelector('select[name="citizenType"]')?.value,
            email: document.querySelector('input[type="email"]')?.value,
            password: document.querySelector('input[type="password"]')?.value ? '***' : ''
        });
    });
}

// Check for validation errors
const errorElements = document.querySelectorAll('.err-msg');
console.log('Validation errors found:', errorElements.length);
errorElements.forEach((el, i) => {
    console.log(`Error ${i}:`, el.textContent);
});

// Check network requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('🌐 Network request:', args[0], args[1]);
    return originalFetch.apply(this, args).then(response => {
        console.log('📥 Response:', response.status, response.statusText);
        return response.clone().json().then(data => {
            console.log('📄 Response data:', data);
            return response;
        }).catch(() => response);
    }).catch(error => {
        console.error('❌ Network error:', error);
        throw error;
    });
};

console.log('✅ Debug setup complete. Try clicking the signup button.');
