import Image from "next/image";

import { DemoUnavailable } from "../demo/demo-unavailable";
import type { components } from "../../lib/api/generated";
import { costCopy, matchCopy, positionCopy } from "./result-copy";

type Pet = components["schemas"]["PublicPetResult"];
const imageByPet: Readonly<Record<string, string>> = {
  "pet-cat-local-01": "/assets/gulu/pet-xiaomai.png",
  "pet-cat-british-02": "/assets/gulu/pet-naigai.png",
  "pet-dog-local-01": "/assets/gulu/pet-afu.png",
  "pet-dog-corgi-01": "/assets/gulu/pet-tudou.png",
};

function Notes({ title, items, tone = "plain" }: Readonly<{ title: string; items: readonly string[]; tone?: string }>) {
  if (items.length === 0) return null;
  return <section className={`result-reasons result-reasons--${tone}`}><strong>{title}</strong><ul>{items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></section>;
}

export function PetCard({ pet, index, allCaution }: Readonly<{ pet: Pet; index: number; allCaution: boolean }>) {
  const image = imageByPet[pet.petId];
  const pendingCopy: Readonly<Record<string, string>> = { DIRECTION_SIZE: "品种与体型", AGE: "年龄阶段", COAT_APPEARANCE: "毛发与外观" };
  const pending = [...pet.pendingItems, ...pet.unknownFields].map((item) => pendingCopy[item] ?? item);
  return <article className="result-pet-card" aria-label={`${pet.nickname}候选宠物档案`}>
    <div className="result-position">{positionCopy(index, allCaution)}</div>
    <Image src={image ?? "/assets/gulu/harbor-hero.png"} width={1024} height={1024} loading={index === 0 ? "eager" : "lazy"} alt={image ? `${pet.nickname}的Demo模拟候选宠物档案插画` : `${pet.nickname}档案的港湾主题占位插画`} />
    <div className="result-pet-card__body"><header><span><small>具体候选宠物</small><h3>{pet.nickname}</h3></span><i data-level={pet.matchLevel}>{matchCopy[pet.matchLevel]}</i></header>
      <p className="listing-chip">{pet.listingDisclosure}</p>
      <Notes title="这只小伙伴的合拍点" items={pet.suitableReasons} />
      <Notes title="要接受的小代价" items={pet.tradeoffs} tone="tradeoff" />
      <Notes title="还没对上的地方" items={pet.mismatchPoints} tone="mismatch" />
      <Notes title="档案里还不知道" items={pending} tone="pending" />
      <div className="cost-strip"><span>获取负担 <b>{costCopy[pet.acquisitionCostLevel]}</b></span><span>长期照护 <b>{costCopy[pet.ongoingCareCostLevel]}</b></span></div>
      <p className="merchant-line">来自 {pet.merchant.displayName}</p>
      <div className="evidence-links" aria-label="个体档案资料来源">{pet.evidence.map((item) => <a key={item.sourceId} href={item.sourceLocator} target="_blank" rel="noreferrer">资料来源：{item.sourceName}</a>)}</div>
        <DemoUnavailable
          actionLabel={pet.contactAction.label}
          subject={`${pet.merchant.displayName}真实联系`}
        />
    </div>
  </article>;
}
