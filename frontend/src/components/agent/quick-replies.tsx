type QuickRepliesProps = Readonly<{
  options: readonly string[];
  disabled?: boolean;
  onSelect: (option: string) => void;
}>;

export function QuickReplies({ options, disabled = false, onSelect }: QuickRepliesProps) {
  if (options.length === 0) return null;
  return <div className="answer-pills" aria-label="快捷回答">{options.map((option) => <button key={option} type="button" disabled={disabled} onClick={() => onSelect(option)}>{option}</button>)}</div>;
}
