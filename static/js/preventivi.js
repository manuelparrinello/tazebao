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

const CLOSED_QUOTE_STATES = ["accettato", "accettata", "approvato", "approvata", "rifiutato", "rifiutata", "scaduto", "annullato", "annullata", "convertito"];

function getActiveFilter() {
  const el = document.getElementById("preventivi");
  return el ? (el.getAttribute("data-active-filter") || "") : "";
}

function matchFilter(preventivo, filter) {
  if (!filter) return true;
  const s = (preventivo.stato || "").toLowerCase();
  switch (filter) {
    case "aperti":
      return !CLOSED_QUOTE_STATES.includes(s) && s !== "pdf_esterno";
    case "accettati":
      return ["accettato", "accettata", "approvato", "approvata"].includes(s);
    case "rifiutati":
      return ["rifiutato", "rifiutata"].includes(s);
    case "scaduti":
      return s === "scaduto";
    case "followup":
      return !CLOSED_QUOTE_STATES.includes(s) && s !== "pdf_esterno" && s !== "bozza";
    default:
      return true;
  }
}

const preventivi = Vue.createApp({
  data() {
    return {
      preventivi: [],
      activeFilter: getActiveFilter(),
    };
  },
  computed: {
    filteredPreventivi() {
      if (!this.activeFilter) return this.preventivi;
      return this.preventivi.filter(function(p) { return matchFilter(p, this.activeFilter); }, this);
    },
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
        const payload = await response.json();
        this.preventivi = Array.isArray(payload) ? payload : (payload.data || []);
      } catch (err) {
        console.log(err);
      }
    },
    openPreventivo(preventivo) {
      if (!preventivo) return;
      if (preventivo.source === "pdf_esterno" && preventivo.pdf_url) {
        window.open(preventivo.pdf_url, "_blank");
      } else {
        window.location.href = `/preventivi/visualizza/${preventivo.id}`;
      }
    },
    formatDate(value) {
      return formatPreventivoDate(value);
    },
    formatEuro(value) {
      return formatPreventivoEuro(value);
    },
    statoBadgeHtml(stato) {
      if (!stato) return '<span class="erp-badge badge text-bg-secondary">-</span>';
      if (stato === "pdf_esterno") return '<span class="erp-badge badge text-bg-warning"><i class="bi bi-filetype-pdf me-1"></i>PDF esterno</span>';
      const map = {
        bozza: "warning",
        inviato: "primary",
        in_attesa: "info",
        accettato: "success",
        rifiutato: "danger",
        scaduto: "secondary",
      };
      const cls = map[stato] || "secondary";
      const label = stato.replace(/_/g, " ").replace(/\b\w/g, function(c) { return c.toUpperCase(); });
      return `<span class="erp-badge badge text-bg-${cls}">${label}</span>`;
    },
  },
  delimiters: ["[[", "]]"],
  mounted() {
    this.fetchAllPreventivi();
  },
}).mount("#preventivi");
