"use client";

import { ProductRecommendation } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

type RecommendationCardProps = {
  product: ProductRecommendation;
  onViewProduct?: () => void;
  onAskFollowup?: () => void;
};

function getBundleIcon(role?: string) {
  if (role === "Cable") return "USB";
  if (role === "Charger") return "PD";
  if (role === "Power bank") return "PB";
  return "3C";
}

export function RecommendationCard({
  product,
  onViewProduct,
  onAskFollowup
}: RecommendationCardProps) {
  const bundleItems = product.bundleItems?.length ? product.bundleItems : null;
  const isBundle = Boolean(bundleItems && bundleItems.length > 1);

  if (isBundle && bundleItems) {
    return (
      <Card className="reco-card reco-bundle-card">
        <div className="bundle-hero">
          <div>
            <Badge tone="success">{product.badge}</Badge>
            <h3>{product.name}</h3>
            <p>{product.summary}</p>
          </div>
          <div className="bundle-total">
            <span>Estimated total</span>
            <strong>{product.price}</strong>
          </div>
        </div>

        <div className="bundle-items">
          {bundleItems.map((item, index) => (
            <div key={`${item.sku || item.name}-${index}`} className="bundle-item">
              <div className="bundle-item-icon">{getBundleIcon(item.role)}</div>
              <div className="bundle-item-copy">
                <span>{item.role || "Accessory"}</span>
                <strong>{item.name}</strong>
                {item.sku ? <em>{item.sku}</em> : null}
              </div>
              {item.price ? <div className="bundle-item-price">{item.price}</div> : null}
            </div>
          ))}
        </div>

        <div className="bundle-info-grid">
          <div className="life-box">
            <div className="box-label success">Why this is easy to use</div>
            <ul>
              {product.features.slice(0, 3).map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
          </div>

          <div className="life-box note-soft">
            <div className="box-label warning">Small thing to check</div>
            <p>{product.note}</p>
          </div>
        </div>

        <div className="reco-actions">
          <Button onClick={onAskFollowup}>Ask a follow-up</Button>
          <Button variant="secondary" onClick={onViewProduct}>
            Compare another option
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="reco-card reco-card-featured">
      <div className="reco-image">
        <div className="reco-image-placeholder" />
        <div className="reco-badge-wrap">
          <Badge tone="success">{product.badge}</Badge>
        </div>
        {product.sku ? <div className="reco-sku">{product.sku}</div> : null}
      </div>

      <div className="reco-content">
        <h3>{product.name}</h3>

        <div className="price-row">
          <div className="price">{product.price}</div>
          {product.rating && product.reviews ? (
            <div className="rating">
              <span className="rating-star">*</span> {product.rating} · {product.reviews}
            </div>
          ) : null}
        </div>

        <div className="features-title">What makes it practical:</div>
        <div className="features-grid">
          {product.features.map((feature) => (
            <div key={feature} className="feature-check">
              <span className="feature-check-mark">OK</span>
              <span>{feature}</span>
            </div>
          ))}
        </div>

        <div className="insight-box">
          <div className="box-label success">Why this fits you</div>
          <div className="box-text">{product.whyFit}</div>
        </div>

        <div className="note-box">
          <div className="box-label warning">Before you buy</div>
          <div className="box-text">{product.note}</div>
        </div>

        <div className="reco-actions">
          <Button onClick={onViewProduct}>Ask a follow-up</Button>
          <Button variant="secondary" onClick={onAskFollowup}>
            Compare another option
          </Button>
        </div>
      </div>
    </Card>
  );
}
