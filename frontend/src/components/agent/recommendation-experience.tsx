"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { components } from "../../lib/api/generated";
import { ApiClientError, createApiClient, type ApiClient } from "../../lib/api/client";
import { clearSessionReference, inspectSessionReference } from "../../lib/session";
import { SiteNav } from "../layout/site-nav";
import { ErrorFeedback } from "./error-feedback";
import { ExpiredDialog } from "./expired-dialog";
import { RecommendationResults } from "./recommendation-results";
import { SessionActions } from "./session-actions";

type Recommendation = components["schemas"]["PublicRecommendation"];
type Conversation = components["schemas"]["PublicConversationSummary"];
type Props = Readonly<{ api?: ApiClient; storage?: Pick<Storage, "getItem" | "setItem" | "removeItem"> }>;

export function RecommendationExperience({ api, storage }: Props) {
  const client = useMemo(() => api ?? createApiClient(), [api]);
  const browserStorage = useMemo(() => storage ?? (typeof window !== "undefined" ? window.localStorage : null), [storage]);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "empty" | "error" | "expired">("loading");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!browserStorage) return;
    const inspected = inspectSessionReference(browserStorage);
    if (inspected.status === "expired") { setState("expired"); return; }
    if (inspected.status !== "active") { setState("empty"); return; }
    setState("loading");
    setError("");
    try {
      const response = await client.getRecommendations(inspected.reference.conversationId);
      setConversation(response.data.conversation);
      setRecommendation(response.data.recommendation);
      setState("ready");
    } catch (cause) {
      if (cause instanceof ApiClientError && cause.code === "SESSION_EXPIRED") {
        clearSessionReference(browserStorage);
        setState("expired");
      } else {
        setError(cause instanceof ApiClientError ? cause.message : "暂时没能打开推荐，之前的聊天还在。");
        setState("error");
      }
    }
  }, [browserStorage, client]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return <div className="app-shell agent-shell result-shell">
    <header className="agent-header"><Link href="/agent" aria-label="返回选宠聊天"><ArrowLeft aria-hidden="true" /></Link><div><strong>推荐结果</strong><small>方向和具体宠物分开看</small></div><span aria-hidden="true" /></header>
    {state === "loading" && <main className="agent-state" role="status"><span className="gulu-avatar">咕</span><p>正在把这次的相遇名单整理好…</p></main>}
    {state === "empty" && <main className="agent-state"><h1>还没有整理好的推荐</h1><p>先聊聊你的日常，咕噜港再根据这次会话给出结果。</p><Link className="result-action" href="/agent">先去聊聊</Link></main>}
    {state === "expired" && <ExpiredDialog onStartNew={() => window.location.assign("/agent")} />}
    {state === "error" && <main className="agent-state"><h1>刚刚有点走神</h1><ErrorFeedback message={error} onRetry={() => void load()} /><Link className="result-text-link" href="/agent">回到聊天</Link></main>}
    {state === "ready" && recommendation && conversation && browserStorage && <>
      <RecommendationResults recommendation={recommendation} />
      <div className="result-session-actions"><SessionActions api={client} conversation={conversation} storage={browserStorage} onUpdated={(data) => {
        setConversation(data.conversation);
        if (data.recommendation) setRecommendation(data.recommendation);
        else window.location.assign("/agent");
      }} onResetComplete={() => window.location.assign("/agent")} /></div>
    </>}
    <SiteNav current="agent" />
  </div>;
}
