/*--------------------*/
/*  CANCELLA CLIENTE  */
/*--------------------*/
function deleteCliente(id) {
  return fetch(`/clienti/${id}`, {
    method: "delete",
    headers: {
      Accept: "application/json",
    },
  });
}

async function clickForDeleteCliente(event, idCliente) {
  event.preventDefault();
  const utenteConferma = confirm("Sei sicuro di voler cancellare il cliente?");

  if (utenteConferma === false) {
    return;
  }

  try {
    const response = await deleteCliente(idCliente);
    console.log("DELETE status:", response.status);
    if (response.ok === false) {
      const corpoRispostaComeTesto = await response.text();
      console.error("Errore response:", corpoRispostaComeTesto);
      throw new Error(
        `Errore durante l'eliminazione (HTTP ${response.status})`
      );
    }
    alert("Cliente eliminato con successo!");
    window.location.href = "/clienti";
  } catch (errore) {
    alert(errore.message);
    console.error(errore);
  }
}

/*-------------------*/
/*  CANCELLA LAVORO  */
/*-------------------*/

function deleteLavoro(id) {
  return fetch(`/lavori/${id}`, {
    method: "delete",
    headers: {
      Accept: "application/json",
    },
  });
}

async function clickForDeleteLavoro(event, idLavoro) {
  event.preventDefault();
  const conferma = confirm("Vuoi cancellare questo lavoro?");
  if (!conferma) return;

  try {
    const response = await deleteLavoro(idLavoro);
    if (!response) {
      const corpoRispostaTesto = await response.text();
      console.error("Errore response:", corpoRispostaTesto);
      throw new Error(
        `Errore durante l'eliminazione (HTTP ${response.status})`
      );
    }
    window.alert("Lavoro eliminato con successo!");
    window.location.href = "/lavori";
  } catch (errore) {
    alert(errore.message);
    console.error(errore);
  }
}