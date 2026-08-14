import { describe, expect, it, vi } from "vitest";

import { ApiClientError, createApiClient } from "./client";

describe("咕噜港API客户端", () => {
  it("未配置外部地址时通过当前网站的同源API访问", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status: 204 }));
    const client = createApiClient({ fetcher });

    await client.resetConversation("conv-local");

    expect(fetcher).toHaveBeenCalledWith("/api/v1/conversations/conv-local", expect.any(Object));
  });
  it("创建会话时只发送公共请求字段，不发送Key或Authorization", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            conversation: {
              conversationId: "conv-123",
              revision: 0,
              stage: "DISCOVERING",
              recommendationMode: "NONE",
              profileSummary: {},
              missingCriticalSlots: [],
              activeBlockers: [],
              conflicts: [],
              lastActiveAt: "2026-08-13T10:00:00Z",
              expiresAt: "2026-08-14T10:00:00Z",
            },
            assistantMessage: {
              messageId: "msg-1",
              role: "ASSISTANT",
              content: "欢迎来到咕噜港。",
              createdAt: "2026-08-13T10:00:00Z",
            },
            nextQuestion: {
              questionId: "q-1",
              text: "平时它大约会独处多久？",
              quickReplies: [],
            },
          },
          meta: { requestId: "req-1" },
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    );
    const client = createApiClient({ baseUrl: "http://localhost:8000", fetcher });

    const response = await client.createConversation();

    expect(response.data.conversation.conversationId).toBe("conv-123");
    expect(fetcher).toHaveBeenCalledOnce();
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/v1/conversations");
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({
      Accept: "application/json",
      "Content-Type": "application/json",
    });
    expect(JSON.stringify(init)).not.toMatch(/authorization|api.?key|deepseek|token/i);
  });

  it("把后端统一错误转换成前端可判断的错误", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "SESSION_EXPIRED",
            message: "这次聊天已经过期，请重新开始。",
            retryable: false,
            details: {},
          },
          meta: { requestId: "req-expired" },
        }),
        { status: 410, headers: { "Content-Type": "application/json" } },
      ),
    );
    const client = createApiClient({ baseUrl: "http://localhost:8000/", fetcher });

    const request = client.getConversation("conv-old");
    await expect(request).rejects.toBeInstanceOf(ApiClientError);
    await expect(request).rejects.toMatchObject({
      name: "ApiClientError",
      status: 410,
      code: "SESSION_EXPIRED",
      retryable: false,
      requestId: "req-expired",
    });
  });

  it("重置会话接受204空响应", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(null, { status: 204 }),
    );
    const client = createApiClient({ baseUrl: "http://localhost:8000", fetcher });

    await expect(client.resetConversation("conv-123")).resolves.toBeUndefined();
  });
});
