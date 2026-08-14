"use client";

import { ShoppingBag, X } from "lucide-react";

import { DemoUnavailable } from "../demo/demo-unavailable";

type SupplyItem = {
  id: string;
  name: string;
  categoryLabel: string;
};

type CartDrawerProps = {
  isOpen: boolean;
  cart: Record<string, number>;
  items: SupplyItem[];
  onClose: () => void;
};

export function CartDrawer({ isOpen, cart, items, onClose }: CartDrawerProps) {
  if (!isOpen) return null;
  const cartItems = items.filter((item) => cart[item.id]);

  return (
    <div className="cart-drawer-backdrop" role="presentation">
      <section className="cart-drawer" role="dialog" aria-modal="true" aria-labelledby="cart-drawer-title">
        <header><div><small>只保存在这台设备上</small><h2 id="cart-drawer-title">模拟购物车</h2></div><button type="button" aria-label="关闭模拟购物车" onClick={onClose}><X aria-hidden="true" /></button></header>
        {cartItems.length ? <ul>{cartItems.map((item) => <li key={item.id}><span><ShoppingBag aria-hidden="true" /></span><div><strong>{item.name}</strong><small>{item.categoryLabel}</small></div><b>× {cart[item.id]}</b></li>)}</ul> : <p className="cart-drawer__empty">购物车还是空的，先选一件用品看看吧。</p>}
        <DemoUnavailable className="cart-checkout" actionLabel="模拟结算" subject="下单与支付" />
      </section>
    </div>
  );
}
