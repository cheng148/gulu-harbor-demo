import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "../../app/page";

describe("咕噜港首页", () => {
  it("把AI选宠作为首页最清晰的主入口", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: "不知道选谁？先从你的生活聊起" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "去聊聊" })).toHaveAttribute("href", "/agent");
  });

  it("页面和个体、品种、店铺卡片都明确标记为虚拟数据", () => {
    render(<Home />);
    expect(screen.getByText("个体关注度、品种与店铺交易指标均为演示数据")).toBeInTheDocument();
    expect(screen.getAllByText("Demo虚拟数据")).toHaveLength(11);
    for (const name of ["小麦", "阿福", "奶盖", "土豆"]) {
      const card = screen.getByRole("article", { name: `${name}宠物档案` });
      expect(within(card).queryByText(/销量|好评/)).not.toBeInTheDocument();
    }
    expect(screen.getAllByText(/相关交易好评率/)).toHaveLength(4);
    expect(screen.getAllByText(/店铺模拟好评/)).toHaveLength(2);
  });

  it("可以按猫狗筛选，也能切换到合作店铺", () => {
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: "猫猫" }));
    expect(screen.getByText("小麦")).toBeInTheDocument();
    expect(screen.queryByText("阿福")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "合作店铺" }));
    expect(screen.getByText("海风宠物生活馆")).toBeInTheDocument();
    expect(screen.queryByText("小麦")).not.toBeInTheDocument();
  });

  it("底部导航保持四个固定图标入口并高亮首页", () => {
    render(<Home />);
    const navigation = screen.getByRole("navigation", { name: "主导航" });
    expect(navigation).toHaveTextContent("首页");
    expect(navigation).toHaveTextContent("选宠");
    expect(navigation).toHaveTextContent("社区");
    expect(navigation).toHaveTextContent("我的");
    expect(screen.getByRole("link", { name: "首页" })).toHaveAttribute("aria-current", "page");
    expect(navigation.querySelectorAll("svg")).toHaveLength(4);
  });

  it("首页受限动作复用统一的未开放反馈", () => {
    render(<Home />);
    const card = screen.getByRole("article", { name: "小麦宠物档案" });
    fireEvent.click(within(card).getByRole("button", { name: "看看档案" }));

    expect(screen.getByRole("dialog", { name: "这项功能还在准备中" })).toHaveTextContent("Demo演示功能，暂未开放。");
    expect(screen.queryByText(/查看成功|联系成功/)).not.toBeInTheDocument();
  });
});
