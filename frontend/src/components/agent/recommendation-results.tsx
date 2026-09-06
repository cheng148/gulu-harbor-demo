import type { components } from "../../lib/api/generated";
import { DirectionCard } from "./direction-card";
import { PetCard } from "./pet-card";
import { RiskNotes } from "./risk-notes";

type Recommendation = components["schemas"]["PublicRecommendation"];

export function RecommendationResults({ recommendation }: Readonly<{ recommendation: Recommendation }>) {
  const allDirectionsCaution = recommendation.directions.length > 0 && recommendation.directions.every((item) => item.matchLevel === "CAUTION");
  const allPetsCaution = recommendation.pets.length > 0 && recommendation.pets.every((item) => item.matchLevel === "CAUTION");
  const petsByDirection = new Set(recommendation.pets.map((pet) => pet.directionId));
  return <main className="result-main">
    <section className="result-hero"><small>这次的相遇名单</small><h1>从方向到具体伙伴，慢慢认识</h1><p>{recommendation.priorityMessage ?? "先看生活方式更合拍的方向，再认识当前候选档案。"}</p></section>
    {recommendation.aiNarrative && <section className="ai-narrative" aria-labelledby="ai-narrative-title">
      <span className="section-kicker">AI整理说明</span>
      <h2 id="ai-narrative-title">选宠搭子帮你捋一捋</h2>
      <p>{recommendation.aiNarrative.intro}</p>
      {recommendation.aiNarrative.items.length > 0 && <ul>{recommendation.aiNarrative.items.map((item) => <li key={item.subjectId}>{item.text}</li>)}</ul>}
    </section>}
    <section className="result-section" aria-labelledby="direction-title"><span className="section-kicker">第一层 · 群体倾向</span><h2 id="direction-title">先看适合你的方向</h2><p>这里回答“什么品种或类型更接近你的日常”，不保证每只个体都一样。</p><div className="result-list">{recommendation.directions.map((direction, index) => <DirectionCard key={direction.directionId} direction={direction} index={index} allCaution={allDirectionsCaution} hasPet={petsByDirection.has(direction.directionId)} />)}</div></section>
    <section className="result-section" aria-labelledby="pet-title"><span className="section-kicker">第二层 · 个体档案</span><h2 id="pet-title">再认识具体的小伙伴</h2><p>这些是模拟合作商家的预置档案，不是现场生成的宠物。</p>{recommendation.pets.length ? <div className="result-list">{recommendation.pets.map((pet, index) => <PetCard key={pet.petId} pet={pet} index={index} allCaution={allPetsCaution} />)}</div> : <p className="pet-empty">{recommendation.petAvailabilityNote ?? "当前Demo暂无合适候选"}</p>}</section>
    <RiskNotes risks={recommendation.generalRisks} disclaimer={recommendation.disclaimer} />
  </main>;
}
