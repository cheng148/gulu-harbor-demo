import type { components } from "../../lib/api/generated";

export type MatchLevel = components["schemas"]["MatchLevel"];
export type CostLevel = components["schemas"]["CostLevel"];

export const matchCopy: Readonly<Record<MatchLevel, string>> = {
  HIGH: "很合拍",
  MEDIUM: "值得认识",
  CAUTION: "需要磨合",
};

export const costCopy: Readonly<Record<CostLevel, string>> = {
  LOW: "较轻",
  MEDIUM: "适中",
  MEDIUM_HIGH: "偏高",
  HIGH: "较高",
};

export function positionCopy(index: number, allCaution: boolean): string {
  if (allCaution) return `相对更接近 · ${index + 1}`;
  return index < 2 ? `优先看看 · ${index + 1}` : `再认识一下 · ${index + 1}`;
}
