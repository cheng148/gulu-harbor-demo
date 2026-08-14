export function ExpiredDialog({ onStartNew }: Readonly<{ onStartNew: () => void }>) {
  return (
    <main className="agent-state expired-state" role="alert">
      <span className="gulu-avatar" aria-hidden="true">咕</span>
      <h1>这次聊天已经靠岸啦</h1>
      <p>超过24小时没有活动，我们不会拿旧信息继续推荐。</p>
      <button type="button" onClick={onStartNew}>开始一次新聊天</button>
    </main>
  );
}
