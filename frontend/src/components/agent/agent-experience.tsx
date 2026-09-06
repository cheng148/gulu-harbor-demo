"use client";

import Link from "next/link";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { components } from "../../lib/api/generated";
import { ApiClientError, createApiClient, type ApiClient } from "../../lib/api/client";
import { clearSessionReference, inspectSessionReference, saveSessionReference } from "../../lib/session";
import { SiteNav } from "../layout/site-nav";
import { Conversation, type ConversationMessage, type ConversationQuestion } from "./conversation";
import { ErrorFeedback } from "./error-feedback";
import { ExpiredDialog } from "./expired-dialog";
import { ProfileSummary, type ProfileSlot } from "./profile-summary";
import { SessionActions } from "./session-actions";

type ConversationSummary = components["schemas"]["PublicConversationSummary"];
type TurnData = components["schemas"]["TurnData"];
const titles: Readonly<Record<string, string>> = {
  "ask-current-time": "先聊聊你的日常",
  "ask-relationship-style": "聊聊你期待的陪伴",
  "ask-daily-burden": "哪些日常更重要",
  "ask-direction-and-size": "说说心里的偏爱",
  "ask-age-stage": "想从哪段时光认识",
  "ask-coat-and-appearance": "聊聊喜欢的模样",
  "confirm-species-allergy": "推荐前轻轻确认",
};
type Props = Readonly<{ api?: ApiClient; storage?: Pick<Storage, "getItem" | "setItem" | "removeItem">; onRecommendationReady?: () => void }>;

export function AgentExperience({ api, storage, onRecommendationReady }: Props) {
  const client = useMemo(() => api ?? createApiClient(), [api]);
  const [conversation, setConversation] = useState<ConversationSummary | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [question, setQuestion] = useState<ConversationQuestion | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error" | "expired">("loading");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [lastAttempt, setLastAttempt] = useState<Readonly<{ content: string; quickReplyId: string | null }> | null>(null);
  const browserStorage = useMemo(() => storage ?? (typeof window !== "undefined" ? window.localStorage : null), [storage]);

  const start = useCallback(async (forceNew = false) => {
    if (!browserStorage) return;
    setState("loading");
    setError("");
    try {
      const inspected = forceNew ? { status: "missing" as const } : inspectSessionReference(browserStorage);
      if (inspected.status === "expired") { setState("expired"); return; }
      if (inspected.status === "active") {
        const response = await client.getConversation(inspected.reference.conversationId);
        setConversation(response.data.conversation);
        setMessages([...response.data.messages]);
        setQuestion(response.data.currentQuestion);
        saveSessionReference(browserStorage, { conversationId: response.data.conversation.conversationId, expiresAt: response.data.conversation.expiresAt });
      } else {
        const response = await client.createConversation();
        setConversation(response.data.conversation);
        setMessages([response.data.assistantMessage]);
        setQuestion(response.data.nextQuestion);
        saveSessionReference(browserStorage, { conversationId: response.data.conversation.conversationId, expiresAt: response.data.conversation.expiresAt });
      }
      setState("ready");
    } catch (cause) {
      if (cause instanceof ApiClientError && cause.code === "SESSION_EXPIRED") {
        clearSessionReference(browserStorage);
        setState("expired");
      } else {
        setError(cause instanceof ApiClientError ? cause.message : "暂时没能开始聊天，请稍后再试。");
        setState("error");
      }
    }
  }, [browserStorage, client]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void start(); }, 0);
    return () => window.clearTimeout(timer);
  }, [start]);

  function applyTurn(next: TurnData) {
    setConversation(next.conversation);
    setQuestion(next.nextQuestion);
    if (next.assistantMessage) setMessages((current) => [...current, next.assistantMessage]);
    if (browserStorage) saveSessionReference(browserStorage, { conversationId: next.conversation.conversationId, expiresAt: next.conversation.expiresAt });
    if (next.recommendation) (onRecommendationReady ?? (() => window.location.assign("/agent/results")))();
  }

  async function answer(content: string, quickReplyId: string | null) {
    if (!conversation || !browserStorage) return;
    setIsSending(true);
    setError("");
    setLastAttempt({ content, quickReplyId });
    try {
      const response = await client.sendMessage(conversation.conversationId, { clientMessageId: `web-${crypto.randomUUID()}`, baseRevision: conversation.revision, content, quickReplyId });
      setMessages((current) => [...current, { messageId: `local-${crypto.randomUUID()}`, role: "USER", content }]);
      setLastAttempt(null);
      applyTurn(response.data);
    } catch (cause) {
      if (cause instanceof ApiClientError && cause.code === "SESSION_EXPIRED") {
        clearSessionReference(browserStorage);
        setState("expired");
      } else {
        setError(cause instanceof ApiClientError ? cause.message : "这句话暂时没送到，请再试一次。");
      }
    } finally { setIsSending(false); }
  }

  const pageTitle = question ? titles[question.questionId] ?? "继续认识彼此" : "这轮聊天整理好了";
  return <div className="app-shell agent-shell">
    <header className="agent-header"><Link href="/" aria-label="返回首页"><ArrowLeft aria-hidden="true" /></Link><div><h1>{pageTitle}</h1>{conversation && <small><CheckCircle2 aria-hidden="true" />保存至 {new Date(conversation.expiresAt).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}</small>}</div><span aria-hidden="true" /></header>
    <main className="agent-main">
      {state === "loading" && <div className="agent-state" role="status"><span className="gulu-avatar">咕</span><p>正在把聊天的小桌子收拾好…</p></div>}
      {state === "error" && <div className="agent-state" role="alert"><h1>刚刚有点走神</h1><p>{error}</p><button type="button" onClick={() => void start()}>再试一次</button></div>}
      {state === "expired" && <ExpiredDialog onStartNew={() => void start(true)} />}
      {state === "ready" && conversation && browserStorage && <>
        <Conversation messages={messages} question={question} isSending={isSending} onAnswer={answer}/>
        {error && lastAttempt && <ErrorFeedback message={error} onRetry={() => void answer(lastAttempt.content, lastAttempt.quickReplyId)} />}
        <ProfileSummary slots={conversation.profileSummary as Readonly<Record<string, ProfileSlot>>} conflicts={conversation.conflicts}/>
        <SessionActions api={client} conversation={conversation} storage={browserStorage} allowModify={false} onUpdated={applyTurn} onResetComplete={() => void start(true)} />
        <aside className="privacy-note"><strong>只聊选宠需要的生活信息</strong><span>不用填写姓名、电话、住址或医疗记录；这次无账户会话保存24小时。</span></aside>
      </>}
    </main>
    <SiteNav current="agent" />
  </div>;
}
