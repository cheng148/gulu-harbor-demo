import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import CommunityPage from "../../app/community/page";
import HomePage from "../../app/page";

describe("T38社区原型", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("可以浏览模拟帖子，并在本机点赞和收藏", () => {
    render(<CommunityPage />);

    expect(screen.getByRole("heading", { name: "社区" })).toBeInTheDocument();
    expect(screen.getAllByRole("article").length).toBeGreaterThanOrEqual(2);

    fireEvent.click(screen.getByRole("button", { name: "点赞小麦来到家的第30天" }));
    expect(screen.getByRole("button", { name: "取消点赞小麦来到家的第30天" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "收藏雨天也能玩的嗅闻小游戏" }));
    expect(screen.getByRole("button", { name: "取消收藏雨天也能玩的嗅闻小游戏" })).toBeInTheDocument();
    expect(window.localStorage.getItem("gulu-harbor.prototype.v1")).toContain("community-rainy-day");
  });

  it("可以打开和关闭模拟帖子详情", () => {
    render(<CommunityPage />);

    fireEvent.click(screen.getByRole("button", { name: "查看小麦来到家的第30天详情" }));
    const dialog = screen.getByRole("dialog", { name: "小麦来到家的第30天" });
    expect(within(dialog).getByText(/从躲在沙发后面，到愿意主动靠近/)).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole("button", { name: "关闭帖子详情" }));
    expect(screen.queryByRole("dialog", { name: "小麦来到家的第30天" })).not.toBeInTheDocument();
  });

  it("发布动态只显示统一Demo提示，不产生发布成功状态", () => {
    render(<CommunityPage />);

    fireEvent.click(screen.getByRole("button", { name: "发布动态" }));
    const dialog = screen.getByRole("dialog", { name: "这项功能还在准备中" });
    expect(within(dialog).getByText("Demo演示功能，暂未开放。")).toBeInTheDocument();
    expect(screen.queryByText(/发布成功/)).not.toBeInTheDocument();
  });

  it("首页底栏的社区入口可以进入社区页面", () => {
    render(<HomePage />);
    expect(screen.getByRole("link", { name: "社区" })).toHaveAttribute("href", "/community");
  });
});
