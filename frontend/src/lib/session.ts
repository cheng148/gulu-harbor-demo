export const SESSION_STORAGE_KEY = "gulu-harbor.session.v1";

export type SessionReference = Readonly<{
  conversationId: string;
  expiresAt: string;
}>;

type SessionStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

function isSessionReference(value: unknown): value is SessionReference {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  if (Object.keys(candidate).sort().join(",") !== "conversationId,expiresAt") {
    return false;
  }
  return (
    typeof candidate.conversationId === "string" &&
    candidate.conversationId.trim().length > 0 &&
    typeof candidate.expiresAt === "string" &&
    Number.isFinite(Date.parse(candidate.expiresAt))
  );
}

export function saveSessionReference(
  storage: SessionStorage,
  reference: SessionReference,
): void {
  if (!isSessionReference(reference)) {
    throw new TypeError("Invalid session reference.");
  }
  storage.setItem(SESSION_STORAGE_KEY, JSON.stringify(reference));
}

export function clearSessionReference(storage: SessionStorage): void {
  storage.removeItem(SESSION_STORAGE_KEY);
}

export type SessionInspection =
  | Readonly<{ status: "active"; reference: SessionReference }>
  | Readonly<{ status: "missing" | "expired" | "invalid" }>;

export function inspectSessionReference(
  storage: SessionStorage,
  now = new Date(),
): SessionInspection {
  const stored = storage.getItem(SESSION_STORAGE_KEY);
  if (stored === null) return { status: "missing" };

  try {
    const reference: unknown = JSON.parse(stored);
    if (!isSessionReference(reference)) {
      clearSessionReference(storage);
      return { status: "invalid" };
    }
    if (Date.parse(reference.expiresAt) <= now.getTime()) {
      clearSessionReference(storage);
      return { status: "expired" };
    }
    return { status: "active", reference };
  } catch {
    clearSessionReference(storage);
    return { status: "invalid" };
  }
}
export function loadSessionReference(
  storage: SessionStorage,
  now = new Date(),
): SessionReference | null {
  const result = inspectSessionReference(storage, now);
  return result.status === "active" ? result.reference : null;
}
