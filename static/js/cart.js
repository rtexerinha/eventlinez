function _updateTotal() {
  if (document.body && document.body.dataset.cartPage) return;
  var promoApplied = document.querySelector('.applied-promo-code');
  if (promoApplied) return;

  var total = 0.0;
  $('.ticket-row').each(function () {
    var qty = parseInt($(this).find('.ticket-qty').text().trim(), 10);
    var amount = 0;
    var amountElement = $(this).find('.ticket-amount');

    if (amountElement.length > 0) {
      var dataPrice = amountElement.attr('data-price');
      amount =
        dataPrice !== undefined
          ? parseFloat(dataPrice) || 0
          : parseFloat(amountElement.text().replace(/[^0-9.]/g, '')) || 0;
    } else {
      var priceEl = $(this).find('.ticket-price');
      var dp = priceEl.attr('data-price');
      amount =
        dp !== undefined
          ? parseFloat(dp) || 0
          : parseFloat(priceEl.text().replace(/[^0-9.]/g, '')) || 0;
    }

    if (!isNaN(qty) && !isNaN(amount) && qty > 0) {
      total += amount * qty;
    }
  });

  var amountField = document.getElementById('total');
  if (!amountField) return;

  if (total >= 0) {
    amountField.textContent = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(total);
  }
}

function controlQty(ticket_id, command) {
  var quantity = document.getElementById('ticket-' + ticket_id + '-qty');
  if (!quantity) return;
  var value = parseInt(quantity.innerText, 10);
  if (command === 'decrease' && value <= 0) return;
  quantity.innerText = (command === 'increase' ? ++value : --value).toString();
  _updateTotal();
}

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function getCSRFToken() {
  var metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) return metaTag.getAttribute('content');
  var hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (hiddenInput) return hiddenInput.value;
  return getCookie('csrftoken');
}

function showCartError(msg) {
  var el = document.getElementById('cart-error-msg');
  if (!el) {
    alert(msg);
    return;
  }
  el.textContent = msg;
  el.style.display = 'block';
  clearTimeout(el._hideTimer);
  el._hideTimer = setTimeout(function () {
    el.style.display = 'none';
  }, 6000);
}

function addToCard() {
  var addButton = document.getElementById('addToCartBtn');
  var originalValue = addButton ? addButton.value : '';
  if (addButton) {
    addButton.value = 'Adding...';
    addButton.disabled = true;
  }

  var errorEl = document.getElementById('cart-error-msg');
  if (errorEl) errorEl.style.display = 'none';

  var linhas = document.getElementsByClassName('ticket-row');
  var tickets = [];
  var hasValidTickets = false;

  for (var i = 0; i < linhas.length; i++) {
    var ticketIdEl = linhas[i].getElementsByClassName('ticket-id')[0];
    if (!ticketIdEl) continue; // sold-out rows have no ticket-id element
    var ticket_id = parseInt(ticketIdEl.innerText, 10);
    var qtyEl = linhas[i].getElementsByClassName('ticket-qty')[0];
    if (!qtyEl) continue;
    var qty = parseInt(qtyEl.innerText, 10);
    tickets.push({ id: ticket_id, quantity: qty });
    if (qty > 0) hasValidTickets = true;
  }

  if (!hasValidTickets) {
    showCartError('Please select at least one ticket before adding to cart.');
    if (addButton) {
      addButton.value = originalValue;
      addButton.disabled = false;
    }
    return;
  }

  var vendor_code = null;
  if (document.getElementById('vendor_code')) {
    vendor_code = document.getElementsByClassName('vendor_code')[0].innerHTML;
  }

  fetch('/cart/add/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
    body: JSON.stringify({ promo_code: null, vendor_code: vendor_code, tickets: tickets }),
  })
    .then(function (response) {
      if (response.status === 429) {
        return response.json().then(function (data) {
          var minutes = Math.ceil(
            ((data.reset_time || Date.now() / 1000 + 300) - Date.now() / 1000) / 60
          );
          showCartError(
            'Too many requests. Please wait ' + minutes + ' minute(s) before trying again.'
          );
          throw new Error('Rate limited');
        });
      }
      if (!response.ok)
        return response.json().then(function (err) {
          return Promise.reject(err);
        });
      return response.json();
    })
    .then(function () {
      window.location.href = '/cart/';
    })
    .catch(function (error) {
      if (error.message !== 'Rate limited')
        showCartError(
          error.error || error.message || 'Failed to add items to cart. Please try again.'
        );
    })
    .finally(function () {
      if (addButton) {
        addButton.value = originalValue;
        addButton.disabled = false;
      }
    });
}

function doCheckout() {
  var checkoutBtn = document.getElementById('checkout-btn');
  var originalText = checkoutBtn ? checkoutBtn.innerHTML : '';
  if (checkoutBtn) {
    checkoutBtn.innerHTML = 'Processing...';
    checkoutBtn.disabled = true;
  }

  fetch('/cart/checkout/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
  })
    .then(function (result) {
      if (result.status === 429) {
        return result.json().then(function (data) {
          var minutes = Math.ceil(
            ((data.reset_time || Date.now() / 1000 + 300) - Date.now() / 1000) / 60
          );
          alert(
            'Too many checkout attempts. Please wait ' + minutes + ' minute(s) before trying again.'
          );
          throw new Error('Rate limited');
        });
      }
      if (!result.ok)
        return result.json().then(function (err) {
          return Promise.reject(err);
        });
      return result.json();
    })
    .then(function (data) {
      // Duplicate purchase detected server-side — go to the existing confirmation
      // instead of opening a second Stripe session.
      if (data && data.redirect_url) {
        window.location.href = data.redirect_url;
        return;
      }
      if (!data.stripe_public_key || !data.session_id)
        throw new Error('Invalid checkout session data');
      if (typeof Stripe === 'undefined')
        throw new Error('Payment library failed to load. Please refresh and try again.');
      return Stripe(data.stripe_public_key).redirectToCheckout({ sessionId: data.session_id });
    })
    .then(function (result) {
      if (result && result.error) alert('Checkout error: ' + result.error.message);
    })
    .catch(function (error) {
      if (error.message !== 'Rate limited')
        alert(error.error || error.message || 'Checkout failed. Please try again.');
    })
    .finally(function () {
      if (checkoutBtn) {
        checkoutBtn.innerHTML = originalText;
        checkoutBtn.disabled = false;
      }
    });
}
