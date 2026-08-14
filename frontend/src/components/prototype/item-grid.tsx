import type { ReactNode } from "react";

type ItemGridProps = {
  children: ReactNode;
  emptyMessage?: string;
};

export function ItemGrid({ children, emptyMessage }: ItemGridProps) {
  if (!children && emptyMessage) {
    return <p className="prototype-empty" role="status">{emptyMessage}</p>;
  }
  return <div className="prototype-grid">{children}</div>;
}
