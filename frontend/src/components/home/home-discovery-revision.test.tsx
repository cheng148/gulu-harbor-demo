import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "../../app/page";

describe("首页发现信息分层", () => {
  it("具体宠物只展示关注度，不把独一个体写成有销量或好评率", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { name: "近期人气榜" })).toBeInTheDocument();

    for (const name of ["小麦", "阿福", "奶盖", "土豆"]) {
      const card = screen.getByRole("article", { name: `${name}宠物档案` });
      expect(within(card).getByText(/近7天浏览/)).toBeInTheDocument();
      expect(within(card).getByText(/人想进一步了解/)).toBeInTheDocument();
      expect(within(card).queryByText(/销量|好评/)).not.toBeInTheDocument();
    }
  });

  it("单独展示品种层面的模拟商家汇总数据", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { name: "本期热门品种" })).toBeInTheDocument();
    const ragdoll = screen.getByRole("article", { name: "布偶猫热门品种" });
    expect(within(ragdoll).getByText(/近30天模拟成交/)).toBeInTheDocument();
    expect(within(ragdoll).getByText(/相关交易好评率/)).toBeInTheDocument();
    expect(within(ragdoll).getByText(/当前模拟在售/)).toBeInTheDocument();
    expect(within(ragdoll).getByText("Demo虚拟数据")).toBeInTheDocument();
  });

  it("使用原型搜索图标和固定语义的四个底栏图标", () => {
    render(<Home />);

    expect(screen.getByRole("searchbox", { name: "搜索宠物、品种或合作店铺" })).toBeInTheDocument();
    expect(document.querySelector('[data-icon="search"]')).toBeInTheDocument();

    for (const icon of ["home", "pet-paw", "community", "profile"]) {
      expect(document.querySelector(`[data-icon="${icon}"]`)).toBeInTheDocument();
    }
  });

  it("顶部补充24小时本地保存提示", () => {
    render(<Home />);

    expect(screen.getByText("24小时本地保存")).toBeInTheDocument();
  });
});
