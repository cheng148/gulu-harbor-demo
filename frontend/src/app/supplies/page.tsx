"use client";

import Link from "next/link";
import { ArrowLeft, Bone, BriefcaseMedical, PackageOpen, ShoppingBag, Sparkles, UtensilsCrossed } from "lucide-react";
import { useMemo, useState } from "react";

import { CartDrawer } from "../../components/prototype/cart-drawer";
import { SiteNav } from "../../components/layout/site-nav";
import { ItemGrid } from "../../components/prototype/item-grid";
import prototypeData from "../../data/prototype.json";
import { createPrototypeStore } from "../../lib/prototype-store";
import { usePrototypeState } from "../../lib/use-prototype-state";

type Category = "all" | "food" | "toys" | "care" | "travel";
const categories = [["all", "全部用品"], ["food", "日常吃喝"], ["toys", "玩具互动"], ["care", "清洁护理"], ["travel", "安心出行"]] as const;
const icons = { food: UtensilsCrossed, toys: Bone, care: Sparkles, travel: BriefcaseMedical };
export default function SuppliesPage() {
  const [category, setCategory] = useState<Category>("all");
  const state = usePrototypeState();
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [feedbackCount, setFeedbackCount] = useState<number | null>(null);
  const items = useMemo(() => prototypeData.supplies.items.filter((item) => category === "all" || item.category === category), [category]);
  const cartCount = Object.values(state.cart).reduce((sum, quantity) => sum + quantity, 0);

  function addToCart(id: string) {
    setFeedbackCount(cartCount + 1);
    createPrototypeStore(window.localStorage).addCartItem(id);
  }

  return (
    <div className="app-shell prototype-shell">
      <main className="prototype-page">
        <header className="prototype-header"><Link href="/" aria-label="返回首页"><ArrowLeft aria-hidden="true" /></Link><div><small>模拟用品橱窗</small><h1>宠物用品</h1></div><span>Demo</span></header>
        <p className="prototype-intro">用品可以放进本地模拟购物车体验；销量和好评率都是Demo虚拟数据，不会产生真实订单。</p>
        <div className="prototype-filters supplies-filters" aria-label="用品分类">{categories.map(([value, label]) => <button key={value} type="button" aria-pressed={category === value} onClick={() => setCategory(value)}>{label}</button>)}</div>
        <ItemGrid>{items.map((item) => { const Icon = icons[item.category as keyof typeof icons] ?? PackageOpen; return <article className="prototype-card supply-card" aria-label={`${item.name}商品`} key={item.id}><div className={`supply-art supply-art--${item.category}`}><Icon aria-hidden="true" /><span>Demo虚拟商品</span></div><div className="prototype-card__body"><small>{item.categoryLabel}</small><h2>{item.name}</h2><p>{item.note}</p><div className="supply-metrics"><span>模拟销量 {item.sold}</span><span>模拟好评 {item.praise}%</span></div><button type="button" aria-label={`把${item.name}加入模拟购物车`} onClick={() => addToCart(item.id)}>加入模拟购物车</button></div></article>; })}</ItemGrid>
      </main>
      {cartCount > 0 && <div className="fixed-cart-bar" data-testid="fixed-cart-bar"><ShoppingBag aria-hidden="true" /><span role="status" aria-label="加入购物车反馈">{feedbackCount === null ? `本机模拟购物车共有 ${cartCount} 件用品` : `已加入模拟购物车，本机共有 ${feedbackCount} 件用品`}</span><button type="button" aria-label="打开模拟购物车" onClick={() => setIsCartOpen(true)}>查看</button></div>}
      <CartDrawer isOpen={isCartOpen} cart={state.cart} items={prototypeData.supplies.items} onClose={() => setIsCartOpen(false)} />
      <SiteNav />
    </div>
  );
}
