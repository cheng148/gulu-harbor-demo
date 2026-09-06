"use client";

import Link from "next/link";
import { ArrowLeft, Plus } from "lucide-react";
import { useState } from "react";

import { DemoUnavailable } from "../../components/demo/demo-unavailable";
import { SiteNav } from "../../components/layout/site-nav";
import { communityPosts } from "../../components/community/community-data";
import styles from "../../components/community/community.module.css";
import { PostCard, type CommunityPost } from "../../components/community/post-card";
import { PostDialog } from "../../components/community/post-dialog";
import { createPrototypeStore } from "../../lib/prototype-store";
import { usePrototypeState } from "../../lib/use-prototype-state";

export default function CommunityPage() {
  const state = usePrototypeState();
  const [selectedPost, setSelectedPost] = useState<CommunityPost | null>(null);

  function toggleLike(id: string) {
    createPrototypeStore(window.localStorage).togglePostLike(id);
  }

  function toggleFavorite(id: string) {
    createPrototypeStore(window.localStorage).toggleFavorite(id);
  }

  return (
    <div className="app-shell prototype-shell">
      <main className={`${styles.page} prototype-page`}>
        <header className="prototype-header"><Link href="/" aria-label="返回首页"><ArrowLeft aria-hidden="true" /></Link><div><small>港湾里的相处故事</small><h1>社区</h1></div><span>Demo</span></header>
        <section className={styles.intro}><div><span>虚构改写内容</span><h2>看看大家怎样慢慢熟悉彼此</h2><p>这里可以浏览、点赞和收藏；真实发帖与评论暂未开放。</p></div><DemoUnavailable actionLabel="发布动态" ariaLabel="发布动态" subject="真实社区发帖" className={styles.publish}><Plus aria-hidden="true" />发布动态</DemoUnavailable></section>
        <div className={styles.feed}>
          {communityPosts.map((post) => <PostCard key={post.id} post={post} isLiked={state.likedPostIds.includes(post.id)} isFavorite={state.favoriteIds.includes(post.id)} onToggleLike={() => toggleLike(post.id)} onToggleFavorite={() => toggleFavorite(post.id)} onOpen={() => setSelectedPost(post)} eagerImage />)}
        </div>
      </main>
      <SiteNav current="community" />
      <PostDialog post={selectedPost} onClose={() => setSelectedPost(null)} />
    </div>
  );
}
