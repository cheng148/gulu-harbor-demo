export const PROTOTYPE_STORAGE_KEY = "gulu-harbor.prototype.v1";
export const PROTOTYPE_STORAGE_EVENT = "gulu-harbor:prototype-state";

export type PrototypeState = {
  favoriteIds: string[];
  likedPostIds: string[];
  cart: Record<string, number>;
  demoMembership: boolean;
};

const emptyState = (): PrototypeState => ({
  favoriteIds: [],
  likedPostIds: [],
  cart: {},
  demoMembership: false,
});

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isCart(value: unknown): value is Record<string, number> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  return Object.entries(value).every(
    ([id, quantity]) => id.length > 0
      && typeof quantity === "number"
      && Number.isInteger(quantity)
      && quantity > 0,
  );
}

export function parsePrototypeState(raw: string | null): PrototypeState {
  if (!raw) return emptyState();
  try {
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object" || Array.isArray(value)) return emptyState();
    const state = value as Partial<PrototypeState>;
    if (!isStringArray(state.favoriteIds) || !isStringArray(state.likedPostIds)
      || !isCart(state.cart) || typeof state.demoMembership !== "boolean") return emptyState();
    return {
      favoriteIds: [...new Set(state.favoriteIds)],
      likedPostIds: [...new Set(state.likedPostIds)],
      cart: { ...state.cart },
      demoMembership: state.demoMembership,
    };
  } catch {
    return emptyState();
  }
}

function toggled(items: string[], id: string): string[] {
  return items.includes(id) ? items.filter((item) => item !== id) : [...items, id];
}

export function createPrototypeStore(storage: Pick<Storage, "getItem" | "setItem">) {
  const load = () => parsePrototypeState(storage.getItem(PROTOTYPE_STORAGE_KEY));
  const save = (state: PrototypeState) => {
    storage.setItem(PROTOTYPE_STORAGE_KEY, JSON.stringify(state));
    if (typeof window !== "undefined" && storage === window.localStorage) {
      window.dispatchEvent(new Event(PROTOTYPE_STORAGE_EVENT));
    }
    return state;
  };

  return {
    load,
    toggleFavorite(id: string) {
      const state = load();
      return save({ ...state, favoriteIds: toggled(state.favoriteIds, id) });
    },
    togglePostLike(id: string) {
      const state = load();
      return save({ ...state, likedPostIds: toggled(state.likedPostIds, id) });
    },
    addCartItem(id: string) {
      const state = load();
      return save({ ...state, cart: { ...state.cart, [id]: (state.cart[id] ?? 0) + 1 } });
    },
    setDemoMembership(enabled: boolean) {
      return save({ ...load(), demoMembership: enabled });
    },
  };
}
