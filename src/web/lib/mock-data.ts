import { ProductRecommendation } from "./types";

export const recommendationProducts: ProductRecommendation[] = [
  {
    badge: "Best Match",
    name: "Apple 20W USB-C Power Adapter",
    price: "$19.99",
    rating: "4.8",
    reviews: "12,453 reviews",
    features: [
      "Official Apple product",
      "20W fast charging",
      "Charges to 50% in 30 minutes",
      "Compact and portable design"
    ],
    whyFit:
      "Perfect for iPhone 15. As the official Apple adapter, it guarantees strong compatibility, fast charging, and a clean under-$25 fit.",
    note:
      "Cable sold separately. You will need a USB-C cable for the latest iPhone setup."
  },
  {
    badge: "Best Value",
    name: "Anker Nano II 30W GaN Charger",
    price: "$22.99",
    rating: "4.7",
    reviews: "8,942 reviews",
    features: [
      "30W power output",
      "GaN technology with smaller body",
      "Foldable plug for travel",
      "Multi-device compatibility"
    ],
    whyFit:
      "Best value inside your budget. It gives you higher wattage than 20W options and still keeps the charger compact and travel-friendly.",
    note:
      "May run slightly warmer than larger chargers because of the compact GaN design."
  },
  {
    badge: "Complete Bundle",
    name: "Belkin BoostCharge 25W with Cable",
    price: "$24.99",
    rating: "4.6",
    reviews: "6,721 reviews",
    features: [
      "25W fast charging",
      "Includes 1m USB-C cable",
      "MFi certified",
      "2-year warranty included"
    ],
    whyFit:
      "This is the easiest all-in-one pick if you want both the charger and cable in one purchase while staying under budget.",
    note:
      "Cable length is 1 meter. Register the product within 30 days to activate the warranty."
  }
];

export const followupQuestions = [
  "Which one charges fastest?",
  "Show me cheaper alternatives",
  "What about wireless chargers?",
  "Compare shipping times"
];
