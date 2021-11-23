function exportTicket() {
  const e = document.getElementById("eventsChoice");
  const eventId = e.options[e.selectedIndex].value;
  if (eventId === "") {
    let url = "excel/";
    window.open(url, "_blank");
  } else {
    let url = `excel/${eventId}`;
    window.open(url, "_blank");
  }
}

function exportVendors() {
  const e = document.getElementById("eventsChoice");
  const eventId = e.options[e.selectedIndex].value;
  console.log(e);
  if (eventId === "") {
    let url = "excel/";
    window.open(url, "_blank");
  } else {
    let url = `excel/${eventId}`;
    window.open(url, "_blank");
  }
}
