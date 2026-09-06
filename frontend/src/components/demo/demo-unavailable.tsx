"use client";

import { X } from "lucide-react";
import { type ReactNode, useEffect, useId, useRef, useState } from "react";

type DemoUnavailableProps = {
  actionLabel: string;
  subject: string;
  className?: string;
  ariaLabel?: string;
  children?: ReactNode;
};

export function DemoUnavailable({ actionLabel, subject, className, ariaLabel, children }: DemoUnavailableProps) {
  const [isOpen, setIsOpen] = useState(false);
  const titleId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const hasOpened = useRef(false);

  useEffect(() => {
    if (!isOpen) {
      if (hasOpened.current) triggerRef.current?.focus();
      return;
    }

    hasOpened.current = true;
    closeRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isOpen]);

  return (
    <>
      <button ref={triggerRef} className={className} type="button" aria-label={ariaLabel} onClick={() => setIsOpen(true)}>{children ?? actionLabel}</button>
      {isOpen && (
        <div className="demo-dialog-backdrop" role="presentation">
          <section className="demo-dialog" role="dialog" aria-modal="true" aria-labelledby={titleId}>
            <header>
              <div><small>Demo功能说明</small><h2 id={titleId}>这项功能还在准备中</h2></div>
              <button ref={closeRef} type="button" aria-label="关闭" onClick={() => setIsOpen(false)}><X aria-hidden="true" /></button>
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
