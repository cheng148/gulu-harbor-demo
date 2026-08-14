"use client";

import { X } from "lucide-react";
import { type ReactNode, useState } from "react";

type DemoUnavailableProps = {
  actionLabel: string;
  subject: string;
  className?: string;
  ariaLabel?: string;
  children?: ReactNode;
};

export function DemoUnavailable({ actionLabel, subject, className, ariaLabel, children }: DemoUnavailableProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button className={className} type="button" aria-label={ariaLabel} onClick={() => setIsOpen(true)}>{children ?? actionLabel}</button>
      {isOpen && (
        <div className="demo-dialog-backdrop" role="presentation">
          <section className="demo-dialog" role="dialog" aria-modal="true" aria-labelledby="demo-dialog-title">
            <header>
              <div><small>Demo功能说明</small><h2 id="demo-dialog-title">这项功能还在准备中</h2></div>
              <button type="button" aria-label="关闭" onClick={() => setIsOpen(false)}><X aria-hidden="true" /></button>
            </header>
            <strong>Demo演示功能，暂未开放。</strong>
            <p>{subject}不会产生任何真实记录或费用。</p>
            <button className="demo-dialog__confirm" type="button" onClick={() => setIsOpen(false)}>知道了</button>
          </section>
        </div>
      )}
    </>
  );
}
