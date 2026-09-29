export type ProductRecommendation = {
  badge: string;
  sku?: string;
  name: string;
  price: string;
  rating?: string;
  reviews?: string;
  summary?: string;
  bundleItems?: {
    sku?: string;
    name: string;
    price?: string;
    role?: string;
  }[];
  features: string[];
  whyFit: string;
  note: string;
};
