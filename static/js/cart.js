function _updateTotal() {
  let total = 0.0;
  console.log('Updating total...');
  $(".ticket-row").each(function (index) {
    let qty = parseInt($(this).find(".ticket-qty").text());

    // Try to find ticket-amount first (for cart page), then ticket-price (for event page)
    let amountElement = $(this).find(".ticket-amount");
    let amount = 0;

    if (amountElement.length > 0) {
      // Cart page: use ticket-amount (includes fee)
      amount = parseFloat(amountElement.text().replace('$', ''));
    } else {
      // Event page: use ticket-price (unit price only)
      amount = parseFloat($(this).find(".ticket-price").text().replace('$', ''));
    }

    console.log(`Item ${index}: qty=${qty}, amount=${amount}`);
    total = total + amount * qty;
  });

  console.log('Calculated total:', total);

  let amountField = document.getElementById("total");
  if (!amountField) {
    console.error('Total field not found');
    return;
  }

  let fmt = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: "2",
    maximumFractionDigits: "2",
  });

  amountField.textContent = fmt.format(total);
  console.log('Total updated to:', fmt.format(total));
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
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify(payload),
  })
    .then(response => {
      console.log('Response status:', response.status);
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
      alert(error.message || 'Failed to add items to cart. Please try again.');
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
      'X-CSRFToken': getCookie('csrftoken'),
    },
  })
    .then(result => {
      console.log('Checkout response status:', result.status);
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
      alert(error.message || 'Checkout failed. Please try again.');
    })
    .finally(() => {
      // Reset button state
      if (checkoutBtn) {
        checkoutBtn.innerHTML = originalText;
        checkoutBtn.disabled = false;
      }
    });
}
