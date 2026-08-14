"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Heart, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { ItemGrid } from "../../components/prototype/item-grid";
import { SiteNav } from "../../components/layout/site-nav";
import prototypeData from "../../data/prototype.json";
import { createPrototypeStore } from "../../lib/prototype-store";
import { usePrototypeState } from "../../lib/use-prototype-state";

type Kind = "all" | "cat" | "dog";

export default function MarketPage() {
  const [kind, setKind] = useState<Kind>("all");
  const [query, setQuery] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const { favoriteIds } = usePrototypeState();
  const keyword = query.trim().toLowerCase();
  const categories = useMemo(() => prototypeData.market.categories.filter((category) =>
    (kind === "all" || category.kind === kind)
    && (!keyword || category.name.toLowerCase().includes(keyword)),
  ), [kind, keyword]);
  const selectedCategory = prototypeData.market.categories.find((category) => category.id === selectedCategoryId);
  const pets = selectedCategoryId ? prototypeData.market.pets.filter((pet) => pet.categoryId === selectedCategoryId) : [];

  function toggleFavorite(id: string) {
    createPrototypeStore(window.localStorage).toggleFavorite(id);
  }

  return (
    <div className="app-shell prototype-shell">
      <main className="prototype-page">
        <header className="prototype-header">
          {selectedCategory ? <button type="button" aria-label="返回品种列表" onClick={() => setSelectedCategoryId(null)}><ArrowLeft aria-hidden="true" /></button> : <Link href="/" aria-label="返回首页"><ArrowLeft aria-hidden="true" /></Link>}
          <div><small>模拟合作商家档案</small><h1>宠物市场</h1></div>
          <span>Demo</span>
        </header>

        {selectedCategory ? <>
          <p className="prototype-intro">先从品种方向认识，再查看每只独立个体和它所在的模拟合作商家。</p>
          <div className="market-detail-heading"><span>Demo虚拟档案</span><h2>{selectedCategory.name}的小伙伴</h2><p>当前展示 2 只模拟在售个体</p></div>
          <ItemGrid>
            {pets.map((pet) => {
              const isFavorite = favoriteIds.includes(pet.id);
              return <article className="prototype-card market-card" aria-label={`${pet.name}宠物档案`} key={pet.id}>
                <div className="prototype-card__image"><Image src={pet.image} alt={`${pet.name}的模拟档案照片`} width={1254} height={1254} priority={pet.id === "naigai"} /><span>Demo虚拟档案</span></div>
                <div className="prototype-card__body"><div className="prototype-card__title"><div><h2>{pet.name}</h2><p>{pet.breed}</p></div><button className={isFavorite ? "is-favorite" : ""} type="button" aria-label={`${isFavorite ? "取消收藏" : "收藏"}${pet.name}`} onClick={() => toggleFavorite(pet.id)}><Heart aria-hidden="true" fill={isFavorite ? "currentColor" : "none"} /></button></div><p>{pet.note}</p><dl><div><dt>年龄</dt><dd>{pet.age}</dd></div><div><dt>体型</dt><dd>{pet.size}</dd></div></dl><small>所在商家 · {pet.merchant}</small><strong>近7天浏览 {pet.views.toLocaleString("zh-CN")} 次</strong></div>
              </article>;
            })}
          </ItemGrid>
        </> : <>
          <p className="prototype-intro">先选一个感兴趣的品种方向，再认识该品种下的具体小伙伴。</p>
          <label className="search-box prototype-search"><Search aria-hidden="true" size={19} /><input type="search" aria-label="搜索品种" placeholder="搜索品种" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
          <div className="prototype-filters" aria-label="宠物类型">
            {([['all', '全部'], ['cat', '只看猫猫'], ['dog', '只看狗狗']] as const).map(([value, label]) => <button key={value} type="button" aria-pressed={kind === value} onClick={() => setKind(value)}>{label}</button>)}
          </div>
          <ItemGrid emptyMessage="暂时没找到这个品种方向，换个关键词看看吧。">
            {categories.map((category) => <article className="prototype-card market-category-card" aria-label={`${category.name}品种`} key={category.id}>
              <div className="prototype-card__image"><Image src={category.image} alt={`${category.name}品种示意照片`} width={1254} height={1254} /><span>Demo虚拟数据</span></div>
              <div className="prototype-card__body"><small>{category.kind === "cat" ? "猫猫方向" : "狗狗方向"}</small><h2>{category.name}</h2><div className="category-metrics"><span>近30天模拟成交 {category.sold}</span><span>相关交易好评率 {category.praise}%</span><span>当前模拟在售 {category.available} 只</span></div><button type="button" aria-label={`查看${category.name}的模拟在售宠物`} onClick={() => setSelectedCategoryId(category.id)}>看看 2 位小伙伴</button></div>
            </article>)}
          </ItemGrid>
        </>}
      </main><SiteNav />
    </div>
  );
}
