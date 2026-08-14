import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import MembershipPage from "../../app/membership/page";
import MePage from "../../app/me/page";
import { createPrototypeStore } from "../../lib/prototype-store";
import { SiteNav } from "../layout/site-nav";

describe("T39会员中心和我的原型", () => {
  beforeEach(() => window.localStorage.clear());

  it("统一导航的四个入口都有真实路由，并正确标记我的", () => {
    render(<SiteNav current="me" />);

    expect(screen.getByRole("link", { name: "首页" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "选宠" })).toHaveAttribute("href", "/agent");
    expect(screen.getByRole("link", { name: "社区" })).toHaveAttribute("href", "/community");
    expect(screen.getByRole("link", { name: "我的" })).toHaveAttribute("href", "/me");
    expect(screen.getByRole("link", { name: "我的" })).toHaveAttribute("aria-current", "page");
  });

  it("会员展示状态只在本机切换，并明确不是实际开通", () => {
    render(<MembershipPage />);

    expect(screen.getByText("当前为普通展示状态")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "预览会员状态" }));
    expect(screen.getByText("当前为会员展示状态")).toBeInTheDocument();
    expect(screen.getByText(/仅改变本机Demo页面/)).toBeInTheDocument();
    expect(createPrototypeStore(window.localStorage).load().demoMembership).toBe(true);
  });

  it("选择会员套餐后仍阻止真实开通，不产生成功或订单", () => {
    render(<MembershipPage />);

    fireEvent.click(screen.getByRole("button", { name: "选择年度会员" }));
    expect(screen.getByRole("button", { name: "选择年度会员" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "确认开通年度会员" }));

    const dialog = screen.getByRole("dialog", { name: "这项功能还在准备中" });
    expect(within(dialog).getByText("Demo演示功能，暂未开放。")).toBeInTheDocument();
    expect(screen.queryByText(/开通成功|支付成功|订单号/)).not.toBeInTheDocument();
  });

  it("我的只汇总本机原型状态，并可进入会员中心", () => {
    const store = createPrototypeStore(window.localStorage);
    store.toggleFavorite("xiaomai");
    store.togglePostLike("community-home-day-30");
    store.addCartItem("supply-food-1");
    store.addCartItem("supply-food-1");
    render(<MePage />);

    expect(screen.getByText("无账户Demo体验")).toBeInTheDocument();
    expect(screen.getByLabelText("本机收藏数量")).toHaveTextContent("1");
    expect(screen.getByLabelText("本机点赞数量")).toHaveTextContent("1");
    expect(screen.getByLabelText("模拟购物车数量")).toHaveTextContent("2");
    expect(screen.getByRole("link", { name: "进入会员中心" })).toHaveAttribute("href", "/membership");
  });
});
