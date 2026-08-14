import { useState, type CSSProperties } from "react";
import {
  ArrowLeftIcon, ArrowRightIcon, CheckCircledIcon,
  ClockIcon, ExclamationTriangleIcon, HeartIcon, HomeIcon, MagnifyingGlassIcon, PersonIcon, ReloadIcon, ResetIcon
} from "@radix-ui/react-icons";
import { Bone, Bookmark, BriefcaseMedical, ChevronRight, Crown, FileText, Heart, MessageCircle, PawPrint, Plus, ShoppingBag, Sparkles, Store, UserRound, UtensilsCrossed } from "lucide-react";
import { BottomSheet, KeyboardInput, KeyboardTextarea, MobileScroll, useKeyboard, useMobileDevice } from "./mobile";
import "./readability.css";

type Screen = "home"|"market"|"petMarket"|"supplies"|"community"|"me"|"membership"|"chat"|"profile"|"allergy"|"results"|"edit"|"states"|"expired"|"error";
type AppTab = "home"|"pet"|"community"|"mine";
const questions = [
  ["普通工作日里，它大约会独处多久？","不用算得特别准，选最接近的一项就好。",["2小时以内","2～5小时","5～8小时","8小时以上"]],
  ["每天大概能留出多少时间陪它活动？","散步、玩耍和互动都可以算进去。",["半小时以内","半小时～1小时","1～2小时","2小时以上"]],
  ["你更喜欢哪种相处节奏？","凭第一感觉选，不需要懂宠物品种。",["安静陪在身边","时不时来贴贴","活泼互动多一点","都可以，看缘分"]],
  ["如果很喜欢，但生活节奏不太一样呢？","这是补充问题，只在答案可能改变推荐时出现。",["愿意为它调整一些","更希望它适应我","要看具体差距","暂时说不准"]],
] as const;
const titles:Record<Screen,string>={home:"",market:"首页",petMarket:"宠物市场",supplies:"宠物用品",community:"社区",me:"我的",membership:"会员中心",chat:"聊聊你的生活",profile:"相处画像",allergy:"最后确认",results:"推荐结果",edit:"修改条件",states:"原型状态",expired:"",error:""};
const pets=[
  ["/assets/gulu/pet-xiaomai.png","小麦","成年本地短毛猫","很合拍","互动温和，独处记录更贴近你的工作日。","换毛期仍要规律梳毛和清洁。"],
  ["/assets/gulu/pet-afu.png","阿福","成年本地混种犬","很合拍","亲人但不过分黏，也能自己安静一会儿。","每天仍需要稳定外出活动。"],
  ["/assets/gulu/pet-naigai.png","奶盖","布偶猫","值得认识","陪伴距离接近你的偏好。","长毛护理更多，掉毛接受度待确认。"],
  ["/assets/gulu/pet-tudou.png","土豆","柯基犬","需要磨合","你喜欢有回应的互动。","活动需求更高，要兑现调整时间的前提。"],
];
const marketCategories=[
  {id:"ragdoll",name:"布偶猫",kind:"猫猫",image:"/assets/gulu/pet-naigai.png",sold:234,praise:96,available:12},
  {id:"british-shorthair",name:"英国短毛猫",kind:"猫猫",image:"/assets/gulu/pet-xiaomai.png",sold:198,praise:95,available:9},
  {id:"corgi",name:"柯基犬",kind:"狗狗",image:"/assets/gulu/pet-tudou.png",sold:176,praise:94,available:8},
  {id:"labrador",name:"拉布拉多犬",kind:"狗狗",image:"/assets/gulu/pet-afu.png",sold:151,praise:97,available:6},
];
const marketPets=[
  {id:"naigai",categoryId:"ragdoll",image:"/assets/gulu/pet-naigai.png",name:"奶盖",kind:"猫猫",breed:"布偶猫",age:"1岁",size:"中等体型",merchant:"海风宠物生活馆",note:"温和黏人，需要耐心梳毛",views:968},
  {id:"yunduo",categoryId:"ragdoll",image:"/assets/gulu/pet-naigai.png",name:"云朵",kind:"猫猫",breed:"布偶猫",age:"10个月",size:"中等体型",merchant:"灯塔伙伴宠物屋",note:"喜欢安静观察，也愿意靠近熟悉的人",views:742},
  {id:"xiaomai",categoryId:"british-shorthair",image:"/assets/gulu/pet-xiaomai.png",name:"小麦",kind:"猫猫",breed:"英国短毛猫",age:"2岁",size:"中等体型",merchant:"海风宠物生活馆",note:"安静亲人，喜欢在身边陪着",views:1234},
  {id:"zhima",categoryId:"british-shorthair",image:"/assets/gulu/pet-xiaomai.png",name:"芝麻",kind:"猫猫",breed:"英国短毛猫",age:"1岁半",size:"中等体型",merchant:"灯塔伙伴宠物屋",note:"独处时比较安稳，熟悉后会主动互动",views:689},
  {id:"tudou",categoryId:"corgi",image:"/assets/gulu/pet-tudou.png",name:"土豆",kind:"狗狗",breed:"柯基犬",age:"2岁",size:"小型犬",merchant:"灯塔伙伴宠物屋",note:"活泼好动，喜欢一起出门",views:821},
  {id:"lizi",categoryId:"corgi",image:"/assets/gulu/pet-tudou.png",name:"栗子",kind:"狗狗",breed:"柯基犬",age:"1岁",size:"小型犬",merchant:"海风宠物生活馆",note:"对玩具很有兴趣，需要规律活动",views:653},
  {id:"afu",categoryId:"labrador",image:"/assets/gulu/pet-afu.png",name:"阿福",kind:"狗狗",breed:"拉布拉多犬",age:"3岁",size:"大型犬",merchant:"灯塔伙伴宠物屋",note:"热情开朗，期待稳定的陪伴",views:1098},
  {id:"kele",categoryId:"labrador",image:"/assets/gulu/pet-afu.png",name:"可乐",kind:"狗狗",breed:"拉布拉多犬",age:"2岁",size:"大型犬",merchant:"海风宠物生活馆",note:"亲人爱互动，需要充足的活动时间",views:777},
];
const supplyItems=[
  {id:"food",name:"海港鲜肉主食包",category:"日常吃喝",note:"猫狗分款的模拟日常主食",sold:328,praise:97,Icon:UtensilsCrossed},
  {id:"toys",name:"灯塔耐咬互动球",category:"玩具互动",note:"适合一起玩耍的模拟用品",sold:246,praise:96,Icon:Bone},
  {id:"care",name:"温和免洗清洁手套",category:"清洁护理",note:"外出回家后的模拟清洁用品",sold:219,praise:98,Icon:Sparkles},
  {id:"travel",name:"轻便透气外出包",category:"安心出行",note:"短途出行使用的模拟便携包",sold:174,praise:95,Icon:BriefcaseMedical},
];
const communityPosts=[
  {id:"xiaomai-30",author:"海风慢慢",avatar:"海",time:"今天 09:20",title:"小麦来到家的第30天",summary:"从躲在沙发后面，到会在我下班时跑来迎接。慢一点认识彼此，好像真的有用。",body:"刚到家时总躲在沙发后面，我没有急着抱它，只把水、食物和猫砂放在安静的位置。现在第30天，它会在我下班时跑来迎接，也愿意靠在旁边睡觉。",image:"/assets/gulu/pet-xiaomai.png",likes:128,comments:19},
  {id:"rain-sniff",author:"阿福的周末",avatar:"福",time:"昨天 18:42",title:"雨天也能玩的嗅闻小游戏",summary:"把零食藏在旧毛巾的小褶皱里，阿福找了十分钟，回家后的精力终于有地方用了。",body:"雨天没法走太久，我把几颗零食藏在旧毛巾的褶皱里，让阿福慢慢闻着找。全程有人看着，没有让它撕咬吞下毛巾。十分钟后，它满足地趴下休息了。",image:"/assets/gulu/pet-afu.png",likes:96,comments:12},
  {id:"naigai-brush",author:"奶盖观察员",avatar:"奶",time:"周一 21:05",title:"奶盖的梳毛小记录",summary:"每天只梳几分钟，比周末一次梳很久轻松。长毛护理不浪漫，但慢慢形成习惯也挺治愈。",body:"以前总想周末一次梳完，奶盖很快就不耐烦。最近改成每天几分钟，先从背部开始，状态不好就停。长毛护理确实要花时间，但我们都轻松多了。",image:"/assets/gulu/pet-naigai.png",likes:84,comments:8},
];

export default function Prototype(){
  const keyboard=useKeyboard();
  const {device}=useMobileDevice();
  const [screen,setScreen]=useState<Screen>("market");
  const [activeTab,setActiveTab]=useState<AppTab>("home");
  const [history,setHistory]=useState<Screen[]>([]);
  const [step,setStep]=useState(0);
  const [draft,setDraft]=useState("");
  const [intake,setIntake]=useState("");
  const [answers,setAnswers]=useState<string[]>([]);
  const [questionOrder,setQuestionOrder]=useState<number[]>([]);
  const [allergy,setAllergy]=useState("");
  const [sheet,setSheet]=useState<"contact"|"reset"|"store"|"checkout"|"communityPost"|"publish"|"membershipOpen"|"accountAction"|null>(null);
  const [saved,setSaved]=useState(false);
  const [retried,setRetried]=useState(false);
  const [marketFilter,setMarketFilter]=useState("全部");
  const [marketQuery,setMarketQuery]=useState("");
  const [petMarketFilter,setPetMarketFilter]=useState("全部");
  const [petMarketQuery,setPetMarketQuery]=useState("");
  const [selectedMarketCategory,setSelectedMarketCategory]=useState<string|null>(null);
  const [favorites,setFavorites]=useState<string[]>(()=>JSON.parse(localStorage.getItem("gulu-demo-favorites")??"[]"));
  const [supplyFilter,setSupplyFilter]=useState("全部用品");
  const [cart,setCart]=useState<Record<string,number>>(()=>JSON.parse(localStorage.getItem("gulu-demo-cart")??"{}"));
  const [cartFeedback,setCartFeedback]=useState<number|null>(null);
  const [communityLikes,setCommunityLikes]=useState<string[]>(()=>JSON.parse(localStorage.getItem("gulu-demo-community-likes")??"[]"));
  const [communityFavorites,setCommunityFavorites]=useState<string[]>(()=>JSON.parse(localStorage.getItem("gulu-demo-community-favorites")??"[]"));
  const [selectedCommunityPost,setSelectedCommunityPost]=useState<string|null>(null);
  const [demoMembership,setDemoMembership]=useState(()=>localStorage.getItem("gulu-demo-membership")==="true");
  const [membershipPlan,setMembershipPlan]=useState<"月度会员"|"年度会员">("月度会员");
  const [accountSubject,setAccountSubject]=useState("真实账户功能");
  const go=(next:Screen)=>{keyboard.hide();setHistory(h=>[...h,screen]);setScreen(next)};
  const back=()=>{keyboard.hide();setHistory(h=>{const n=[...h];setScreen(n.pop()??"home");return n})};
  const resetConversation=()=>{keyboard.hide();setScreen("chat");setActiveTab("pet");setHistory([]);setStep(0);setDraft("");setIntake("");setAnswers([]);setQuestionOrder([]);setAllergy("");setSheet(null)};
  const selectTab=(tab:AppTab)=>{keyboard.hide();setActiveTab(tab);setScreen(tab==="home"?"market":tab==="pet"?"home":tab==="community"?"community":"me")};
  const beginQuestions=()=>{keyboard.hide();const value=draft.trim();if(!value)return;const order:number[]=/上班|独处|工作|时间/.test(value)?[2,1]:[0,2,1];if(/柯基|一定|非.*不可|特别喜欢/.test(value))order.push(3);setIntake(value);setQuestionOrder(order);setAnswers([]);setStep(0);setDraft("")};
  const answer=(value:string)=>{keyboard.hide();const next=[...answers,value];setAnswers(next);setDraft("");step>=questionOrder.length-1?go("allergy"):setStep(s=>s+1)};
  const previousQuestion=()=>{keyboard.hide();if(step===0){setIntake("");setQuestionOrder([]);setAnswers([]);setDraft("");return}setAnswers(a=>a.slice(0,-1));setStep(s=>s-1);setDraft("")};

  const Home=()=> <main className="home home-approved">
    <img className="approved-home-image" src="/assets/gulu/approved-ai-entry.png" alt="咕噜港AI选宠入口：聊一聊，遇见更合拍的它"/>
    <button className="approved-hotspot approved-start" aria-label="开始聊聊" onClick={()=>go("chat")}/>
  </main>;

  const Market=()=> {const visible=pets.filter(p=>marketFilter==="全部"||marketFilter==="猫猫"&&String(p[2]).includes("猫")||marketFilter==="狗狗"&&(String(p[2]).includes("犬")||String(p[2]).includes("狗")));return <main className="page market-home">
    <div className="virtual-banner"><ExclamationTriangleIcon/><span><b>Demo虚拟数据</b><small>销量、好评和店铺热度均为原型演示</small></span></div>
    <div className="market-search"><MagnifyingGlassIcon/><KeyboardInput value={marketQuery} onChange={e=>setMarketQuery(e.target.value)} placeholder="搜索宠物、品种或合作店铺"/></div>
    <section className="market-agent"><span><em>AI选宠顾问</em><h2>不知道选谁？<br/>先从你的生活聊起</h2><button onClick={()=>selectTab("pet")}>去聊聊<ArrowRightIcon/></button></span><img src="/assets/gulu/harbor-hero.png" alt="猫狗与海港灯塔插画"/></section>
    <nav className="market-entries" aria-label="逛逛咕噜港"><button aria-label="逛宠物市场" onClick={()=>go("petMarket")}><Store/><span><b>宠物市场</b><small>看看具体的小伙伴</small></span><ArrowRightIcon/></button><button aria-label="看看宠物用品" onClick={()=>go("supplies")}><ShoppingBag/><span><b>宠物用品</b><small>准备相处的小物件</small></span><ArrowRightIcon/></button></nav>
    <div className="market-cats">{["全部","猫猫","狗狗","合作店铺"].map(x=><button className={marketFilter===x?"on":""} key={x} onClick={()=>setMarketFilter(x)}>{x}</button>)}</div>
    {marketFilter!=="合作店铺"&&<><div className="market-title"><span><em>近期人气榜</em><h3>最近常被看见的小家伙</h3></span><small>近7天模拟热度</small></div><div className="market-grid">{visible.filter(p=>!marketQuery||p.join("").includes(marketQuery)).map((p,i)=><article key={p[1]} className="market-pet"><img src={p[0]} alt={p[1]+"的模拟宠物档案插画"}/><section><i>Demo虚拟数据</i><h3>{p[1]}</h3><p>{p[2]}</p><div><span>近7天浏览 {1234-i*137} 次</span><span>{86-i*9} 人想进一步了解</span></div><button onClick={()=>setSheet("store")}>看看档案</button></section></article>)}</div></>}
    {marketFilter!=="合作店铺"&&<><div className="market-title"><span><em>商家交易汇总</em><h3>本期热门品种</h3></span><small>近30天模拟数据</small></div><div className="breed-hot-list">{marketCategories.filter(category=>marketFilter==="全部"||category.kind===marketFilter).map(category=><article key={category.id}><img src={category.image} alt={category.name+"品种示意照片"}/><section><i>Demo虚拟数据</i><h3>{category.name}</h3><span>近30天模拟成交 {category.sold}</span><span>相关交易好评率 {category.praise}%</span><span>当前模拟在售 {category.available} 只</span></section></article>)}</div></>}
    {(marketFilter==="全部"||marketFilter==="合作店铺")&&<><div className="market-title"><span><em>合作店铺</em><h3>本期店铺推荐</h3></span><small>Demo模拟</small></div><div className="shop-list">{[["海风宠物生活馆","档案完整 · 近期上新","/assets/gulu/pet-xiaomai.png","模拟好评 98%"],["灯塔伙伴宠物屋","照护记录较完整","/assets/gulu/pet-afu.png","模拟好评 97%"]].map(s=><article key={s[0]}><img src={s[2]} alt={s[0]+"的模拟店铺封面"}/><span><i>Demo虚拟数据</i><h3>{s[0]}</h3><p>{s[1]} · {s[3]}</p></span><button onClick={()=>setSheet("store")}>进店看看</button></article>)}</div></>}
  </main>}

  const PetMarket=()=> {
    const categories=marketCategories.filter(category=>(petMarketFilter==="全部"||category.kind===petMarketFilter)&&(!petMarketQuery||category.name.includes(petMarketQuery)));
    const selected=marketCategories.find(category=>category.id===selectedMarketCategory);
    const visible=selectedMarketCategory?marketPets.filter(p=>p.categoryId===selectedMarketCategory):[];
    const toggleFavorite=(id:string)=>setFavorites(current=>{const next=current.includes(id)?current.filter(item=>item!==id):[...current,id];localStorage.setItem("gulu-demo-favorites",JSON.stringify(next));return next});
    return <main className="page prototype-page"><em className="tag">模拟合作商家档案</em><h2>宠物市场</h2><p className="intro">先选品种方向，再认识该品种下的具体小伙伴和所在商家。</p>
      {selected?<><button className="category-back" onClick={()=>setSelectedMarketCategory(null)}><ArrowLeftIcon/>返回品种列表</button><div className="market-title category-detail-title"><span><em>Demo虚拟档案</em><h3>{selected.name}的小伙伴</h3></span><small>当前2只</small></div><div className="prototype-grid">{visible.map(p=>{const favorite=favorites.includes(p.id);return <article className="prototype-pet" aria-label={`${p.name}宠物档案`} key={p.id}><div><img src={p.image} alt={`${p.name}的模拟档案照片`}/><i>Demo虚拟档案</i></div><section><header><span><h3>{p.name}</h3><small>{p.breed}</small></span><button aria-label={`${favorite?"取消收藏":"收藏"}${p.name}`} className={favorite?"on":""} onClick={()=>toggleFavorite(p.id)}><Heart fill={favorite?"currentColor":"none"}/></button></header><p>{p.note}</p><dl><div><dt>年龄</dt><dd>{p.age}</dd></div><div><dt>体型</dt><dd>{p.size}</dd></div></dl><small>所在商家 · {p.merchant}</small><b>近7天浏览 {p.views.toLocaleString("zh-CN")} 次</b></section></article>})}</div></>:<><div className="market-search"><MagnifyingGlassIcon/><KeyboardInput value={petMarketQuery} onChange={event=>setPetMarketQuery(event.target.value)} placeholder="搜索品种"/></div><div className="prototype-filters">{[["全部","全部"],["猫猫","只看猫猫"],["狗狗","只看狗狗"]].map(([value,label])=><button className={petMarketFilter===value?"on":""} key={value} onClick={()=>setPetMarketFilter(value)}>{label}</button>)}</div><div className="prototype-grid">{categories.map(category=><article className="prototype-category" aria-label={`${category.name}品种`} key={category.id}><div><img src={category.image} alt={`${category.name}品种示意照片`}/><i>Demo虚拟数据</i></div><section><small>{category.kind}方向</small><h3>{category.name}</h3><span>近30天模拟成交 {category.sold}</span><span>当前模拟在售 {category.available} 只</span><button aria-label={`查看${category.name}的模拟在售宠物`} onClick={()=>setSelectedMarketCategory(category.id)}>看看2位小伙伴</button></section></article>)}</div>{!categories.length&&<p className="prototype-empty">暂时没找到这个品种方向，换个关键词看看吧。</p>}</>}
    </main>;
  };

  const Supplies=()=> {
    const visible=supplyItems.filter(item=>supplyFilter==="全部用品"||item.category===supplyFilter);
    const count=Object.values(cart).reduce((sum,quantity)=>sum+quantity,0);
    const add=(id:string)=>setCart(current=>{const next={...current,[id]:(current[id]??0)+1};const nextCount=Object.values(next).reduce((sum,quantity)=>sum+quantity,0);setCartFeedback(nextCount);localStorage.setItem("gulu-demo-cart",JSON.stringify(next));return next});
    return <main className="page prototype-page"><em className="tag">模拟用品橱窗</em><h2>宠物用品</h2><p className="intro">用品可以放进本地模拟购物车体验；销量和好评率都是Demo虚拟数据。</p>
      <div className="prototype-filters supplies-filter">{["全部用品","日常吃喝","玩具互动","清洁护理","安心出行"].map(value=><button className={supplyFilter===value?"on":""} key={value} onClick={()=>setSupplyFilter(value)}>{value}</button>)}</div>
      <div className="prototype-grid">{visible.map(item=>{const Icon=item.Icon;return <article className="prototype-supply" key={item.id}><div className={`supply-art ${item.id}`}><Icon/><i>Demo虚拟商品</i></div><section><small>{item.category}</small><h3>{item.name}</h3><p>{item.note}</p><div><span>模拟销量 {item.sold}</span><span>模拟好评 {item.praise}%</span></div><button aria-label={`把${item.name}加入模拟购物车`} onClick={()=>add(item.id)}>加入模拟购物车</button></section></article>})}</div>
      {count>0&&<div className="demo-cart-status" data-testid="fixed-cart-bar"><ShoppingBag/><span role="status" aria-label="加入购物车反馈">{cartFeedback===null?`本机模拟购物车共有 ${count} 件用品`:`已加入模拟购物车，本机共有 ${cartFeedback} 件用品`}</span><button onClick={()=>setSheet("checkout")}>模拟结算</button></div>}
    </main>;
  };

  const Community=()=> {
    const toggle=(storageKey:string,id:string,current:string[],update:(next:string[])=>void)=>{const next=current.includes(id)?current.filter(item=>item!==id):[...current,id];localStorage.setItem(storageKey,JSON.stringify(next));update(next)};
    return <main className="page community-page">
      <section className="community-intro"><span><em>Demo社区</em><h2>社区</h2><p>看看大家与小伙伴慢慢熟悉的日常。帖子和互动数字均为虚拟演示数据。</p></span><button aria-label="发布动态" onClick={()=>setSheet("publish")}><Plus/>发布动态</button></section>
      <div className="community-feed">{communityPosts.map(post=>{const liked=communityLikes.includes(post.id);const favorite=communityFavorites.includes(post.id);return <article className="community-card" key={post.id}>
        <header><b>{post.avatar}</b><span><strong>{post.author}</strong><small>{post.time} · Demo虚拟帖子</small></span></header>
        <button className="community-open" aria-label={`查看${post.title}详情`} onClick={()=>{setSelectedCommunityPost(post.id);setSheet("communityPost")}}><img src={post.image} alt={`${post.title}的宠物日常插画`}/><span><h3>{post.title}</h3><p>{post.summary}</p></span></button>
        <footer><button className={liked?"on":""} aria-label={`${liked?"取消点赞":"点赞"}${post.title}`} onClick={()=>toggle("gulu-demo-community-likes",post.id,communityLikes,setCommunityLikes)}><Heart fill={liked?"currentColor":"none"}/>{post.likes+(liked?1:0)}</button><span><MessageCircle/>{post.comments}</span><button className={favorite?"on":""} aria-label={`${favorite?"取消收藏":"收藏"}${post.title}`} onClick={()=>toggle("gulu-demo-community-favorites",post.id,communityFavorites,setCommunityFavorites)}><Bookmark fill={favorite?"currentColor":"none"}/>{favorite?"已收藏":"收藏"}</button></footer>
      </article>})}</div>
    </main>;
  };

  const Me=()=> {
    const cartCount=Object.values(cart).reduce((sum,quantity)=>sum+quantity,0);
    const favoriteCount=favorites.length+communityFavorites.length;
    const unavailable=(subject:string)=>{setAccountSubject(subject);setSheet("accountAction")};
    return <main className="page account-page">
      <section className="account-hero"><b>咕</b><span><em>无账户Demo体验</em><h2>我的港湾</h2><p>这里只整理保存在本机的原型互动，不代表真实账户资料。</p></span></section>
      <div className="account-stats"><div aria-label="本机收藏数量"><strong>{favoriteCount}</strong><span>本机收藏</span></div><div aria-label="本机点赞数量"><strong>{communityLikes.length}</strong><span>社区点赞</span></div><div aria-label="模拟购物车数量"><strong>{cartCount}</strong><span>模拟购物车</span></div></div>
      <nav className="account-menu" aria-label="我的功能"><button aria-label="进入会员中心" onClick={()=>go("membership")}><Crown/><span><b>会员中心</b><small>{demoMembership?"当前为会员展示状态":"查看普通与会员展示状态"}</small></span><ChevronRight/></button><button aria-label="我的收藏" onClick={()=>unavailable("跨页面收藏整理")}><Bookmark/><span><b>我的收藏</b><small>当前仅展示上方本机数量</small></span><ChevronRight/></button><button aria-label="真实订单" onClick={()=>unavailable("真实账户订单")}><FileText/><span><b>我的订单</b><small>Demo不创建真实订单</small></span><ChevronRight/></button><button aria-label="账户资料" onClick={()=>unavailable("真实账户资料")}><UserRound/><span><b>账户资料</b><small>首版不建设登录和账户系统</small></span><ChevronRight/></button></nav>
      <p className="account-local-note">收藏、点赞和购物车仅保存在这台设备的浏览器中；清理浏览器数据后会消失。</p>
    </main>;
  };

  const Membership=()=> {
    const preview=(enabled:boolean)=>{setDemoMembership(enabled);localStorage.setItem("gulu-demo-membership",String(enabled))};
    return <main className="page account-page membership-page">
      <section className={`membership-state ${demoMembership?"member":""}`}><span><Crown/></span><div><em>仅供页面预览</em><h2>{demoMembership?"当前为会员展示状态":"当前为普通展示状态"}</h2><p>仅改变本机Demo页面，不代表已经注册、付费或开通会员。</p></div><nav><button aria-pressed={!demoMembership} onClick={()=>preview(false)}>预览普通状态</button><button aria-pressed={demoMembership} onClick={()=>preview(true)}>预览会员状态</button></nav></section>
      <section className="membership-copy"><em>模拟套餐选择</em><h2>先看看页面怎样呈现</h2><p>第一版尚未确认价格和正式权益，因此这里只演示套餐选择与开通边界。</p></section>
      <div className="membership-plans">{(["月度会员","年度会员"] as const).map(plan=><button aria-label={`选择${plan}`} aria-pressed={membershipPlan===plan} onClick={()=>setMembershipPlan(plan)} key={plan}><strong>{plan}</strong><span>不展示价格，不代表真实可购买套餐。</span></button>)}</div>
      <button className="membership-open" aria-label={`确认开通${membershipPlan}`} onClick={()=>setSheet("membershipOpen")}>确认开通{membershipPlan}</button>
      <p className="membership-boundary">价格、权益、续费和退款规则仍待产品确认。本页不会创建订单、会员身份或任何费用。</p>
    </main>;
  };

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
    <button className="chat-reset-action" onClick={()=>setSheet("reset")}>重新开始</button>
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
  const AppNav=()=> <nav className="nav" aria-label="主导航"><button className={activeTab==="home"?"on":""} onClick={()=>selectTab("home")}><HomeIcon/><small>首页</small></button><button className={activeTab==="pet"?"on":""} onClick={()=>selectTab("pet")}><PawPrint data-icon="pet-paw"/><small>选宠</small></button><button className={activeTab==="community"?"on":""} onClick={()=>selectTab("community")}><HeartIcon/><small>社区</small></button><button className={activeTab==="mine"?"on":""} onClick={()=>selectTab("mine")}><PersonIcon/><small>我的</small></button></nav>;
  const selectedPost=communityPosts.find(post=>post.id===selectedCommunityPost);
  const screens:Record<Screen,()=>React.ReactNode>={home:Home,market:Market,petMarket:PetMarket,supplies:Supplies,community:Community,me:Me,membership:Membership,chat:Chat,profile:Profile,allergy:Allergy,results:Results,edit:Edit,states:States,expired:()=> <Empty expired/>,error:()=> <Empty expired={false}/>};
  const Current=screens[screen];
  return <div className="gulu-shell" style={{"--gulu-status-height":device.platform==="ios"?"54px":"72px","--gulu-safe-area":device.platform==="ios"?device.geometry.safeArea.bottom+"px":"0px"} as CSSProperties}>
    {screen==="chat"&&<header className="apphead chat-fixed-head" data-testid="chat-fixed-header"><button aria-label="返回" onClick={back}><ArrowLeftIcon/></button><strong data-testid="chat-stage-title">{chatTitle}</strong><span/></header>}
    {screen!=="home"&&screen!=="chat"&&screen!=="expired"&&screen!=="error"&&<header className="apphead"><button aria-label="返回" onClick={back}><ArrowLeftIcon/></button><strong>{titles[screen]}</strong><span/></header>}
    <MobileScroll key={screen} className="paper"><Current/></MobileScroll>
    {!['profile','allergy','edit','expired','error'].includes(screen)&&<AppNav/>}
    <BottomSheet open={sheet==="contact"} onOpenChange={v=>!v&&setSheet(null)} title="联系商家进一步了解" description="当前只是原型演示入口。"><div className="sheet"><p>Demo演示功能，暂未开放。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="store"} onOpenChange={v=>!v&&setSheet(null)} title="模拟宠物与店铺详情" description="这里展示的是Demo虚拟数据，不代表真实在售、销量或好评。"><div className="sheet"><p>详情页会在后续原型中继续补充。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="checkout"} onOpenChange={v=>!v&&setSheet(null)} title="这项功能还在准备中" description="下单与支付不会产生任何真实记录或费用。"><div className="sheet"><p>Demo演示功能，暂未开放。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="communityPost"} onOpenChange={v=>!v&&setSheet(null)} title={selectedPost?.title??"社区帖子详情"} description={`${selectedPost?.author??"咕噜港用户"} · Demo虚拟帖子`}><div className="sheet community-sheet">{selectedPost&&<><img src={selectedPost.image} alt={`${selectedPost.title}详情插画`}/><p>{selectedPost.body}</p></>}<button aria-label="收起详情" onClick={()=>setSheet(null)}>收起详情</button></div></BottomSheet>
    <BottomSheet open={sheet==="publish"} onOpenChange={v=>!v&&setSheet(null)} title="这项功能还在准备中" description="第一版只演示浏览和本机互动，不会真的发布内容。"><div className="sheet"><p>Demo演示功能，暂未开放。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="membershipOpen"} onOpenChange={v=>!v&&setSheet(null)} title="这项功能还在准备中" description={`${membershipPlan}付费开通不会产生任何真实记录或费用。`}><div className="sheet"><p>Demo演示功能，暂未开放。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="accountAction"} onOpenChange={v=>!v&&setSheet(null)} title="这项功能还在准备中" description={`${accountSubject}不会产生任何真实记录。`}><div className="sheet"><p>Demo演示功能，暂未开放。</p><button onClick={()=>setSheet(null)}>知道啦</button></div></BottomSheet>
    <BottomSheet open={sheet==="reset"} onOpenChange={v=>!v&&setSheet(null)} title="要重新认识一次吗？" description="重置后，之前的回答和推荐不会带到新会话。"><div className="sheet"><button className="danger" onClick={resetConversation}>确认重置</button><button onClick={()=>setSheet(null)}>先不重置</button></div></BottomSheet>
  </div>
}
