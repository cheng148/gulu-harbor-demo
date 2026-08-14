import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "../../lib/api/generated";
import { saveSessionReference } from "../../lib/session";
import { ExpiredDialog } from "./expired-dialog";
import { SessionActions } from "./session-actions";

type Conversation = components["schemas"]["PublicConversationSummary"];

const profile = {
  currentTimeArrangement: { status: "CONFIRMED" as const, value: "约5到8小时" },
  interactionRhythm: { status: "CONFIRMED" as const, value: "喜欢适度互动" },
  companionshipDistance: { status: "UNKNOWN" as const, value: null },
};

function conversation(revision = 3): Conversation {
  return {
    conversationId: "conv-t31",
    revision,
    stage: "RECOMMENDED",
    recommendationMode: "FINAL",
    profileSummary: profile,
    missingCriticalSlots: [],
    activeBlockers: [],
    conflicts: [],
    lastActiveAt: "2026-08-13T10:00:00.000Z",
    expiresAt: "2099-08-14T10:00:00.000Z",
  };
}

describe("T31 会话操作", () => {
  beforeEach(() => window.localStorage.clear());

  it("只修改用户选中的条件，并用新结果替换旧结果", async () => {
    const nextConversation = conversation(4);
    const api = {
      patchProfile: vi.fn().mockResolvedValue({
        data: {
          conversation: nextConversation,
          recommendation: { directions: [], pets: [] },
          recommendationChanges: [{ changeType: "LEVEL_CHANGED", subjectId: "pet-1", detail: "更适合安静陪伴" }],
          nextQuestion: null,
        },
      }),
      resetConversation: vi.fn(),
    };
    const onUpdated = vi.fn();

    render(<SessionActions api={api as never} conversation={conversation()} storage={window.localStorage} onUpdated={onUpdated} />);
    fireEvent.click(screen.getByRole("button", { name: "修改条件再看看" }));
    const dialog = screen.getByRole("dialog", { name: "想调整哪一项？" });
    fireEvent.click(within(dialog).getByRole("button", { name: /日常时间/ }));
    fireEvent.click(within(dialog).getByRole("button", { name: "每天可以稳定陪伴" }));
    fireEvent.click(within(dialog).getByRole("button", { name: "保存并重新推荐" }));

    await waitFor(() => expect(api.patchProfile).toHaveBeenCalledWith("conv-t31", {
      baseRevision: 3,
      updates: { currentTimeArrangement: { value: "MEDIUM", constraintStrength: "PREFERENCE" } },
    }));
    expect(onUpdated).toHaveBeenCalledWith(expect.objectContaining({ conversation: nextConversation }));
    expect(await screen.findByText("已经更新好啦")).toBeInTheDocument();
    expect(screen.getByText("更适合安静陪伴")).toBeInTheDocument();
  });

  it("修改失败时保留填写内容，并允许重试同一次修改", async () => {
    const api = {
      patchProfile: vi.fn()
        .mockRejectedValueOnce(new Error("offline"))
        .mockResolvedValueOnce({ data: { conversation: conversation(4), recommendation: null, recommendationChanges: [], nextQuestion: null } }),
      resetConversation: vi.fn(),
    };

    render(<SessionActions api={api as never} conversation={conversation()} storage={window.localStorage} onUpdated={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "修改条件再看看" }));
    fireEvent.click(screen.getByRole("button", { name: /互动节奏/ }));
    fireEvent.click(screen.getByRole("button", { name: "更偏安静陪伴" }));
    fireEvent.click(screen.getByRole("button", { name: "保存并重新推荐" }));

    expect(await screen.findByText("之前的推荐和填写内容都还在。" )).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "更偏安静陪伴" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "再试一次" }));
    await waitFor(() => expect(api.patchProfile).toHaveBeenCalledTimes(2));
  });

  it("主动重置必须先确认，成功后清除本地旧会话", async () => {
    saveSessionReference(window.localStorage, { conversationId: "conv-t31", expiresAt: "2099-08-14T10:00:00.000Z" });
    const api = { patchProfile: vi.fn(), resetConversation: vi.fn().mockResolvedValue(undefined) };
    const onResetComplete = vi.fn();

    render(<SessionActions api={api as never} conversation={conversation()} storage={window.localStorage} onUpdated={vi.fn()} onResetComplete={onResetComplete} />);
    fireEvent.click(screen.getByRole("button", { name: "重新开始" }));
    expect(api.resetConversation).not.toHaveBeenCalled();
    const dialog = screen.getByRole("dialog", { name: "要重新认识一次吗？" });
    fireEvent.click(within(dialog).getByRole("button", { name: "确认重置" }));

    await waitFor(() => expect(api.resetConversation).toHaveBeenCalledWith("conv-t31"));
    expect(window.localStorage.getItem("gulu-harbor.session.v1")).toBeNull();
    expect(onResetComplete).toHaveBeenCalledOnce();
  });
});

describe("T31 会话过期", () => {
  it("明确说明旧信息不会继续使用，并由用户主动开始新聊天", () => {
    const onStartNew = vi.fn();
    render(<ExpiredDialog onStartNew={onStartNew} />);

    expect(screen.getByRole("heading", { name: "这次聊天已经靠岸啦" })).toBeInTheDocument();
    expect(screen.getByText("超过24小时没有活动，我们不会拿旧信息继续推荐。" )).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "开始一次新聊天" }));
    expect(onStartNew).toHaveBeenCalledOnce();
  });
});
