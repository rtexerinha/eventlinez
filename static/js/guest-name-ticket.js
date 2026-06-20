function getCsrfToken() {
  var meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute('content');
  var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (input) return input.value;
  var match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

function showSaveFeedback(input, success) {
  var label = input.closest('.guest-name-section').querySelector('.save-status');
  if (!label) return;
  label.textContent = success ? 'Saved ✓' : 'Error saving';
  label.style.color = success ? '#28a745' : '#dc3545';
  label.style.opacity = '1';
  clearTimeout(label._hide);
  label._hide = setTimeout(function () { label.style.opacity = '0'; }, 2000);
}

function saveGuestName(input) {
  var id = input.dataset.id;
  var value = input.value;
  var formData = new FormData();
  formData.append('id', id);
  formData.append('type', 'guest_name');
  formData.append('value', value);

  fetch('/customer/ticket/save/', {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })
    .then(function (r) { return r.json(); })
    .then(function (data) { showSaveFeedback(input, data.success === true); })
    .catch(function () { showSaveFeedback(input, false); });
}

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.guest-name-input').forEach(function (input) {
    input.addEventListener('blur', function () { saveGuestName(this); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); saveGuestName(this); }
    });
  });
});
