"use client";

import Link from "next/link";
import { ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = {
  children: ReactNode;
  href?: string;
  variant?: ButtonVariant;
  fullWidth?: boolean;
  type?: "button" | "submit";
  onClick?: () => void;
  disabled?: boolean;
};

function variantClassName(variant: ButtonVariant) {
  if (variant === "secondary") return "button button-secondary";
  if (variant === "ghost") return "button button-ghost";
  return "button button-primary";
}

export function Button({
  children,
  href,
  variant = "primary",
  fullWidth = false,
  type = "button",
  onClick,
  disabled = false
}: ButtonProps) {
  const className = `${variantClassName(variant)}${
    fullWidth ? " button-full" : ""
  }`;

  if (href) {
    return (
      <Link href={href} className={className} prefetch={false}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} className={className} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
