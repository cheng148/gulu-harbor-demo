import Image from "next/image";
import { X } from "lucide-react";

import styles from "./community.module.css";
import type { CommunityPost } from "./post-card";

type PostDialogProps = { post: CommunityPost | null; onClose: () => void };

export function PostDialog({ post, onClose }: PostDialogProps) {
  if (!post) return null;

  return (
    <div className={styles.dialogBackdrop} role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className={styles.dialog} role="dialog" aria-modal="true" aria-labelledby="community-dialog-title">
        <header><div><small>Demo社区详情</small><h2 id="community-dialog-title">{post.title}</h2></div><button type="button" aria-label="关闭帖子详情" onClick={onClose}><X aria-hidden="true" /></button></header>
        <Image src={post.image} alt={`${post.pet}的Demo帖子配图`} width={1254} height={1254} />
        <div className={styles.dialogBody}><span>Demo虚拟内容</span><p>{post.body}</p><small>{post.author} · {post.pet}</small></div>
      </section>
    </div>
  );
}
