export function ErrorFeedback({ message, onRetry }: Readonly<{ message: string; onRetry: () => void }>) {
  return (
    <div className="session-error" role="alert">
      <strong>刚刚没有更新成功</strong>
      <p>{message}</p>
      <span>之前的推荐和填写内容都还在。</span>
      <button type="button" onClick={onRetry}>再试一次</button>
    </div>
  );
}
