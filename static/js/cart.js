
function _updateTotal(){
    let total = 0.0
    $(".ticket-row").each(function(index){
        let qty = parseInt($(this).find(".ticket-qty").text())
        let price = parseFloat($(this).find(".ticket-price").text())
        total = total + price * qty
    })

    let amountField = document.getElementById("total")

    let fmt = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: '2',
        maximumFractionDigits: '2'
    });

    amountField.textContent = fmt.format(total);
}

function controlQty(ticket_id, command){
    let quantity = document.getElementById("ticket-" + ticket_id + "-qty");
    let value = parseInt(quantity.innerText, 10);
    if (command === "decrease" && value <= 0)
        return
    if (command === "increase")
        value = ++value;
    if (command === "decrease")
        value = --value;
    quantity.innerText = value.toString();

    _updateTotal();
}


function doFunction() {
    let linhas = document.getElementsByClassName("ticket-row");
    let tickets = []
    for (let i = 0; i < linhas.length; i++) {
        let ticket_id = parseInt(linhas[i].getElementsByClassName("ticket-id")[0].innerText, 10)
        let qty = parseInt(linhas[i].getElementsByClassName("ticket-qty")[0].innerText, 10)
        tickets.push({"id": ticket_id, "quantity": qty})
    }

    let payload = {
        "promoCode": null,
        "tickets": tickets
    }

    fetch('/cart/add/', {
        method: 'post',
        redirect: 'follow',
        body: JSON.stringify(payload)
    }).then(response => {
        window.location.replace("/cart/");
    });
}


