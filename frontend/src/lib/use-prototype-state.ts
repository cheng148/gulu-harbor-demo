"use client";

import { useMemo, useSyncExternalStore } from "react";

import { PROTOTYPE_STORAGE_EVENT, PROTOTYPE_STORAGE_KEY, parsePrototypeState } from "./prototype-store";

function subscribe(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(PROTOTYPE_STORAGE_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(PROTOTYPE_STORAGE_EVENT, onStoreChange);
  };
}

function getSnapshot() {
  return window.localStorage.getItem(PROTOTYPE_STORAGE_KEY);
}

export function usePrototypeState() {
  const raw = useSyncExternalStore(subscribe, getSnapshot, () => null);
  return useMemo(() => parsePrototypeState(raw), [raw]);
}
