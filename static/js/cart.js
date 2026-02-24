function _updateTotal() {
  // On the cart page the total is server-rendered and authoritative — skip JS recalculation.
  // The cart page sets data-cart-page on the body to signal this.
  if (document.body && document.body.dataset.cartPage) {
    console.log('Cart page detected — skipping _updateTotal(), using server-rendered total.');
    return;
  }

  // Check if we have a promo code applied - if so, don't override the server-calculated total
  const promoApplied = document.querySelector('.applied-promo-code');
  if (promoApplied) {
    console.log('Promo code applied - keeping server-calculated total');
    return;
  }

  let total = 0.0;
  console.log('Updating total...');
  $(".ticket-row").each(function (index) {
    let qty = parseInt($(this).find(".ticket-qty").text().trim(), 10);

    let amount = 0;
    let amountElement = $(this).find(".ticket-amount");

    if (amountElement.length > 0) {
      // Prefer data-price attribute (set by server, no parsing needed)
      let dataPrice = amountElement.attr('data-price');
      if (dataPrice !== undefined) {
        amount = parseFloat(dataPrice) || 0;
      } else {
        // Fallback: strip currency symbols and parse text
        let amountText = amountElement.text().replace(/[^0-9.]/g, '');
        amount = parseFloat(amountText) || 0;
      }
    } else {
      // Event page: use ticket-price (unit price × qty)
      let priceEl = $(this).find(".ticket-price");
      let dataPrice = priceEl.attr('data-price');
      if (dataPrice !== undefined) {
        amount = parseFloat(dataPrice) || 0;
      } else {
        let priceText = priceEl.text().replace(/[^0-9.]/g, '');
        amount = parseFloat(priceText) || 0;
      }
    }

    console.log(`Item ${index}: qty=${qty}, amount=${amount}`);
    if (!isNaN(qty) && !isNaN(amount) && qty > 0) {
      total = total + (amount * qty);
    }
  });

  console.log('Calculated total:', total);

  let amountField = document.getElementById("total");
  if (!amountField) {
    console.error('Total field not found');
    return;
  }

  if (total >= 0) {
    let fmt = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    amountField.textContent = fmt.format(total);
    console.log('Total updated to:', fmt.format(total));
  }
}

function controlQty(ticket_id, command) {
  console.log(`controlQty called: ticket_id=${ticket_id}, command=${command}`);
  let quantity = document.getElementById("ticket-" + ticket_id + "-qty");
  if (!quantity) {
    console.error(`Quantity element not found: ticket-${ticket_id}-qty`);
    return;
  }

  let value = parseInt(quantity.innerText, 10);
  console.log(`Current quantity: ${value}`);

  if (command === "decrease" && value <= 0) return;
  if (command === "increase") value = ++value;
  if (command === "decrease") value = --value;

  console.log(`New quantity: ${value}`);
  quantity.innerText = value.toString();

  _updateTotal();
}

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

function getCSRFToken() {
  // Try multiple methods to get CSRF token
  let token = null;

  // Method 1: Try to get from meta tag
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    token = metaTag.getAttribute('content');
  }

  // Method 2: Try to get from hidden input
  if (!token) {
    const hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (hiddenInput) {
      token = hiddenInput.value;
    }
  }

  // Method 3: Try to get from cookie
  if (!token) {
    token = getCookie('csrftoken');
  }

  return token;
}

function addToCard() {
  console.log('Adding items to cart...');

  // Show loading state if there's an add to cart button
  const addButton = document.querySelector('.add-to-cart-btn, [onclick*="addToCard"]');
  let originalText = '';
  if (addButton) {
    originalText = addButton.innerHTML;
    addButton.innerHTML = 'Adding...';
    addButton.disabled = true;
  }

  let linhas = document.getElementsByClassName("ticket-row");
  let tickets = [];
  let hasValidTickets = false;

  for (let i = 0; i < linhas.length; i++) {
    let ticket_id = parseInt(
      linhas[i].getElementsByClassName("ticket-id")[0].innerText,
      10
    );
    let qty = parseInt(
      linhas[i].getElementsByClassName("ticket-qty")[0].innerText,
      10
    );

    tickets.push({ id: ticket_id, quantity: qty });

    if (qty > 0) {
      hasValidTickets = true;
    }
  }

  if (!hasValidTickets) {
    alert('Please select at least one ticket before adding to cart.');
    if (addButton) {
      addButton.innerHTML = originalText;
      addButton.disabled = false;
    }
    return;
  }

  var vendor_code = null;
  if (document.getElementById("vendor_code")) {
    vendor_code = document.getElementsByClassName("vendor_code")[0].innerHTML;
  }

  let payload = {
    promo_code: null,
    vendor_code: vendor_code,
    tickets: tickets,
  };

  console.log('Sending payload:', payload);

  fetch("/cart/add/", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken(),
    },
    body: JSON.stringify(payload),
  })
    .then(response => {
      console.log('Response status:', response.status);

      // Handle rate limiting
      if (response.status === 429) {
        return response.json().then(data => {
          const resetTime = data.reset_time || Date.now() / 1000 + 300; // Default 5 min
          const waitTime = Math.ceil(resetTime - Date.now() / 1000);
          const minutes = Math.ceil(waitTime / 60);

          alert(`Too many requests. Please wait ${minutes} minute(s) before trying again.`);
          throw new Error('Rate limited');
        });
      }

      if (!response.ok) {
        return response.json().then(err => Promise.reject(err));
      }
      return response.json();
    })
    .then(data => {
      console.log('Success:', data);
      // Redirect to cart page
      window.location.href = "/cart/";
    })
    .catch(error => {
      console.error('Cart add error:', error);
      if (error.message !== 'Rate limited') {
        alert(error.message || 'Failed to add items to cart. Please try again.');
      }
    })
    .finally(() => {
      // Reset button state
      if (addButton) {
        addButton.innerHTML = originalText;
        addButton.disabled = false;
      }
    });
}

function doCheckout() {
  console.log('Starting checkout...');

  // Show loading state
  const checkoutBtn = document.getElementById('checkout-btn');
  const originalText = checkoutBtn ? checkoutBtn.innerHTML : 'Checkout';
  if (checkoutBtn) {
    checkoutBtn.innerHTML = 'Processing...';
    checkoutBtn.disabled = true;
  }

  fetch("/cart/checkout/", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken(),
    },
  })
    .then(result => {
      console.log('Checkout response status:', result.status);

      // Handle rate limiting
      if (result.status === 429) {
        return result.json().then(data => {
          const resetTime = data.reset_time || Date.now() / 1000 + 300;
          const waitTime = Math.ceil(resetTime - Date.now() / 1000);
          const minutes = Math.ceil(waitTime / 60);

          alert(`Too many checkout attempts. Please wait ${minutes} minute(s) before trying again.`);
          throw new Error('Rate limited');
        });
      }

      if (!result.ok) {
        return result.json().then(err => Promise.reject(err));
      }
      return result.json();
    })
    .then(data => {
      console.log('Checkout data:', data);
      if (!data.stripe_public_key || !data.session_id) {
        throw new Error('Invalid checkout session data');
      }

      const stripe = Stripe(data.stripe_public_key);
      return stripe.redirectToCheckout({
        sessionId: data.session_id,
      });
    })
    .then(function (result) {
      if (result.error) {
        console.error('Stripe error:', result.error);
        alert('Checkout error: ' + result.error.message);
      }
    })
    .catch(function (error) {
      console.error("Checkout Error:", error);
      if (error.message !== 'Rate limited') {
        alert(error.message || 'Checkout failed. Please try again.');
      }
    })
    .finally(() => {
      // Reset button state
      if (checkoutBtn) {
        checkoutBtn.innerHTML = originalText;
        checkoutBtn.disabled = false;
      }
    });
}
