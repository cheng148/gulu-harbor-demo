import Image from "next/image";
import { Bookmark, Heart, MessageCircle } from "lucide-react";

import styles from "./community.module.css";

export type CommunityPost = {
  id: string;
  title: string;
  author: string;
  pet: string;
  image: string;
  excerpt: string;
  body: string;
  tag: string;
  likes: number;
};

type PostCardProps = {
  post: CommunityPost;
  isLiked: boolean;
  isFavorite: boolean;
  onToggleLike: () => void;
  onToggleFavorite: () => void;
  onOpen: () => void;
};

export function PostCard({ post, isLiked, isFavorite, onToggleLike, onToggleFavorite, onOpen }: PostCardProps) {
  return (
    <article className={styles.card} aria-label={`${post.title}社区帖子`}>
      <button className={styles.cover} type="button" aria-label={`从配图查看${post.title}`} onClick={onOpen}>
        <Image src={post.image} alt={`${post.pet}的Demo帖子配图`} width={1254} height={1254} />
        <span>Demo虚拟内容</span>
      </button>
      <div className={styles.body}>
        <div className={styles.meta}><span>{post.tag}</span><small>{post.pet}</small></div>
        <button className={styles.titleButton} type="button" onClick={onOpen}><h2>{post.title}</h2></button>
        <p>{post.excerpt}</p>
        <small className={styles.author}>来自 {post.author}</small>
        <div className={styles.actions}>
          <button className={isLiked ? styles.active : ""} type="button" aria-label={`${isLiked ? "取消点赞" : "点赞"}${post.title}`} aria-pressed={isLiked} onClick={onToggleLike}><Heart aria-hidden="true" fill={isLiked ? "currentColor" : "none"} /><span>{post.likes + (isLiked ? 1 : 0)}</span></button>
          <button type="button" aria-label={`查看${post.title}详情`} onClick={onOpen}><MessageCircle aria-hidden="true" /><span>详情</span></button>
          <button className={isFavorite ? styles.active : ""} type="button" aria-label={`${isFavorite ? "取消收藏" : "收藏"}${post.title}`} aria-pressed={isFavorite} onClick={onToggleFavorite}><Bookmark aria-hidden="true" fill={isFavorite ? "currentColor" : "none"} /><span>{isFavorite ? "已收藏" : "收藏"}</span></button>
        </div>
      </div>
    </article>
  );
}
