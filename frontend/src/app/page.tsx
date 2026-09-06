"use client";

import Image from "next/image";
import Link from "next/link";
import { CheckCircle2, Search, ShoppingBag, Store } from "lucide-react";
import { useMemo, useState } from "react";

import { DemoUnavailable } from "../components/demo/demo-unavailable";
import { AgentCta } from "../components/home/agent-cta";
import { SiteNav } from "../components/layout/site-nav";
import prototypeData from "../data/prototype.json";

type Category = "all" | "cat" | "dog" | "shops";

const { pets, breeds, shops } = prototypeData.home;

const tabs: Array<{ id: Category; label: string }> = [
  { id: "all", label: "全部" },
  { id: "cat", label: "猫猫" },
  { id: "dog", label: "狗狗" },
  { id: "shops", label: "合作店铺" },
];

export default function Home() {
  const [category, setCategory] = useState<Category>("all");
  const [query, setQuery] = useState("");
  const keyword = query.trim().toLowerCase();

  const visiblePets = useMemo(() => {
    if (category === "shops") return [];
    return pets.filter((pet) => (category === "all" || pet.kind === category) && (!keyword || `${pet.name}${pet.breed}`.toLowerCase().includes(keyword)));
  }, [category, keyword]);

  const visibleBreeds = useMemo(() => {
    if (category === "shops") return [];
    return breeds.filter((breed) => (category === "all" || breed.kind === category) && (!keyword || breed.name.toLowerCase().includes(keyword)));
  }, [category, keyword]);

  return (
    <div className="app-shell">
      <main className="market-home">
        <header className="home-header">
          <Image className="home-logo" src="/assets/gulu/gulu-logo-lighthouse.png" alt="咕噜港" width={1774} height={887} priority />
          <div className="home-status"><span><CheckCircle2 aria-hidden="true" size={16} />24小时本地保存</span><p>去认识一个新伙伴吧</p></div>
        </header>
        <div className="harbor-divider" aria-hidden="true"><span /><i>≈</i><span /></div>

        <aside className="virtual-banner" aria-label="数据说明"><strong>Demo虚拟数据</strong><span>个体关注度、品种与店铺交易指标均为演示数据</span></aside>

        <label className="search-box">
          <Search data-icon="search" aria-hidden="true" size={19} strokeWidth={2} />
          <input aria-label="搜索宠物、品种或合作店铺" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索宠物、品种或合作店铺" />
        </label>

        <AgentCta />

        <nav className="discovery-entries" aria-label="逛逛咕噜港">
          <Link href="/market" aria-label="逛宠物市场"><span><Store aria-hidden="true" /></span><div><strong>宠物市场</strong><small>看看具体的小伙伴</small></div><b>›</b></Link>
          <Link href="/supplies" aria-label="看看宠物用品"><span><ShoppingBag aria-hidden="true" /></span><div><strong>宠物用品</strong><small>准备相处的小物件</small></div><b>›</b></Link>
        </nav>

        <div className="category-tabs" aria-label="首页分类">
          {tabs.map((tab) => <button className={category === tab.id ? "is-active" : ""} key={tab.id} type="button" aria-pressed={category === tab.id} onClick={() => setCategory(tab.id)}>{tab.label}</button>)}
        </div>

        {category !== "shops" && (
          <section className="content-section" id="recommendations">
            <div className="section-heading"><div><p>大家最近常来看</p><h1>近期人气榜</h1></div><span>近7天模拟热度</span></div>
            {visiblePets.length ? <div className="pet-grid">{visiblePets.map((pet, index) => (
              <article className="pet-card" aria-label={`${pet.name}宠物档案`} key={pet.id}>
                <div className="card-image-wrap"><Image src={`/assets/gulu/pet-${pet.id}.png`} alt={`${pet.name}的模拟在售档案照片`} width={1254} height={1254} loading={index === 0 ? "eager" : "lazy"} /><span>Demo虚拟数据</span></div>
                <div className="pet-card__body"><div className="pet-card__title"><h2>{pet.name}</h2><span>{pet.breed}</span></div><p>{pet.note}</p><div className="demo-metrics pet-interest"><span>近7天浏览 {pet.views.toLocaleString("zh-CN")} 次</span><span>{pet.interested} 人想进一步了解</span></div><DemoUnavailable actionLabel="看看档案" subject={`${pet.name}档案查看`} /></div>
              </article>
            ))}</div> : <p className="empty-state">暂时没找到相符的小伙伴，换个关键词试试吧。</p>}
          </section>
        )}

        {category !== "shops" && visibleBreeds.length > 0 && (
          <section className="content-section breeds-section" aria-label="本期热门品种">
            <div className="section-heading"><div><p>商家交易汇总</p><h2>本期热门品种</h2></div><span>近30天模拟数据</span></div>
            <p className="section-note">这里反映的是模拟合作商家的交易情况，不代表对整个品种的性格、健康或品质评价。</p>
            <div className="breed-list">{visibleBreeds.map((breed) => (
              <article className="breed-card" aria-label={`${breed.name}热门品种`} key={breed.name}>
                <Image src={breed.image} alt={`${breed.name}示意照片`} width={1254} height={1254} />
                <div className="breed-card__body"><span className="demo-chip">Demo虚拟数据</span><h3>{breed.name}</h3><div className="breed-metrics"><span>近30天模拟成交 {breed.sold}</span><span>相关交易好评率 {breed.praise}%</span><span>当前模拟在售 {breed.available} 只</span></div></div>
              </article>
            ))}</div>
          </section>
        )}

        {(category === "all" || category === "shops") && (
          <section className="content-section shops-section">
            <div className="section-heading"><div><p>合作店铺</p><h2>港湾里的伙伴商家</h2></div><span>近30天模拟数据</span></div>
            <div className="shop-list">{shops.map((shop) => (
              <article className="shop-card" key={shop.name}><Image src={shop.image} alt="模拟合作店铺宠物照片" width={1254} height={1254} /><div><span className="demo-chip">Demo虚拟数据</span><h3>{shop.name}</h3><p>{shop.note}</p><strong>模拟成交 {shop.sold} · 店铺模拟好评 {shop.praise}%</strong></div><DemoUnavailable actionLabel="进店看看" subject={`${shop.name}真实店铺访问`} /></article>
            ))}</div>
          </section>
        )}
      </main>

      <SiteNav current="home" />
    </div>
  );
}
