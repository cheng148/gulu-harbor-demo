"use client";

import { RotateCcw, SlidersHorizontal, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { components } from "../../lib/api/generated";
import { ApiClientError, type ApiClient } from "../../lib/api/client";
import { clearSessionReference, saveSessionReference } from "../../lib/session";
import { ErrorFeedback } from "./error-feedback";

type Conversation = components["schemas"]["PublicConversationSummary"];
type TurnData = components["schemas"]["TurnData"];
type SlotName = components["schemas"]["PublicProfileSlotName"];
type ProfileValue = components["schemas"]["PublicProfileValue"];
type EditChoice = Readonly<{ label: string; value: ProfileValue }>;
type EditableSlot = Readonly<{ name: SlotName; label: string; choices: readonly EditChoice[] }>;

const editable: readonly EditableSlot[] = [
  { name: "currentTimeArrangement", label: "日常时间", choices: [
    { label: "时间比较有限", value: "LOW" }, { label: "能安排一些时间", value: "LOW_MEDIUM" },
    { label: "每天可以稳定陪伴", value: "MEDIUM" }, { label: "时间很充足", value: "HIGH" },
  ] },
  { name: "interactionRhythm", label: "互动节奏", choices: [
    { label: "更偏安静陪伴", value: "LOW_MEDIUM" }, { label: "喜欢适度互动", value: "MEDIUM" },
    { label: "希望互动多一些", value: "MEDIUM_HIGH" }, { label: "喜欢经常一起玩", value: "HIGH" },
  ] },
  { name: "companionshipDistance", label: "陪伴距离", choices: [
    { label: "彼此留些空间", value: "INDEPENDENT" }, { label: "待在同一个房间", value: "SAME_ROOM" },
    { label: "安静陪在附近", value: "NEARBY" }, { label: "喜欢亲近一些", value: "CLOSE" },
  ] },
  { name: "ongoingInvestmentWillingness", label: "照护投入", choices: [
    { label: "希望负担轻一些", value: "LOW" }, { label: "可以稳定投入", value: "MEDIUM" },
    { label: "能接受较多打理", value: "MEDIUM_HIGH" }, { label: "愿意投入很多时间精力", value: "HIGH" },
  ] },
  { name: "agePreference", label: "年龄阶段", choices: [
    { label: "更偏幼年", value: "YOUNG" }, { label: "更偏成年", value: "ADULT" }, { label: "年龄都可以", value: "ANY" },
  ] },
  { name: "coatAppearancePreference", label: "毛发与外形", choices: [
    { label: "更偏短毛", value: ["SHORT_HAIR"] }, { label: "更偏长毛", value: ["LONG_HAIR", "SEMI_LONG_HAIR"] }, { label: "没有特别要求", value: ["ANY"] },
  ] },
  { name: "allergySpecies", label: "过敏情况", choices: [
    { label: "猫狗都不过敏", value: [] }, { label: "对猫过敏", value: ["CAT"] },
    { label: "对狗过敏", value: ["DOG"] }, { label: "还不确定", value: ["UNCERTAIN"] },
  ] },
];

const valueLabels = new Map(editable.flatMap((slot) => slot.choices.map((choice) => [JSON.stringify(choice.value), choice.label] as const)));
function displayValue(value: unknown): string {
  if (value == null) return "还没聊到";
  return valueLabels.get(JSON.stringify(value)) ?? (Array.isArray(value) ? value.join("、") : String(value));
}
function sameValue(left: unknown, right: unknown) { return JSON.stringify(left) === JSON.stringify(right); }

type Props = Readonly<{
  api: ApiClient;
  conversation: Conversation;
  storage: Pick<Storage, "getItem" | "setItem" | "removeItem">;
  onUpdated: (data: TurnData) => void;
  onResetComplete?: () => void;
  allowModify?: boolean;
}>;

export function SessionActions({ api, conversation, storage, onUpdated, onResetComplete, allowModify = true }: Props) {
  const profileSummary = useMemo(() => conversation.profileSummary ?? {}, [conversation.profileSummary]);
  const rows = useMemo(() => editable.filter((item) => item.name in profileSummary), [profileSummary]);
  const [panel, setPanel] = useState<"edit" | "reset" | null>(null);
  const [selected, setSelected] = useState<EditableSlot | null>(null);
  const [value, setValue] = useState<ProfileValue | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [changes, setChanges] = useState<readonly components["schemas"]["PublicRecommendationChange"][]>([]);
  const [success, setSuccess] = useState(false);

  function choose(item: EditableSlot) {
    setSelected(item);
    const current = profileSummary[item.name]?.value;
    setValue(item.choices.find((choice) => sameValue(choice.value, current))?.value ?? null);
    setError(""); setSuccess(false);
  }

  async function submit() {
    if (!selected || value === null) return;
    setPending(true); setError("");
    try {
      const response = await api.patchProfile(conversation.conversationId, {
        baseRevision: conversation.revision,
        updates: { [selected.name]: { value, constraintStrength: "PREFERENCE" } },
      });
      saveSessionReference(storage, { conversationId: response.data.conversation.conversationId, expiresAt: response.data.conversation.expiresAt });
      setChanges(response.data.recommendationChanges); setSuccess(true); onUpdated(response.data);
    } catch (cause) {
      setError(cause instanceof ApiClientError && cause.code === "REVISION_CONFLICT"
        ? "页面里的信息比当前会话旧了一步，请返回聊天页刷新后再改。"
        : "可能是网络或模型暂时没有回应，请再试一次。");
    } finally { setPending(false); }
  }

  async function reset() {
    setPending(true); setError("");
    try {
      await api.resetConversation(conversation.conversationId);
      clearSessionReference(storage); onResetComplete?.();
    } catch {
      setError("暂时没能重新开始，原来的聊天仍然保留着。请再试一次。"); setPanel("reset");
    } finally { setPending(false); }
  }

  return <section className="session-actions" aria-label="会话操作">
    {allowModify && <button className="session-actions__primary" type="button" onClick={() => { setPanel("edit"); setError(""); }}><SlidersHorizontal aria-hidden="true" />修改条件再看看</button>}
    <button className="session-actions__reset" type="button" onClick={() => { setPanel("reset"); setError(""); }}><RotateCcw aria-hidden="true" />重新开始</button>

    {panel === "edit" && <div className="session-dialog-backdrop"><section className="session-dialog" role="dialog" aria-modal="true" aria-labelledby="edit-title">
      <header><div><small>换个条件再看看</small><h2 id="edit-title">想调整哪一项？</h2></div><button type="button" aria-label="关闭修改条件" onClick={() => setPanel(null)}><X aria-hidden="true" /></button></header>
      <p>原来的答案会保留，只改你选择的这一项。</p>
      <div className="edit-slot-list">{rows.map((item) => <button type="button" className={selected?.name === item.name ? "is-selected" : ""} onClick={() => choose(item)} key={item.name}><span><small>{item.label}</small><strong>{displayValue(profileSummary[item.name]?.value)}</strong></span><i>{selected?.name === item.name ? "正在修改" : "选择"}</i></button>)}</div>
      {selected && <fieldset className="edit-choices"><legend>新的{selected.label}</legend>{selected.choices.map((choice) => <button type="button" aria-pressed={sameValue(value, choice.value)} className={sameValue(value, choice.value) ? "is-selected" : ""} onClick={() => setValue(choice.value)} key={choice.label}>{choice.label}</button>)}</fieldset>}
      {error && <ErrorFeedback message={error} onRetry={submit} />}
      {success && <div className="session-success" role="status"><strong>已经更新好啦</strong><span>{changes.length ? changes.map((item) => item.detail).join("；") : "新条件已经保存，推荐也重新整理好了。"}</span></div>}
      <button className="session-dialog__submit" type="button" disabled={!selected || value === null || pending} onClick={submit}>{pending ? "正在重新整理…" : "保存并重新推荐"}</button>
    </section></div>}

    {panel === "reset" && <div className="session-dialog-backdrop"><section className="session-dialog session-dialog--reset" role="dialog" aria-modal="true" aria-labelledby="reset-title">
      <header><div><small>重新开始</small><h2 id="reset-title">要重新认识一次吗？</h2></div><button type="button" aria-label="关闭重置确认" onClick={() => setPanel(null)}><X aria-hidden="true" /></button></header>
      <p>重置后，之前的回答和推荐不会带到新会话。</p>
      {error && <ErrorFeedback message={error} onRetry={reset} />}
      <button className="session-dialog__danger" type="button" disabled={pending} onClick={reset}>{pending ? "正在重新开始…" : "确认重置"}</button>
      <button className="session-dialog__cancel" type="button" onClick={() => setPanel(null)}>先不重置</button>
    </section></div>}
  </section>;
}
