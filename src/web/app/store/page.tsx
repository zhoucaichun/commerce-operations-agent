"use client";

import Link from "next/link";
import { useState } from "react";
import { StoreWidget } from "../../components/store/StoreWidget";

const products = [
  { sku: "SKU005", name: "Dual Port GaN Charger 65W", category: "Chargers", price: "$49.90", accent: "violet", tags: ["Laptop + phone", "2 USB-C ports"] },
  { sku: "SKU013", name: "Power Bank 20000mAh 65W", category: "Power Banks", price: "$69.90", accent: "orange", tags: ["Travel ready", "Laptop power"] },
  { sku: "SKU020", name: "USB-C Hub 6-in-1", category: "Hubs & Docks", price: "$45.90", accent: "blue", tags: ["4K HDMI", "100W pass-through"] },
  { sku: "SKU001", name: "MagCharge Wireless Charger 15W", category: "Wireless", price: "$29.90", accent: "green", tags: ["MagSafe", "Desk essential"] }
];

export default function StoreMockPage() {
  const [widgetOpen, setWidgetOpen] = useState(false);
  return <main className="storefront">
    <div className="store-demo-ribbon">DEMO STOREFRONT · ShopPilot Commerce Agent integration preview</div>
    <header className="store-nav"><Link className="store-brand" href="/store"><span>SP</span><strong>ShopPilot 3C</strong></Link><nav aria-label="Store navigation"><a href="#chargers">Chargers</a><a href="#power">Power Banks</a><a href="#hubs">Hubs &amp; Docks</a><a href="#new">New arrivals</a></nav><div className="store-nav-actions"><button className="store-support" onClick={() => setWidgetOpen(true)}>✦ AI Assistant</button><button className="store-link-button" onClick={() => setWidgetOpen(true)}>Support</button><span aria-label="Shopping bag">Bag (0)</span></div></header>
    <section className="store-hero"><div className="store-hero-copy"><p>POWER, MADE SIMPLE</p><h1>Everyday power.<br />Less guesswork.</h1><span>Find a charger, cable or hub that fits the devices you already own.</span><div><a className="store-cta" href="#chargers">Shop charging</a><button className="store-plain-button" onClick={() => setWidgetOpen(true)}>Ask AI before you buy →</button></div></div><div className="hero-device" aria-label="Illustration of a 65W USB-C charger"><div className="hero-cable" /><div className="hero-charger"><i /><i /></div><div className="hero-orbit" /></div></section>
    <section className="store-trust"><span>→ Free shipping over $45</span><span>◌ 30-day return policy</span><span>✓ 18-month limited warranty</span><span>✦ AI product guidance</span></section>
    <section className="store-section" id="chargers"><div className="store-section-heading"><div><p>SHOP THE ESSENTIALS</p><h2>Built around your setup</h2></div><a href="#products">View all products →</a></div><div className="store-category-grid"><a href="#products"><b>01</b><span>Chargers</span><small>Fast, compact USB-C power</small></a><a href="#products"><b>02</b><span>Power Banks</span><small>Power for every journey</small></a><a href="#products"><b>03</b><span>Cables</span><small>Reliable connections</small></a><a href="#products"><b>04</b><span>Hubs &amp; Docks</span><small>More from one port</small></a></div></section>
    <section className="store-section store-products" id="products"><div className="store-section-heading"><div><p>POPULAR THIS WEEK</p><h2>Power picks, selected for you</h2></div><button className="store-filter">Filter &amp; sort</button></div><div className="store-product-grid">{products.map((product) => <article className="store-product" key={product.sku}><div className={`product-art ${product.accent}`}><span>ShopPilot<br />3C</span><div className="product-shape" /></div><p>{product.category}</p><h3>{product.name}</h3><ul>{product.tags.map((tag) => <li key={tag}>{tag}</li>)}</ul><div><strong>{product.price}</strong><button onClick={() => setWidgetOpen(true)}>Ask AI</button></div></article>)}</div></section>
    <section className="store-agent-callout"><div><p>NOT SURE WHAT FITS?</p><h2>Meet your shopping copilot.</h2><span>Ask about compatibility, find the right setup, check delivery policy, or get help with a simulated order.</span></div><button onClick={() => setWidgetOpen(true)}>Open ShopPilot AI Assistant</button></section>
    <footer className="store-footer"><strong>ShopPilot 3C</strong><span>Simulated Shopify-style storefront · synthetic catalog only</span><Link href="/console">Merchant Console →</Link></footer>
    {widgetOpen ? <StoreWidget onClose={() => setWidgetOpen(false)} /> : null}
    <button className="store-widget-trigger" aria-label="Open ShopPilot AI Assistant" onClick={() => setWidgetOpen(true)}><span>✦</span><em>Ask ShopPilot AI</em></button>
  </main>;
}
