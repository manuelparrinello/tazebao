export function inizialiNome() {
  if (this.cliente.nome.length) {
    return this.nomeCliente.charAt(0).toUpperCase();
  } else {
    return "-";
  }
}

export function submitFormNewCliente(e) {
  e.preventDefault();
  // Creazione di un oggetto FormData per inviare i dati del modulo
  const form = document.querySelector("#nuovoCliente");
  const formData = new FormData(form);
  formData.append("nomeCliente", this.nomeCliente);
  formData.append("telefono", this.telefono);
  formData.append("email", this.email);
  formData.append("colore", this.colore);
  formData.append("note", this.note);

  // Invio della richiesta POST al server
  fetch("/clienti/new", {
    method: "POST",
    body: formData,
  }).then((response) => {
    if (response.ok) {
      // Reindirizzamento alla pagina dei clienti dopo il successo
      window.alert("Cliente creato con successo!");
      window.location.href = "/clienti";
    } else {
      console.error("Errore durante la creazione del cliente.");
    }
  });

  
}
