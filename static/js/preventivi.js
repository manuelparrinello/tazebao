function formatPreventivoDate(value) {
  const formatter = window.erpDateFormatter?.formatDate;
  if (formatter) return formatter(value);
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  const parts = new Intl.DateTimeFormat("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).formatToParts(parsed);
  return parts
    .map((part) => (part.type === "month" ? part.value.charAt(0).toUpperCase() + part.value.slice(1) : part.value))
    .join("");
}

function formatPreventivoEuro(value) {
  if (value == null || isNaN(value)) return "&euro; 0,00";
  const num = Number(value);
  return "&euro; " + num.toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const preventivi = Vue.createApp({
  data() {
    return {
      preventivi: [],
    };
  },
  methods: {
    async fetchAllPreventivi() {
      const url = `/api/preventivi/getall`;
      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("Errore HTTP:" + response.status);
        }
        const data = await response.json();
        this.preventivi = data;
      } catch (err) {
        console.log(err);
      }
    },
    openPreventivo(id) {
      if (!id) return;
      window.location.href = `/preventivi/visualizza/${id}`;
    },
    formatDate(value) {
      return formatPreventivoDate(value);
    },
    formatEuro(value) {
      return formatPreventivoEuro(value);
    },
    statoBadgeHtml(stato) {
      if (!stato) return '<span class="erp-badge badge text-bg-secondary">-</span>';
      const map = {
        bozza: "secondary",
        inviato: "primary",
        accettato: "success",
        rifiutato: "danger",
      };
      const cls = map[stato] || "secondary";
      return `<span class="erp-badge badge text-bg-${cls}">${stato}</span>`;
    },
  },
  delimiters: ["[[", "]]"],
  mounted() {
    this.fetchAllPreventivi();
  },
}).mount("#preventivi");
