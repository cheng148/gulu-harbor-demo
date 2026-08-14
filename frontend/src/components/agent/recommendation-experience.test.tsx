import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { saveSessionReference } from "../../lib/session";
import { RecommendationExperience } from "./recommendation-experience";

describe("T30 推荐结果页会话连接", () => {
  beforeEach(() => window.localStorage.clear());

  it("读取当前24小时会话并展示已经生成的结果", async () => {
    saveSessionReference(window.localStorage, { conversationId: "conv-ready", expiresAt: "2099-08-14T10:00:00.000Z" });
    const api = { getRecommendations: vi.fn().mockResolvedValue({ data: { conversation: { conversationId: "conv-ready", expiresAt: "2099-08-14T10:00:00.000Z" }, recommendation: { directions: [], pets: [], generalRisks: [], disclaimer: "不直接销售宠物。", priorityMessage: null, petAvailabilityNote: "当前Demo暂无合适候选" } } }) };

    render(<RecommendationExperience api={api as never} storage={window.localStorage} />);

    expect(await screen.findByText("当前Demo暂无合适候选")).toBeInTheDocument();
    expect(api.getRecommendations).toHaveBeenCalledWith("conv-ready");
  });

  it("没有当前会话时引导用户先完成聊天，不伪造推荐", async () => {
    const api = { getRecommendations: vi.fn() };
    render(<RecommendationExperience api={api as never} storage={window.localStorage} />);

    expect(await screen.findByRole("heading", { name: "还没有整理好的推荐" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "先去聊聊" })).toHaveAttribute("href", "/agent");
    expect(api.getRecommendations).not.toHaveBeenCalled();
  });
});
