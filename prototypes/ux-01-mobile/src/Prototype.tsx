import { useState, type CSSProperties } from "react";
import {
  ArrowLeftIcon, ArrowRightIcon, ChatBubbleIcon, CheckCircledIcon,
  ClockIcon, ExclamationTriangleIcon, HeartIcon, HomeIcon, MagnifyingGlassIcon, PersonIcon, ReloadIcon, ResetIcon
} from "@radix-ui/react-icons";
import { BottomSheet, KeyboardInput, KeyboardTextarea, MobileScroll, useKeyboard, useMobileDevice } from "./mobile";

type Screen = "home"|"market"|"chat"|"profile"|"allergy"|"results"|"edit"|"states"|"expired"|"error";
type AppTab = "home"|"pet"|"community"|"mine";
const questions = [
  ["普通工作日里，它大约会独处多久？","不用算得特别准，选最接近的一项就好。",["2小时以内","2～5小时","5～8小时","8小时以上"]],
  ["每天大概能留出多少时间陪它活动？","散步、玩耍和互动都可以算进去。",["半小时以内","半小时～1小时","1～2小时","2小时以上"]],
  ["你更喜欢哪种相处节奏？","凭第一感觉选，不需要懂宠物品种。",["安静陪在身边","时不时来贴贴","活泼互动多一点","都可以，看缘分"]],
  ["如果很喜欢，但生活节奏不太一样呢？","这是补充问题，只在答案可能改变推荐时出现。",["愿意为它调整一些","更希望它适应我","要看具体差距","暂时说不准"]],
] as const;
const titles:Record<Screen,string>={home:"",market:"首页",chat:"聊聊你的生活",profile:"相处画像",allergy:"最后确认",results:"推荐结果",edit:"修改条件",states:"原型状态",expired:"",error:""};
const pets=[
  ["/assets/gulu/pet-xiaomai.png","小麦","成年本地短毛猫","很合拍","互动温和，独处记录更贴近你的工作日。","换毛期仍要规律梳毛和清洁。"],
  ["/assets/gulu/pet-afu.png","阿福","成年本地混种犬","很合拍","亲人但不过分黏，也能自己安静一会儿。","每天仍需要稳定外出活动。"],
  ["/assets/gulu/pet-naigai.png","奶盖","布偶猫","值得认识","陪伴距离接近你的偏好。","长毛护理更多，掉毛接受度待确认。"],
  ["/assets/gulu/pet-tudou.png","土豆","柯基犬","需要磨合","你喜欢有回应的互动。","活动需求更高，要兑现调整时间的前提。"],
];

export default function Prototype(){
  const keyboard=useKeyboard();
  const {device}=useMobileDevice();
  const [screen,setScreen]=useState<Screen>("home");
  const [activeTab,setActiveTab]=useState<AppTab>("pet");
  const [history,setHistory]=useState<Screen[]>([]);
  const [step,setStep]=useState(0);
  const [draft,setDraft]=useState("");
  const [intake,setIntake]=useState("");
  const [answers,setAnswers]=useState<string[]>([]);
  const [questionOrder,setQuestionOrder]=useState<number[]>([]);
  const [allergy,setAllergy]=useState("");
  const [sheet,setSheet]=useState<"contact"|"reset"|"store"|null>(null);
  const [saved,setSaved]=useState(false);
  const [retried,setRetried]=useState(false);
  const [marketFilter,setMarketFilter]=useState("全部");
  const [marketQuery,setMarketQuery]=useState("");
  const go=(next:Screen)=>{keyboard.hide();setHistory(h=>[...h,screen]);setScreen(next)};
  const back=()=>{keyboard.hide();setHistory(h=>{const n=[...h];setScreen(n.pop()??"home");return n})};
  const resetConversation=()=>{keyboard.hide();setScreen("chat");setActiveTab("pet");setHistory([]);setStep(0);setDraft("");setIntake("");setAnswers([]);setQuestionOrder([]);setAllergy("");setSheet(null)};
  const selectTab=(tab:AppTab)=>{keyboard.hide();setActiveTab(tab);setScreen(tab==="home"?"market":tab==="pet"?"home":"states")};
  const beginQuestions=()=>{keyboard.hide();const value=draft.trim();if(!value)return;const order:number[]=/上班|独处|工作|时间/.test(value)?[2,1]:[0,2,1];if(/柯基|一定|非.*不可|特别喜欢/.test(value))order.push(3);setIntake(value);setQuestionOrder(order);setAnswers([]);setStep(0);setDraft("")};
  const answer=(value:string)=>{keyboard.hide();const next=[...answers,value];setAnswers(next);setDraft("");step>=questionOrder.length-1?go("allergy"):setStep(s=>s+1)};
  const previousQuestion=()=>{keyboard.hide();if(step===0){setIntake("");setQuestionOrder([]);setAnswers([]);setDraft("");return}setAnswers(a=>a.slice(0,-1));setStep(s=>s-1);setDraft("")};

  const Home=()=> <main className="home home-approved">
    <img className="approved-home-image" src="/assets/gulu/approved-ai-entry.png" alt="咕噜港AI选宠入口：聊一聊，遇见更合拍的它"/>
    <button className="approved-hotspot approved-start" aria-label="开始聊聊" onClick={()=>go("chat")}/>
    <nav className="approved-home-nav" aria-label="主导航">
      <button aria-label="首页" onClick={()=>selectTab("home")}/><button aria-label="选宠" onClick={()=>selectTab("pet")}/><button aria-label="社区" onClick={()=>selectTab("community")}/><button aria-label="我的" onClick={()=>selectTab("mine")}/>
    </nav>
  </main>;

  const Market=()=> {const visible=pets.filter(p=>marketFilter==="全部"||marketFilter==="猫猫"&&String(p[2]).includes("猫")||marketFilter==="狗狗"&&(String(p[2]).includes("犬")||String(p[2]).includes("狗")));return <main className="page market-home">
    <div className="virtual-banner"><ExclamationTriangleIcon/><span><b>Demo虚拟数据</b><small>销量、好评和店铺热度均为原型演示</small></span></div>
    <div className="market-search"><MagnifyingGlassIcon/><KeyboardInput value={marketQuery} onChange={e=>setMarketQuery(e.target.value)} placeholder="搜索宠物、品种或合作店铺"/></div>
    <section className="market-agent"><span><em>AI选宠顾问</em><h2>不知道选谁？<br/>先从你的生活聊起</h2><button onClick={()=>setScreen("home")}>去聊聊<ArrowRightIcon/></button></span><img src="/assets/gulu/harbor-hero.png" alt="猫狗与海港灯塔插画"/></section>
    <div className="market-cats">{["全部","猫猫","狗狗","合作店铺"].map(x=><button className={marketFilter===x?"on":""} key={x} onClick={()=>setMarketFilter(x)}>{x}</button>)}</div>
    {marketFilter!=="合作店铺"&&<><div className="market-title"><span><em>本期推荐</em><h3>最近值得认识的小家伙</h3></span><small>演示排序</small></div><div className="market-grid">{visible.filter(p=>!marketQuery||p.join("").includes(marketQuery)).map((p,i)=><article key={p[1]} className="market-pet"><img src={p[0]} alt={p[1]+"的模拟宠物档案插画"}/><section><i>Demo虚拟数据</i><h3>{p[1]}</h3><p>{p[2]}</p><div><span>模拟销量 {328-i*47}</span><span>模拟好评 {98-i}%</span></div><button onClick={()=>setSheet("store")}>看看档案</button></section></article>)}</div></>}
    {(marketFilter==="全部"||marketFilter==="合作店铺")&&<><div className="market-title"><span><em>合作店铺</em><h3>本期店铺推荐</h3></span><small>Demo模拟</small></div><div className="shop-list">{[["海风宠物生活馆","档案完整 · 近期上新","/assets/gulu/pet-xiaomai.png","模拟好评 98%"],["灯塔伙伴宠物屋","照护记录较完整","/assets/gulu/pet-afu.png","模拟好评 97%"]].map(s=><article key={s[0]}><img src={s[2]} alt={s[0]+"的模拟店铺封面"}/><span><i>Demo虚拟数据</i><h3>{s[0]}</h3><p>{s[1]} · {s[3]}</p></span><button onClick={()=>setSheet("store")}>进店看看</button></article>)}</div></>}
  </main>}

  const Chat=()=> {const q=questions[questionOrder[step]??0];return <main className="page chat-page">
    {!intake?<>
      <div className="chat-note">不用准备标准答案，想到什么就说什么</div>
      <div className="bubble chat-bubble"><b>咕</b><span><em>嗨，先认识一下你</em><h2>你希望遇见一位怎样的小伙伴？</h2><p>可以说喜欢猫还是狗、平时的生活节奏，或者只说一句“我还不太懂”也没关系。</p></span></div>
      <div className="suggestions"><button onClick={()=>setDraft("我想找一只安静一点、能陪在身边的猫")}>想找安静一点的猫</button><button onClick={()=>setDraft("我很喜欢亲人、愿意互动的狗")}>喜欢亲人的狗</button><button onClick={()=>setDraft("猫狗都可以，我还不太懂")}>猫狗都可以</button></div>
      <div className="write chat-write"><label>用自己的话和我说说</label><KeyboardTextarea value={draft} onChange={e=>setDraft(e.target.value)} placeholder="比如：白天要上班，晚上可以陪它玩一会儿……"/><button disabled={!draft.trim()} onClick={beginQuestions}>发送给咕噜</button></div>
    </>:<>
      <div className="chat-thread"><div className="user-bubble">{intake}</div>{questionOrder.slice(0,step).map((qi,i)=><div className="answered" key={qi+"-"+i}><div className="agent-line"><b>咕</b><span>{questions[qi][0]}</span></div><div className="user-bubble">{answers[i]}</div></div>)}</div>
      <div className="bubble chat-bubble"><b>咕</b><span><em>{questionOrder[step]===3?"还有一个可能影响结果的小地方":"我根据刚才的话，再了解一点"}</em><h2>{q[0]}</h2><p>{q[1]}</p></span></div>
      <div className="quick-label">可以直接点，也可以自己说</div><div className="suggestions answer-pills">{q[2].map(x=><button key={x} onClick={()=>answer(x)}>{x}</button>)}</div>
      <div className="write chat-write"><KeyboardTextarea value={draft} onChange={e=>setDraft(e.target.value)} placeholder="按自己的情况告诉我……"/><button disabled={!draft.trim()} onClick={()=>answer(draft.trim())}>发送这句话</button></div>
      <button className="previous-question" onClick={previousQuestion}><ArrowLeftIcon/>{step===0?"修改刚才的描述":"返回上一问"}</button>
      <button className="outline" onClick={()=>go("profile")}><CheckCircledIcon/>看看目前记住了什么<ArrowRightIcon/></button>
    </>}
  </main>};

  const Profile=()=> <main className="page profile-page"><section className="profile-hero"><div><em className="tag">你的相处画像</em><h2>我目前这样理解你</h2><p className="intro">这是聊天中的暂时整理，不是给你贴标签。你随时都能修改。</p></div><img src="/assets/gulu/user-profile-companion.png" alt="你的相处画像卡通形象"/></section><div className="profile">
    {[["独处时间","约5～8小时","已确认"],["陪伴投入","每天约1～2小时","已确认"],["互动节奏","喜欢适度贴贴","已确认"],["陪伴距离","希望亲近，也保留空间","已确认"],["活动与外出","还没有聊到","待确认"],["日常照护","可以接受基础照护","已确认"],["清洁与掉毛","还没有聊到","待确认"],["愿意调整","可以调整一些","已确认"]].map(r=><div key={r[0]}><span><small>{r[0]}</small><strong>{r[1]}</strong></span><i className={r[2]==="待确认"?"pending":""}>{r[2]}</i></div>)}
    </div><p className="tip"><b>“待确认”是什么？</b>只是可能影响结果、但你还没说过的信息，不代表回答错了。</p></main>;

  const Allergy=()=> <main className="page confirm"><div className="badge"><ExclamationTriangleIcon/></div><em className="tag">推荐前的最后确认</em><h2>你本人对猫或狗有明确过敏吗？</h2><p className="intro">只按猫、狗两个物种处理，不会承诺某个品种“绝对低敏”。</p><div className="choices">{["都没有","对猫过敏","对狗过敏","还不确定"].map(x=><button className={allergy===x?"selected":""} key={x} onClick={()=>setAllergy(x)}>{x}{allergy===x&&<CheckCircledIcon/>}</button>)}</div><button className="primary" disabled={!allergy} onClick={()=>go("results")}>看看推荐结果<ArrowRightIcon/></button><small className="demo">只用于这次判断，不需要填写医疗记录。</small></main>;

  const Results=()=> <main className="page results"><em className="tag">这次的相遇名单</em><h2>先认识这4位小家伙</h2><p className="intro">等级先判断，再在同等级里排序；页面不会展示内部数字分。</p>{pets.map((p,i)=><article className="pet" key={p[1]}><div className="rank">{i<2?"优先看看":"再认识一下"} · {i+1}</div><img src={p[0]} alt={p[1]+"的模拟宠物档案插画"}/><section><header><span><small>{p[2]}</small><h3>{p[1]}</h3></span><i>{p[3]}</i></header><p><b>合拍点</b>{p[4]}</p><p><b>要接受的小代价</b>{p[5]}</p><small className="merchant">模拟合作商家 · Demo模拟在售</small><button onClick={()=>setSheet("contact")}>进一步了解这只小家伙</button></section></article>)}<button className="secondary" onClick={()=>go("edit")}><ReloadIcon/>修改条件再看看</button><button className="text" onClick={()=>go("profile")}>查看我的相处画像</button><p className="disclaimer">咕噜港负责匹配和连接，不直接销售，也不对宠物健康和性格作绝对保证。</p></main>;

  const Edit=()=> <main className="page"><em className="tag">换个条件再看看</em><h2>想调整哪一项？</h2><p className="intro">原来的答案会保留，只改你选择的这一项。</p>{[["独处时间","约5～8小时"],["每天陪伴","约1～2小时"],["互动节奏","喜欢适度贴贴"],["愿意调整","可以调整一些"],["过敏情况","都没有"]].map(r=><button className="row" key={r[0]}><span><small>{r[0]}</small><strong>{r[1]}</strong></span><ArrowRightIcon/></button>)}<button className="primary spaced" onClick={()=>setSaved(true)}>保存并重新推荐</button>{saved&&<div className="success"><CheckCircledIcon/><span><b>已经更新好啦</b><small>原型会带着新条件重新整理结果。</small><button onClick={()=>setScreen("results")}>查看新结果</button></span></div>}</main>;

  const States=()=> <main className="page"><em className="tag">原型状态体验</em><h2>出错时也不会让你迷路</h2><p className="intro">点开看看过期、重试和主动重置的提示。</p><button className="state" onClick={()=>go("expired")}><ExclamationTriangleIcon/><span><b>会话已过期</b><small>24小时没有活动后的提示</small></span><ArrowRightIcon/></button><button className="state" onClick={()=>go("error")}><ReloadIcon/><span><b>暂时没连上</b><small>失败时保留旧内容</small></span><ArrowRightIcon/></button><button className="state" onClick={()=>setSheet("reset")}><ResetIcon/><span><b>主动重置</b><small>清空本次画像重新开始</small></span><ArrowRightIcon/></button></main>;

  const Empty=({expired}:{expired:boolean})=> <main className="page empty"><div className="badge">{expired?<ResetIcon/>:<ExclamationTriangleIcon/>}</div><h2>{expired?"这次聊天已经靠岸啦":retried?"已经重新连上啦":"刚刚有点走神"}</h2><p>{expired?"超过24小时没有活动，我们不会拿旧信息继续推荐。":retried?"之前的回答都还在，可以安心继续。":"这次没有生成新推荐，之前的内容都替你保留着。"}</p><button className="primary" onClick={()=>expired?resetConversation():retried?setScreen("results"):setRetried(true)}>{expired?"开始一次新聊天":retried?"回到推荐结果":"再试一次"}</button><button className="text" onClick={back}>先返回</button></main>;

  const chatTitle=!intake?"先认识一下你":questionOrder[step]===3?"确认一个小偏好":"了解你的日常";
  const AppNav=()=> <nav className="nav" aria-label="主导航"><button className={activeTab==="home"?"on":""} onClick={()=>selectTab("home")}><HomeIcon/><small>首页</small></button><button className={activeTab==="pet"?"on":""} onClick={()=>selectTab("pet")}><ChatBubbleIcon/><small>选宠</small></button><button className={activeTab==="community"?"on":""} onClick={()=>selectTab("community")}><HeartIcon/><small>社区</small></button><button className={activeTab==="mine"?"on":""} onClick={()=>selectTab("mine")}><PersonIcon/><small>我的</small></button></nav>;
  const screens:Record<Screen,()=>React.ReactNode>={home:Home,market:Market,chat:Chat,profile:Profile,allergy:Allergy,results:Results,edit:Edit,states:States,expired:()=> <Empty expired/>,error:()=> <Empty expired={false}/>};
  const Current=screens[screen];
  return <div className="gulu-shell" style={{"--gulu-status-height":device.platform==="ios"?"54px":"72px","--gulu-safe-area":device.platform==="ios"?device.geometry.safeArea.bottom+"px":"0px"} as CSSProperties}>
    {screen==="chat"&&<header className="apphead chat-fixed-head" data-testid="chat-fixed-header"><button aria-label="返回" onClick={back}><ArrowLeftIcon/></button><strong data-testid="chat-stage-title">{chatTitle}</strong><button className="head-reset" onClick={()=>setSheet("reset")}>重新开始</button></header>}
    {screen!=="home"&&screen!=="chat"&&screen!=="expired"&&screen!=="error"&&<header className="apphead"><button aria-label="返回" onClick={back}><ArrowLeftIcon/></button><strong>{titles[screen]}</strong><span/></header>}
    <MobileScroll key={screen} className="paper"><Current/></MobileScroll>
    {!['home','profile','allergy','edit','expired','error'].includes(screen)&&<AppNav/>}
    <BottomSheet open={sheet==="contact"} onOpenChange={v=>!v&&setSheet(null)} title="联系商家进一步了解" description="当前只是原型演示入口。"><div className="sheet"><p>Demo演示功能，暂未开放。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="store"} onOpenChange={v=>!v&&setSheet(null)} title="模拟宠物与店铺详情" description="这里展示的是Demo虚拟数据，不代表真实在售、销量或好评。"><div className="sheet"><p>详情页会在后续原型中继续补充。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="reset"} onOpenChange={v=>!v&&setSheet(null)} title="要重新认识一次吗？" description="重置后，之前的回答和推荐不会带到新会话。"><div className="sheet"><button className="danger" onClick={resetConversation}>确认重置</button><button onClick={()=>setSheet(null)}>先不重置</button></div></BottomSheet>
  </div>
}
