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

function addToCard() {
  let linhas = document.getElementsByClassName("ticket-row");
  let tickets = [];
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

  fetch("/cart/add/", {
    method: "post",
    redirect: "follow",
    body: JSON.stringify(payload),
  }).then((response) => {
    window.location.replace("/cart/");
  });
}

function doCheckout() {
  fetch("/cart/checkout/", {
    method: "POST",
  })
    .then((result) => {
      return result.json();
    })
    .then((data) => {
      return Stripe(data.stripe_public_key).redirectToCheckout({
        sessionId: data.session_id,
      });
    })
    .then(function (result) { })
    .catch(function (error) {
      console.error("Error:", error);
    });
}
