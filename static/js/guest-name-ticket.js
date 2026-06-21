function getCsrfToken() {
  var meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute('content');
  var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (input) return input.value;
  var match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

function showSaveFeedback(section, success) {
  var label = section.querySelector('.save-status');
  if (!label) return;
  label.textContent = success ? 'Saved ✓' : 'Error — please try again';
  label.style.color = success ? '#28a745' : '#dc3545';
  label.style.opacity = '1';
  clearTimeout(label._hide);
  label._hide = setTimeout(function () { label.style.opacity = '0'; }, 2500);
}

function saveGuestName(section) {
  var input = section.querySelector('.guest-name-input');
  var btn = section.querySelector('.save-guest-btn');
  if (!input) return;

  var id = input.dataset.id;
  var value = input.value.trim();

  if (btn) { btn.textContent = 'Saving…'; btn.disabled = true; }

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
    .then(function (data) { showSaveFeedback(section, data.success === true); })
    .catch(function () { showSaveFeedback(section, false); })
    .finally(function () {
      if (btn) { btn.textContent = 'Save'; btn.disabled = false; }
    });
}

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.guest-name-section').forEach(function (section) {
    var input = section.querySelector('.guest-name-input');
    var btn = section.querySelector('.save-guest-btn');

    if (btn) {
      btn.addEventListener('click', function () { saveGuestName(section); });
    }
    if (input) {
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); saveGuestName(section); }
      });
    }
  });
});
