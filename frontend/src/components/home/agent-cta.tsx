import Image from "next/image";
import Link from "next/link";

export function AgentCta() {
  return (
    <section className="agent-cta" aria-labelledby="agent-cta-title">
      <div className="agent-cta__copy">
        <p className="agent-cta__eyebrow">AI选宠顾问</p>
        <h2 id="agent-cta-title">不知道选谁？先从你的生活聊起</h2>
        <Link className="agent-cta__link" href="/agent">
          去聊聊
          <span aria-hidden="true">→</span>
        </Link>
      </div>
      <Image
        className="agent-cta__art"
        src="/assets/gulu/harbor-hero.png"
        alt="港湾边的猫咪、狗狗和灯塔插画"
        width={1122}
        height={1402}
        priority
      />
    </section>
  );
}
