import { FormEvent, KeyboardEvent, useState } from "react";
import { QuickReplies } from "./quick-replies";

export type ConversationMessage = Readonly<{ messageId: string; role: "USER" | "ASSISTANT"; content: string }>;
export type ConversationQuestion = Readonly<{ questionId: string; text: string; quickReplies: readonly string[] }>;
type Props = Readonly<{ messages: readonly ConversationMessage[]; question: ConversationQuestion | null; isSending: boolean; onAnswer: (content: string, quickReplyId: string | null) => Promise<void> }>;

export function Conversation({ messages, question, isSending, onAnswer }: Props) {
  const [draft, setDraft] = useState("");
  async function submit(content: string, quickReplyId: string | null) {
    const trimmed = content.trim();
    if (!trimmed || isSending) return;
    await onAnswer(trimmed, quickReplyId);
    setDraft("");
  }
  function handleSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); void submit(draft, null); }
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void submit(draft, null); }
  }
  return <section className="agent-conversation" aria-label="选宠对话">
    <div className="chat-thread" aria-live="polite">{messages.map((message) => <div className={message.role === "USER" ? "user-message" : "assistant-message"} key={message.messageId}>{message.role === "ASSISTANT" && <span className="gulu-avatar" aria-hidden="true">咕</span>}<p>{message.content}</p></div>)}</div>
    {question && <article className="current-question"><span className="gulu-avatar" aria-hidden="true">咕</span><div><small>我根据刚才的话，再了解一点</small><h2>{question.text}</h2><p>不用找标准答案，按最接近你的情况说就好。</p></div></article>}
    {question && <p className="quick-help">可以直接点，也可以用自己的话说</p>}
    {question && <QuickReplies options={question.quickReplies} disabled={isSending} onSelect={(option) => void submit(option, option)} />}
    {question && <form className="chat-composer" onSubmit={handleSubmit}><label htmlFor="agent-answer">用自己的话回答</label><textarea id="agent-answer" inputMode="text" enterKeyHint="send" value={draft} maxLength={2000} disabled={isSending} onChange={(event) => setDraft(event.target.value)} onKeyDown={handleKeyDown} placeholder="比如：白天要上班，晚上可以陪它玩一会儿……"/><button type="submit" disabled={isSending || !draft.trim()}>{isSending ? "正在听你说…" : "发送给咕噜"}</button></form>}
  </section>;
}
