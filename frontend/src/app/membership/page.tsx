"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useState } from "react";

import { DemoAccountState } from "../../components/account/demo-account-state";
import styles from "../../components/account/account.module.css";
import { DemoUnavailable } from "../../components/demo/demo-unavailable";
import { SiteNav } from "../../components/layout/site-nav";

type Plan = "月度会员" | "年度会员";

export default function MembershipPage() {
  const [plan, setPlan] = useState<Plan>("月度会员");
  return <div className="app-shell prototype-shell"><main className={styles.page}>
    <header className="prototype-header"><Link href="/me" aria-label="返回我的"><ArrowLeft aria-hidden="true" /></Link><div><small>会员展示原型</small><h1>会员中心</h1></div><span>Demo</span></header>
    <DemoAccountState />
    <section className={styles.sectionTitle}><small>模拟套餐选择</small><h2>先看看页面怎样呈现</h2><p>第一版尚未确认价格和正式权益，因此这里只演示套餐选择与开通边界。</p></section>
    <div className={styles.plans}>{(["月度会员", "年度会员"] as const).map((item) => <button className={styles.plan} type="button" aria-label={`选择${item}`} aria-pressed={plan === item} onClick={() => setPlan(item)} key={item}><strong>{item}</strong><span>不展示价格，不代表真实可购买套餐。</span></button>)}</div>
    <DemoUnavailable className={styles.openButton} actionLabel={`确认开通${plan}`} ariaLabel={`确认开通${plan}`} subject={`${plan}付费开通`} />
    <p className={styles.boundary}>价格、权益、续费和退款规则仍待产品确认。本页不会创建订单、会员身份或任何费用。</p>
  </main><SiteNav current="me" /></div>;
}
