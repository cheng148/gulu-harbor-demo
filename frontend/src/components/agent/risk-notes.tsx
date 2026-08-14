export function RiskNotes({ risks, disclaimer }: Readonly<{ risks: readonly string[]; disclaimer: string }>) {
  return <aside className="risk-notes" aria-label="推荐说明"><strong>认识之前，也想提醒你</strong><ul>{risks.map((risk) => <li key={risk}>{risk}</li>)}</ul><p>{disclaimer}</p></aside>;
}
