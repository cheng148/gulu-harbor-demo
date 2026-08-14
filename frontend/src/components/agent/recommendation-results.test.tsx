import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { components } from "../../lib/api/generated";
import { RecommendationResults } from "./recommendation-results";

type Recommendation = components["schemas"]["PublicRecommendation"];

const evidence = {
  sourceId: "bluecross-finding-right-pet",
  sourceName: "Blue Cross",
  sourceLocator: "https://www.bluecross.org.uk/advice/pets/wellbeing-and-care/finding-the-right-pet",
} as const;

function recommendation(pets: Recommendation["pets"]): Recommendation {
  return {
    directions: [
      {
        directionId: "cat-adult-local-mix",
        name: "成年本地／混种短毛猫",
        kind: "TYPE",
        matchLevel: "HIGH",
        suitableReasons: ["相处节奏更接近你期待的安静陪伴"],
        tradeoffs: ["换毛期仍需要规律梳理和清洁"],
        mismatchPoints: [],
        pendingItems: [],
        acquisitionCostLevel: "LOW",
        ongoingCareCostLevel: "MEDIUM",
        evidence: [evidence],
        evidenceNote: "方向只表达群体倾向，仍要结合个体档案。",
        sourceIds: [evidence.sourceId],
      },
      {
        directionId: "cat-ragdoll",
        name: "布偶猫",
        kind: "BREED",
        matchLevel: "MEDIUM",
        suitableReasons: ["陪伴距离接近你的偏好"],
        tradeoffs: ["长毛护理投入更高"],
        mismatchPoints: [],
        pendingItems: ["完整工作日独处表现待确认"],
        acquisitionCostLevel: "HIGH",
        ongoingCareCostLevel: "MEDIUM_HIGH",
        evidence: [{ ...evidence, sourceId: "tica-ragdoll", sourceName: "The International Cat Association" }],
        evidenceNote: "品种描述不代表每只猫都一样。",
        sourceIds: ["tica-ragdoll"],
      },
    ],
    pets,
    generalRisks: ["品种或类型只表示群体倾向，具体个体仍需继续了解"],
    disclaimer: "咕噜港负责匹配并帮助联系商家进一步了解，不直接销售宠物。",
    priorityMessage: "先从更接近你日常的方向看起。",
    petAvailabilityNote: pets.length ? null : "当前Demo暂无合适候选",
  };
}

const xiaomai = {
  petId: "pet-cat-local-01",
  nickname: "小麦",
  directionId: "cat-adult-local-mix",
  matchLevel: "HIGH",
  suitableReasons: ["已观察到它熟悉后喜欢待在人附近"],
  tradeoffs: ["换环境后可能暂时躲藏"],
  mismatchPoints: [],
  pendingItems: [],
  knownNotes: ["短时间独处观察较稳定"],
  unknownFields: ["完整工作日独处表现"],
  acquisitionCostLevel: "LOW",
  ongoingCareCostLevel: "MEDIUM",
  sourceIds: [evidence.sourceId],
  evidence: [evidence],
  merchant: { merchantId: "merchant-harbor", displayName: "港湾宠物生活馆（模拟商家）", isSimulated: true },
  dataNature: "DEMO_SIMULATED",
  listingStatus: "SIMULATED_AVAILABLE",
  listingDisclosure: "Demo模拟数据，不代表真实在售",
  contactAction: { available: false, label: "联系商家进一步了解", type: "DEMO_CONTACT_MERCHANT", unavailableMessage: "Demo演示功能，暂未开放。" },
} as const;

describe("T30 双层推荐结果", () => {
  it("把品种／类型方向与具体候选宠物分层展示，并显示依据和代价", () => {
    render(<RecommendationResults recommendation={recommendation([xiaomai])} />);

    expect(screen.getByRole("heading", { name: "先看适合你的方向" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "再认识具体的小伙伴" })).toBeInTheDocument();
    expect(screen.getByText("成年本地／混种短毛猫")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "小麦" })).toBeInTheDocument();
    expect(screen.getAllByText("很合拍")).toHaveLength(2);
    expect(screen.getAllByText("要接受的小代价")).not.toHaveLength(0);
    expect(screen.getAllByRole("link", { name: /Blue Cross/ })).not.toHaveLength(0);
    expect(screen.getByText("Demo模拟数据，不代表真实在售")).toBeInTheDocument();
  });

  it("页面只显示匹配等级，不泄漏内部数字分", () => {
    const { container } = render(<RecommendationResults recommendation={recommendation([xiaomai])} />);
    const text = container.textContent ?? "";

    expect(text).not.toMatch(/matchScore|rawScore|内部数字分|\b\d{1,3}分\b/);
    expect(text).not.toContain("%");
  });

  it("联系模拟商家的入口使用统一未开放反馈", () => {
    render(<RecommendationResults recommendation={recommendation([xiaomai])} />);
    fireEvent.click(screen.getByRole("button", { name: "联系商家进一步了解" }));

    expect(screen.getByRole("dialog", { name: "这项功能还在准备中" })).toHaveTextContent("Demo演示功能，暂未开放。");
    expect(screen.queryByText(/联系成功/)).not.toBeInTheDocument();
  });

  it("方向成立但没有合适个体时明确说明，不临时凑宠物", () => {
    render(<RecommendationResults recommendation={recommendation([])} />);

    const direction = screen.getByRole("article", { name: "成年本地／混种短毛猫方向" });
    expect(within(direction).getByText("当前Demo暂无合适候选")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 3 })).not.toBeInTheDocument();
  });

  it("需要磨合时明确展示尚未解决的差距", () => {
    const result = recommendation([]);
    const caution: Recommendation = {
      ...result,
      directions: [{
        ...result.directions[0],
        matchLevel: "CAUTION",
        mismatchPoints: ["你当前可投入的活动时间低于这个方向的日常需要"],
      }],
      priorityMessage: "目前没有特别合拍的选择，先看看相对更接近的方向。",
    };
    render(<RecommendationResults recommendation={caution} />);

    expect(screen.getByText("需要磨合")).toBeInTheDocument();
    expect(screen.getByText("还没对上的地方")).toBeInTheDocument();
    expect(screen.getByText(/活动时间低于/)).toBeInTheDocument();
    expect(screen.queryByText("优先看看")).not.toBeInTheDocument();
  });
});
