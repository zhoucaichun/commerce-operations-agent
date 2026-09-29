import { ProductRecommendation } from "./types";

type ParsedProduct = {
  sku?: string;
  name: string;
  price?: string;
  role?: string;
};

const SECTION_HEADINGS = [
  "Best pick",
  "Best picks",
  "Why it fits",
  "Why they fit",
  "Note",
  "Notes",
  "Also consider",
  "For charging multiple devices"
];

function normalizeAnswer(answer: string) {
  return answer
    .replace(/\r\n/g, "\n")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/^\s*#{1,6}\s+/gm, "")
    .trim();
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function extractSection(answer: string, headings: string[]) {
  const headingPattern = headings.map(escapeRegExp).join("|");
  const stopPattern = SECTION_HEADINGS.map(escapeRegExp).join("|");
  const pattern = new RegExp(
    `(?:^|\\n)\\s*(?:${headingPattern})\\s*:\\s*([\\s\\S]*?)(?=\\n\\s*(?:${stopPattern})\\s*:|$)`,
    "i"
  );

  return answer.match(pattern)?.[1]?.trim() || "";
}

function cleanLines(text: string) {
  return text
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.replace(/^\s*[-*•]\s*/, "").trim())
    .filter(Boolean);
}

function inferRole(name: string) {
  const lower = name.toLowerCase();
  if (lower.includes("cable")) return "Cable";
  if (lower.includes("charger") || lower.includes("adapter")) return "Charger";
  if (lower.includes("power bank")) return "Power bank";
  return "Accessory";
}

function parseProductLine(line: string): ParsedProduct | null {
  const cleaned = line.replace(/^\s*[-*•]\s*/, "").trim();
  if (!cleaned) return null;

  const pipeParts = cleaned.split("|").map((part) => part.trim()).filter(Boolean);
  if (/^SKU[\w-]+$/i.test(pipeParts[0] || "")) {
    const sku = pipeParts[0];
    const pricePart = pipeParts.find((part) => /\$[\d.]+/.test(part));
    const nameParts = pipeParts.slice(1).filter((part) => !/\$[\d.]+/.test(part));
    const name = nameParts.join(" | ").trim();

    if (name) {
      return {
        sku,
        name,
        price: pricePart?.match(/\$[\d.]+/)?.[0],
        role: inferRole(name)
      };
    }
  }

  const parenthesizedPrice = cleaned.match(
    /^(?:(SKU[\w-]+)\s*\|\s*)?(.+?)\s*\((\$[\d.]+)\)\s*$/i
  );
  if (parenthesizedPrice) {
    const name = parenthesizedPrice[2].trim();
    return {
      sku: parenthesizedPrice[1]?.trim(),
      name,
      price: parenthesizedPrice[3].trim(),
      role: inferRole(name)
    };
  }

  return null;
}

function splitFeatureLines(text: string) {
  const normalized = text.replace(/\r\n/g, "\n").trim();
  if (!normalized) return [];

  const bulletLines = cleanLines(normalized);
  if (bulletLines.length > 1) {
    return bulletLines;
  }

  return normalized
    .split(/(?<=[.!?。！？])\s+/)
    .map((item) => item.replace(/^\s*[-*•]\s*/, "").trim())
    .filter(Boolean);
}

function sumPrices(products: ParsedProduct[]) {
  const total = products.reduce((sum, product) => {
    const value = product.price?.match(/[\d.]+/)?.[0];
    return value ? sum + Number(value) : sum;
  }, 0);

  return total > 0 ? `$${total.toFixed(2)}` : products[0]?.price || "$0.00";
}

function isComplementaryBundle(products: ParsedProduct[]) {
  const roles = new Set(products.map((product) => product.role).filter(Boolean));
  return roles.size > 1 && roles.has("Charger");
}

function hasBundleIntent(answer: string) {
  return /\b(bundle|setup|set|kit|combo|charger\s*\+\s*cable|complete)\b/i.test(answer);
}

function inferBundleName(answer: string, productCount: number) {
  if (/iphone\s*15/i.test(answer)) {
    return productCount > 1 ? "iPhone 15 Charging Bundle" : "iPhone 15 Charging Pick";
  }

  return productCount > 1 ? "Ready-to-use Charging Bundle" : "Best Charging Pick";
}

function buildFriendlySummary(products: ParsedProduct[]) {
  const hasCable = products.some((product) => product.role === "Cable");
  const hasCharger = products.some((product) => product.role === "Charger");

  if (hasCable && hasCharger) {
    return "Charger and cable are both covered, so you can use it straight away without guessing what else to buy.";
  }

  if (hasCharger) {
    return "A practical charger pick for daily fast charging, with the key compatibility points checked first.";
  }

  return "A practical accessory pick based on your device and charging scenario.";
}

export function parseRecommendationAnswer(
  answer: string
): ProductRecommendation | null {
  const normalized = normalizeAnswer(answer);

  if (!/Best picks?:/i.test(normalized) || !/Why (it|they) fits?:/i.test(normalized)) {
    return null;
  }

  const bestSection = extractSection(normalized, ["Best pick", "Best picks"]);
  const whySection = extractSection(normalized, ["Why it fits", "Why they fit"]);
  const notesSection = extractSection(normalized, ["Note", "Notes"]);

  const products = cleanLines(bestSection)
    .map(parseProductLine)
    .filter((product): product is ParsedProduct => Boolean(product));

  if (!products.length) return null;

  const primary = products[0];
  const whyItems = splitFeatureLines(whySection).slice(0, 4);
  const noteText = notesSection.trim() || "No extra setup note was provided.";
  const isBundle =
    products.length > 1 && hasBundleIntent(normalized) && isComplementaryBundle(products);

  return {
    badge: isBundle ? "Complete set" : "Best match",
    sku: primary.sku,
    name: isBundle ? inferBundleName(normalized, products.length) : primary.name,
    price: isBundle ? sumPrices(products) : primary.price || "$0.00",
    summary: buildFriendlySummary(products),
    bundleItems: isBundle ? products : undefined,
    rating: undefined,
    reviews: undefined,
    features: whyItems.length
      ? whyItems
      : ["Matched to your device, connector type, and daily charging need."],
    whyFit: whySection || "This recommendation fits your device and request.",
    note: noteText
  };
}
