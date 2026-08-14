import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AgentExperience } from "./agent-experience";

const expiresAt = "2026-08-14T10:00:00.000Z";

function conversation(revision = 0) {
  return {
    conversationId: "conv-t29",
    revision,
    stage: "DISCOVERING" as const,
    recommendationMode: "NONE" as const,
    profileSummary: {
      currentTimeArrangement: { status: revision ? "CONFIRMED" as const : "UNKNOWN" as const, value: revision ? "大约4到8小时" : null },
      interactionRhythm: { status: "UNKNOWN" as const, value: null },
      companionshipDistance: { status: "UNKNOWN" as const, value: null },
      disturbanceTolerance: { status: "CONFLICTED" as const, value: ["比较在意掉毛", "大多可以商量"] },
    },
    missingCriticalSlots: ["interactionRhythm"],
    activeBlockers: [],
    conflicts: revision ? ["日常负担的两次表达不太一致"] : [],
    lastActiveAt: "2026-08-13T10:00:00.000Z",
    expiresAt,
  };
}

function assistant(messageId: string, content: string) {
  return { messageId, role: "ASSISTANT" as const, content, createdAt: "2026-08-13T10:00:00.000Z" };
}

function api() {
  return {
    createConversation: vi.fn().mockResolvedValue({
      data: {
        conversation: conversation(),
        assistantMessage: assistant("welcome", "嗨，我是咕噜港的选宠搭子。"),
        nextQuestion: {
          questionId: "ask-current-time",
          text: "普通工作日里，宠物大约会独处多久？",
          quickReplies: ["独处较少，时间比较充足", "大约4到8小时"],
        },
      },
      meta: { requestId: "req-create" },
    }),
    getConversation: vi.fn(),
    sendMessage: vi.fn().mockResolvedValue({
      data: {
        conversation: conversation(1),
        assistantMessage: assistant("answer-1", "谢谢你说得这么清楚，我们再聊聊相处感觉。"),
        profileChanges: [{ slotName: "currentTimeArrangement", status: "CONFIRMED", value: "大约4到8小时" }],
        nextQuestion: {
          questionId: "ask-relationship-style",
          text: "你更期待怎样的相处感觉？",
          quickReplies: ["喜欢经常互动", "安静陪在附近"],
        },
        quickReplies: ["喜欢经常互动", "安静陪在附近"],
        recommendation: null,
        warnings: [],
        recommendationChanges: [],
      },
      meta: { requestId: "req-turn" },
    }),
    patchProfile: vi.fn(),
    getRecommendations: vi.fn(),
    resetConversation: vi.fn(),
  };
}

describe("AI选宠对话页", () => {
  beforeEach(() => window.localStorage.clear());

  it("一轮只展示一个主要问题，并同时提供快捷回答和自由输入", async () => {
    const client = api();
    render(<AgentExperience api={client} storage={window.localStorage} />);

    expect(await screen.findByText("先聊聊你的日常")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "普通工作日里，宠物大约会独处多久？" })).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "选宠对话" })).getAllByRole("heading", { level: 2 })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "大约4到8小时" })).toBeInTheDocument();
    expect(screen.getByLabelText("用自己的话回答")).toHaveAttribute("inputmode", "text");
  });

  it("快捷回答后切换标题、问题和画像，且不把未知项伪装成已确认", async () => {
    const client = api();
    render(<AgentExperience api={client} storage={window.localStorage} />);
    fireEvent.click(await screen.findByRole("button", { name: "大约4到8小时" }));

    expect(await screen.findByText("聊聊你期待的陪伴")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "你更期待怎样的相处感觉？" })).toBeInTheDocument();
    expect(client.sendMessage).toHaveBeenCalledWith("conv-t29", expect.objectContaining({ content: "大约4到8小时", quickReplyId: "大约4到8小时", baseRevision: 0 }));

    const profile = screen.getByRole("region", { name: "你的相处画像" });
    expect(within(profile).getByText("约4～8小时")).toBeInTheDocument();
    expect(within(profile).getAllByText("还没聊到")).not.toHaveLength(0);
    expect(within(profile).getAllByText("需要再聊聊")).not.toHaveLength(0);
  });

  it("中文自由输入按Enter发送，Shift+Enter保留换行", async () => {
    const client = api();
    render(<AgentExperience api={client} storage={window.localStorage} />);
    const input = await screen.findByLabelText("用自己的话回答");

    fireEvent.change(input, { target: { value: "我白天需要上班" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(client.sendMessage).not.toHaveBeenCalled();
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });

    await waitFor(() => expect(client.sendMessage).toHaveBeenCalledWith("conv-t29", expect.objectContaining({ content: "我白天需要上班", quickReplyId: null })));
  });
});
