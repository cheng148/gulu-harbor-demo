import type { components } from "../../lib/api/generated";
import { costCopy, matchCopy, positionCopy } from "./result-copy";

type Direction = components["schemas"]["PublicDirectionResult"];

function Reasons({ title, items, tone = "plain" }: Readonly<{ title: string; items: readonly string[]; tone?: string }>) {
  if (items.length === 0) return null;
  return <section className={`result-reasons result-reasons--${tone}`}><strong>{title}</strong><ul>{items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></section>;
}

export function DirectionCard({ direction, index, allCaution, hasPet }: Readonly<{ direction: Direction; index: number; allCaution: boolean; hasPet: boolean }>) {
  const pendingCopy: Readonly<Record<string, string>> = { DIRECTION_SIZE: "品种与体型", AGE: "年龄阶段", COAT_APPEARANCE: "毛发与外观" };
  const pending = direction.pendingItems.map((item) => pendingCopy[item] ?? item);
  return <article className="direction-card" aria-label={`${direction.name}方向`}>
    <div className="result-position">{positionCopy(index, allCaution)}</div>
    <header><span><small>{direction.kind === "TYPE" ? "类型方向" : "品种方向"}</small><strong>{direction.name}</strong></span><i data-level={direction.matchLevel}>{matchCopy[direction.matchLevel]}</i></header>
    <Reasons title="为什么更接近你" items={direction.suitableReasons} />
    <Reasons title="要接受的小代价" items={direction.tradeoffs} tone="tradeoff" />
    <Reasons title="还没对上的地方" items={direction.mismatchPoints} tone="mismatch" />
    <Reasons title="再确认会更稳妥" items={pending} tone="pending" />
    <div className="cost-strip"><span>获取负担 <b>{costCopy[direction.acquisitionCostLevel]}</b></span><span>长期照护 <b>{costCopy[direction.ongoingCareCostLevel]}</b></span></div>
    {!hasPet && <p className="no-candidate">当前Demo暂无合适候选</p>}
    <p className="evidence-note">{direction.evidenceNote}</p>
    <div className="evidence-links" aria-label="方向资料来源">{direction.evidence.map((item) => <a key={item.sourceId} href={item.sourceLocator} target="_blank" rel="noreferrer">资料来源：{item.sourceName}</a>)}</div>
  </article>;
}
