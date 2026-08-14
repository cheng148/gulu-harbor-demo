import Link from "next/link";
import { House, PawPrint, UserRound, UsersRound } from "lucide-react";

type SiteTab = "home" | "agent" | "community" | "me";

const items = [
  { id: "home", label: "首页", href: "/", Icon: House, icon: "home" },
  { id: "agent", label: "选宠", href: "/agent", Icon: PawPrint, icon: "pet-paw" },
  { id: "community", label: "社区", href: "/community", Icon: UsersRound, icon: "community" },
  { id: "me", label: "我的", href: "/me", Icon: UserRound, icon: "profile" },
] as const;

export function SiteNav({ current }: { current?: SiteTab }) {
  return <nav className="bottom-nav" aria-label="主导航">{items.map(({ id, label, href, Icon, icon }) => {
    const isCurrent = current === id;
    return <Link className={isCurrent ? "is-current" : undefined} href={href} aria-current={isCurrent ? "page" : undefined} aria-label={label} key={id}><span className="nav-icon"><Icon data-icon={icon} aria-hidden="true" /></span><small>{label}</small></Link>;
  })}</nav>;
}
