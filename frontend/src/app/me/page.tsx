"use client";

import Link from "next/link";
import { Bookmark, ChevronRight, Crown, FileText, Heart, UserRound } from "lucide-react";

import styles from "../../components/account/account.module.css";
import { DemoUnavailable } from "../../components/demo/demo-unavailable";
import { SiteNav } from "../../components/layout/site-nav";
import { usePrototypeState } from "../../lib/use-prototype-state";

export default function MePage() {
  const state = usePrototypeState();
  const cartCount = Object.values(state.cart).reduce((sum, quantity) => sum + quantity, 0);
  return <div className="app-shell prototype-shell"><main className={styles.page}>
    <section className={styles.hero}><div className={styles.avatar}>咕</div><div><small>无账户Demo体验</small><h1>我的港湾</h1><p>这里只整理保存在本机的原型互动，不代表真实账户资料。</p></div></section>
    <div className={styles.stats}><div className={styles.stat} aria-label="本机收藏数量"><strong>{state.favoriteIds.length}</strong><span>本机收藏</span></div><div className={styles.stat} aria-label="本机点赞数量"><strong>{state.likedPostIds.length}</strong><span>社区点赞</span></div><div className={styles.stat} aria-label="模拟购物车数量"><strong>{cartCount}</strong><span>模拟购物车</span></div></div>
    <nav className={styles.menu} aria-label="我的功能"><Link href="/membership" aria-label="进入会员中心"><Crown aria-hidden="true" /><span><strong>会员中心</strong><small>{state.demoMembership ? "当前为会员展示状态" : "查看普通与会员展示状态"}</small></span><ChevronRight aria-hidden="true" /></Link><DemoUnavailable actionLabel="我的收藏" ariaLabel="我的收藏" subject="跨页面收藏整理"><Bookmark aria-hidden="true" /><span><strong>我的收藏</strong><small>当前仅展示上方本机数量</small></span><ChevronRight aria-hidden="true" /></DemoUnavailable><DemoUnavailable actionLabel="真实订单" ariaLabel="真实订单" subject="真实账户订单"><FileText aria-hidden="true" /><span><strong>我的订单</strong><small>Demo不创建真实订单</small></span><ChevronRight aria-hidden="true" /></DemoUnavailable><DemoUnavailable actionLabel="账户资料" ariaLabel="账户资料" subject="真实账户资料"><UserRound aria-hidden="true" /><span><strong>账户资料</strong><small>首版不建设登录和账户系统</small></span><ChevronRight aria-hidden="true" /></DemoUnavailable></nav>
    <p className={styles.localNote}><Heart aria-hidden="true" size={12} /> 收藏、点赞和购物车仅保存在这台设备的浏览器中；清理浏览器数据后会消失。</p>
  </main><SiteNav current="me" /></div>;
}
