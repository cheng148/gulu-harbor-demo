import type { components } from "./generated";

type Schemas = components["schemas"];
type CreateConversationResponse = Schemas["CreateConversationResponse"];
type GetConversationResponse = Schemas["GetConversationResponse"];
type TurnResponse = Schemas["TurnResponse"];
type RecommendationResponse = Schemas["RecommendationResponse"];
type SendMessageRequest = Schemas["SendMessageRequest"];
type PatchProfileRequest = Schemas["PatchProfileRequest"];
type PublicErrorResponse = Schemas["PublicErrorResponse"];

export type ApiClientOptions = Readonly<{
  baseUrl?: string;
  fetcher?: typeof fetch;
}>;

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly retryable: boolean;
  readonly details: Readonly<Record<string, unknown>>;
  readonly requestId?: string;

  constructor(input: {
    status: number;
    code: string;
    message: string;
    retryable: boolean;
    details?: Readonly<Record<string, unknown>>;
    requestId?: string;
  }) {
    super(input.message);
    this.name = "ApiClientError";
    this.status = input.status;
    this.code = input.code;
    this.retryable = input.retryable;
    this.details = input.details ?? {};
    this.requestId = input.requestId;
  }
}

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

function isPublicErrorResponse(value: unknown): value is PublicErrorResponse {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  if (typeof candidate.error !== "object" || candidate.error === null) return false;
  const error = candidate.error as Record<string, unknown>;
  return (
    typeof error.code === "string" &&
    typeof error.message === "string" &&
    typeof error.retryable === "boolean"
  );
}

export function createApiClient(options: ApiClientOptions = {}) {
  const baseUrl = normalizeBaseUrl(
    options.baseUrl ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "",
  );
  const fetcher = options.fetcher ?? fetch;

  async function request<T>(
    path: string,
    init: RequestInit,
    expectedStatus: number,
  ): Promise<T> {
    const response = await fetcher(`${baseUrl}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    if (response.status === expectedStatus) {
      if (expectedStatus === 204) return undefined as T;
      return (await response.json()) as T;
    }

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }

    if (isPublicErrorResponse(payload)) {
      throw new ApiClientError({
        status: response.status,
        code: payload.error.code,
        message: payload.error.message,
        retryable: payload.error.retryable,
        details: payload.error.details,
        requestId: payload.meta.requestId,
      });
    }

    throw new ApiClientError({
      status: response.status,
      code: "INVALID_API_RESPONSE",
      message: "服务返回了无法识别的内容，请稍后再试。",
      retryable: response.status >= 500,
    });
  }

  const conversationPath = (conversationId: string) =>
    `/api/v1/conversations/${encodeURIComponent(conversationId)}`;

  return {
    createConversation: () =>
      request<CreateConversationResponse>(
        "/api/v1/conversations",
        { method: "POST", body: JSON.stringify({ clientLocale: "zh-CN" }) },
        201,
      ),
    getConversation: (conversationId: string) =>
      request<GetConversationResponse>(
        conversationPath(conversationId),
        { method: "GET" },
        200,
      ),
    sendMessage: (conversationId: string, body: SendMessageRequest) =>
      request<TurnResponse>(
        `${conversationPath(conversationId)}/messages`,
        { method: "POST", body: JSON.stringify(body) },
        200,
      ),
    patchProfile: (conversationId: string, body: PatchProfileRequest) =>
      request<TurnResponse>(
        `${conversationPath(conversationId)}/profile`,
        { method: "PATCH", body: JSON.stringify(body) },
        200,
      ),
    getRecommendations: (conversationId: string) =>
      request<RecommendationResponse>(
        `${conversationPath(conversationId)}/recommendations`,
        { method: "GET" },
        200,
      ),
    resetConversation: (conversationId: string) =>
      request<void>(
        conversationPath(conversationId),
        { method: "DELETE" },
        204,
      ),
  } as const;
}

export type ApiClient = ReturnType<typeof createApiClient>;
