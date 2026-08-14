"use client";

import { Crown, UserRound } from "lucide-react";

import { createPrototypeStore } from "../../lib/prototype-store";
import { usePrototypeState } from "../../lib/use-prototype-state";
import styles from "./account.module.css";

export function DemoAccountState() {
  const state = usePrototypeState();

  function preview(enabled: boolean) {
    createPrototypeStore(window.localStorage).setDemoMembership(enabled);
  }

  return <section className={`${styles.stateCard} ${state.demoMembership ? styles.memberState : ""}`} aria-label="会员展示状态">
    <div className={styles.stateIcon}>{state.demoMembership ? <Crown aria-hidden="true" /> : <UserRound aria-hidden="true" />}</div>
    <div><small>仅供页面预览</small><h2>{state.demoMembership ? "当前为会员展示状态" : "当前为普通展示状态"}</h2><p>仅改变本机Demo页面，不代表已经注册、付费或开通会员。</p></div>
    <div className={styles.stateActions}><button type="button" aria-pressed={!state.demoMembership} onClick={() => preview(false)}>预览普通状态</button><button type="button" aria-pressed={state.demoMembership} onClick={() => preview(true)}>预览会员状态</button></div>
  </section>;
}
