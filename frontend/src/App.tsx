import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid
} from "recharts";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY;
const POLL_MS = 2000;

interface Frame {
  id: number; timestamp: number; phase: string;
  altitude: number; airspeed: number; vertical_speed: number;
  engine_temp: number; fuel_level: number;
  risk_score: number; flight_state: string;
  callsign?: string;
  pitch?: number; roll?: number; yaw?: number;
}

const PHASE_COLOR: Record<string, string> = {
  PREFLIGHT:"#64748b", TAKEOFF:"#10b981", CLIMB:"#06b6d4",
  CRUISE:"#3b82f6", DESCENT:"#f59e0b", LANDING:"#f87171", UNKNOWN:"#94a3b8",
};

async function fetchFrames(): Promise<Frame[]> {
  try {
    const r = await fetch(
      `${SUPABASE_URL}/rest/v1/telemetry_frames?select=*&order=id.desc&limit=80`,
      { headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` } }
    );
    if (!r.ok) return [];
    return (await r.json()).reverse();
  } catch { return []; }
}

function deriveAlerts(f: Frame) {
  const rules: [keyof Frame, string, number, string, string, string][] = [
    ["engine_temp",">",125,"EMERGENCY","ENG-001","ENGINE TEMP REDLINE"],
    ["engine_temp",">",115,"WARNING","ENG-002","Engine temp elevated"],
    ["fuel_level","<",8,"EMERGENCY","FUEL-001","FUEL CRITICAL"],
    ["fuel_level","<",20,"WARNING","FUEL-002","Fuel low"],
    ["airspeed",">",340,"WARNING","SPD-001","VMO exceeded"],
    ["risk_score",">",75,"EMERGENCY","RISK-001","HIGH RISK"],
    ["risk_score",">",50,"WARNING","RISK-002","Elevated risk"],
  ];
  return rules.filter(([field, op, thr]) =>
    op === ">" ? (f[field] as number) > thr : (f[field] as number) < thr
  ).map(([field,,, sev, code, msg]) => ({ severity: sev, code, message: msg, field: String(field), value: f[field] as number }));
}

const SEV: Record<string, {bg:string,border:string,text:string,dot:string}> = {
  EMERGENCY: {bg:"rgba(239,68,68,0.08)",  border:"rgba(239,68,68,0.4)",  text:"#fca5a5", dot:"#ef4444"},
  WARNING:   {bg:"rgba(245,158,11,0.08)", border:"rgba(245,158,11,0.35)",text:"#fcd34d", dot:"#f59e0b"},
  CAUTION:   {bg:"rgba(234,179,8,0.06)",  border:"rgba(234,179,8,0.3)",  text:"#fef08a", dot:"#eab308"},
};

const Tip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{background:"rgba(2,6,14,0.95)",border:"1px solid rgba(99,102,241,0.3)",borderRadius:8,padding:"8px 12px",fontFamily:"'JetBrains Mono',monospace",fontSize:11}}>
      {payload.map((p:any) => (
        <div key={p.name} style={{color:p.color,marginBottom:2}}>
          {p.name}: <span style={{color:"#e2e8f0"}}>{Number(p.value).toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
};

function KPI({ label, value, unit, warn, crit, accent="#06b6d4", icon }: {
  label:string; value:string; unit:string; warn?:boolean; crit?:boolean; accent?:string; icon:string;
}) {
  const borderColor = crit ? "rgba(239,68,68,0.7)" : warn ? "rgba(245,158,11,0.5)" : "rgba(255,255,255,0.07)";
  const valColor    = crit ? "#f87171" : warn ? "#fbbf24" : "#f1f5f9";
  const glowColor   = crit ? "rgba(239,68,68,0.15)" : warn ? "rgba(245,158,11,0.1)" : "transparent";
  return (
    <motion.div whileHover={{y:-2}} transition={{duration:0.15}} style={{
      background:`linear-gradient(135deg, rgba(15,20,35,0.95) 0%, rgba(10,14,26,0.98) 100%)`,
      border:`1px solid ${borderColor}`,
      borderRadius:16,
      padding:"20px 22px",
      boxShadow:`0 4px 24px ${glowColor}, 0 1px 0 rgba(255,255,255,0.04) inset`,
      position:"relative", overflow:"hidden", cursor:"default",
    }}>
      {/* top shimmer */}
      <div style={{position:"absolute",top:0,left:0,right:0,height:1,background:`linear-gradient(90deg,transparent,${accent}60,transparent)`}}/>
      {/* bg glow */}
      {(warn||crit) && <div style={{position:"absolute",top:-20,right:-20,width:80,height:80,borderRadius:"50%",background:glowColor,filter:"blur(20px)",pointerEvents:"none"}}/>}
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
        <span style={{fontSize:10,letterSpacing:"0.14em",color:"#94a3b8",textTransform:"uppercase",fontFamily:"'JetBrains Mono',monospace"}}>{label}</span>
        <span style={{fontSize:16}}>{icon}</span>
      </div>
      <div style={{display:"flex",alignItems:"baseline",gap:6}}>
        <span style={{fontSize:32,fontWeight:700,fontFamily:"'JetBrains Mono',monospace",color:valColor,lineHeight:1}}>{value}</span>
        <span style={{fontSize:12,color:"#64748b",fontFamily:"'JetBrains Mono',monospace"}}>{unit}</span>
      </div>
      {(warn||crit) && (
        <div style={{marginTop:10,height:2,borderRadius:1,background:crit?"rgba(239,68,68,0.5)":"rgba(245,158,11,0.4)",animation:"pulse 1.5s ease-in-out infinite"}}/>
      )}
    </motion.div>
  );
}

function Panel({ title, children, accent="#06b6d4" }: {title:string;children:React.ReactNode;accent?:string}) {
  return (
    <div style={{
      background:"rgba(10,14,26,0.95)",
      border:"1px solid rgba(255,255,255,0.06)",
      borderRadius:16,
      padding:"20px 22px",
      boxShadow:"0 4px 32px rgba(0,0,0,0.4)",
      position:"relative",overflow:"hidden",
    }}>
      <div style={{position:"absolute",top:0,left:0,right:0,height:1,background:`linear-gradient(90deg,transparent,${accent}50,transparent)`}}/>
      <p style={{fontSize:10,letterSpacing:"0.14em",color:"#94a3b8",textTransform:"uppercase",fontFamily:"'JetBrains Mono',monospace",marginBottom:16}}>{title}</p>
      {children}
    </div>
  );
}

export default function App() {
  const [history, setHistory] = useState<Frame[]>([]);
  const [alerts, setAlerts]   = useState<ReturnType<typeof deriveAlerts>>([]);
  const [ready, setReady]     = useState(false);

  const poll = useCallback(async () => {
    const frames = await fetchFrames();
    if (!frames.length) return;
    setHistory(frames);
    setAlerts(deriveAlerts(frames[frames.length - 1]));
    setReady(true);
  }, []);

  useEffect(() => { poll(); const id = setInterval(poll, POLL_MS); return () => clearInterval(id); }, [poll]);

  const f = history[history.length - 1];
  const phase = f?.phase ?? "UNKNOWN";
  const phaseColor = PHASE_COLOR[phase] ?? "#475569";
  const risk = f?.risk_score ?? 0;
  const riskColor = risk >= 75 ? "#ef4444" : risk >= 50 ? "#f59e0b" : "#10b981";

  const chartData = history.map(h => ({
    t: h.timestamp,
    alt: h.altitude,
    spd: h.airspeed,
    tmp: h.engine_temp,
    fuel: +(h.fuel_level).toFixed(1),
    risk: h.risk_score ?? 0,
    vs: h.vertical_speed,
  }));

  if (!ready) return (
    <div style={{minHeight:"100vh",background:"#02060e",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:16}}>
      <motion.div animate={{rotate:360}} transition={{repeat:Infinity,duration:2,ease:"linear"}}
        style={{width:36,height:36,border:"2px solid rgba(6,182,212,0.2)",borderTop:"2px solid #06b6d4",borderRadius:"50%"}}/>
      <p style={{fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:"#64748b",letterSpacing:"0.2em"}}>INITIALIZING FLIGHTSENSE AI</p>
    </div>
  );

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@700;800&display=swap');
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
        body{background:#02060e;color:#e2e8f0;-webkit-font-smoothing:antialiased;}
        ::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-track{background:transparent;}
        ::-webkit-scrollbar-thumb{background:rgba(6,182,212,0.2);border-radius:2px;}
        @keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}
        @keyframes blink{0%,100%{opacity:1;}50%{opacity:0.2;}}
      `}</style>

      {/* Subtle dot grid */}
      <div style={{position:"fixed",inset:0,pointerEvents:"none",
        backgroundImage:"radial-gradient(rgba(255,255,255,0.03) 1px,transparent 1px)",
        backgroundSize:"28px 28px",zIndex:0}}/>
      {/* Top edge glow */}
      <div style={{position:"fixed",top:0,left:0,right:0,height:1,background:"linear-gradient(90deg,transparent,rgba(6,182,212,0.4),transparent)",zIndex:1}}/>

      <div style={{position:"relative",zIndex:2,maxWidth:1440,margin:"0 auto",padding:"28px 24px",minHeight:"100vh"}}>

        {/* ── HEADER ── */}
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:32,flexWrap:"wrap",gap:12}}>
          <div>
            <h1 style={{fontFamily:"'Syne',sans-serif",fontWeight:800,fontSize:28,letterSpacing:"0.02em",lineHeight:1}}>
              Flight<span style={{color:"#06b6d4"}}>Sense</span>
              <span style={{color:"#1e293b",fontSize:15,fontWeight:400,fontFamily:"'JetBrains Mono',monospace",marginLeft:10}}>AI</span>
            </h1>
            <p style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#94a3b8",letterSpacing:"0.18em",marginTop:5,textTransform:"uppercase"}}>
              Aerospace Mission Intelligence Platform
            </p>
          </div>

          <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
            {/* Phase */}
              <div style={{display:"flex",alignItems:"center",gap:8,background:"rgba(255,255,255,0.03)",border:`1px solid ${phaseColor}40`,borderRadius:100,padding:"7px 16px"}}>
              <div style={{width:7,height:7,borderRadius:"50%",background:phaseColor,boxShadow:`0 0 8px ${phaseColor}`}}/>
              <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:phaseColor,letterSpacing:"0.1em"}}>{f?.callsign ?? phase} · {phase}</span>
            </div>
            {/* Frame */}
            <div style={{background:"rgba(255,255,255,0.02)",border:"1px solid rgba(255,255,255,0.06)",borderRadius:100,padding:"7px 14px"}}>
              <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#94a3b8"}}>#{f?.id ?? "---"}</span>
            </div>
            {/* Live */}
            <div style={{display:"flex",alignItems:"center",gap:6,background:"rgba(16,185,129,0.06)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:100,padding:"7px 14px"}}>
              <div style={{width:6,height:6,borderRadius:"50%",background:"#10b981",animation:"blink 1.2s ease-in-out infinite"}}/>
              <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#10b981",letterSpacing:"0.12em"}}>LIVE</span>
            </div>
            {/* Critical badge */}
            {alerts.filter(a=>a.severity==="EMERGENCY").length > 0 && (
              <motion.div animate={{opacity:[1,0.5,1]}} transition={{repeat:Infinity,duration:1}}
                style={{background:"rgba(239,68,68,0.1)",border:"1px solid rgba(239,68,68,0.4)",borderRadius:100,padding:"7px 14px"}}>
                <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#f87171",letterSpacing:"0.1em"}}>
                  ⚠ {alerts.filter(a=>a.severity==="EMERGENCY").length} CRITICAL
                </span>
              </motion.div>
            )}
          </div>
        </div>

        {/* ── KPI GRID ── */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(6,1fr)",gap:14,marginBottom:20}}>
          <KPI label="Altitude"       value={f?.altitude?.toFixed(0)??"---"}          unit="ft"    icon="✈️" accent="#06b6d4"/>
          <KPI label="Airspeed"       value={f?.airspeed?.toFixed(1)??"---"}           unit="kt"    icon="💨" warn={(f?.airspeed??0)>300} crit={(f?.airspeed??0)>340} accent="#818cf8"/>
          <KPI label="Vertical Speed" value={f?.vertical_speed?.toFixed(0)??"---"}     unit="fpm"   icon="↕️" accent="#34d399"/>
          <KPI label="Engine Temp"    value={f?.engine_temp?.toFixed(1)??"---"}        unit="°C"    icon="🌡️" warn={(f?.engine_temp??0)>115} crit={(f?.engine_temp??0)>125} accent="#f97316"/>
          <KPI label="Fuel"           value={f?.fuel_level?.toFixed(1)??"---"}         unit="%"     icon="⛽" warn={(f?.fuel_level??100)<20} crit={(f?.fuel_level??100)<8} accent="#a78bfa"/>
          <KPI label="Risk Index"     value={risk.toFixed(1)}                          unit="/100"  icon="⚡" warn={risk>50} crit={risk>75} accent={riskColor}/>
        </div>

        {/* ── RISK BAR ── */}
        <div style={{background:"rgba(10,14,26,0.95)",border:"1px solid rgba(255,255,255,0.05)",borderRadius:12,padding:"14px 20px",marginBottom:20}}>
          <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
            <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#94a3b8",letterSpacing:"0.14em",textTransform:"uppercase"}}>Mission Risk Index</span>
            <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:13,fontWeight:700,color:riskColor}}>{risk.toFixed(1)}<span style={{color:"#1e293b",fontWeight:400}}> / 100</span></span>
          </div>
          <div style={{height:6,background:"rgba(255,255,255,0.04)",borderRadius:3,overflow:"hidden"}}>
            <motion.div animate={{width:`${Math.min(risk,100)}%`}} transition={{duration:0.8,ease:"easeOut"}}
              style={{height:"100%",borderRadius:3,background:`linear-gradient(90deg,#10b981,${riskColor})`,boxShadow:`0 0 12px ${riskColor}60`}}/>
          </div>
          <div style={{display:"flex",justifyContent:"space-between",marginTop:5}}>
            {["0","25 SAFE","50 CAUTION","75 DANGER","100"].map(t=>(
              <span key={t} style={{fontFamily:"'JetBrains Mono',monospace",fontSize:8,color:"#1e293b"}}>{t}</span>
            ))}
          </div>
        </div>

        {/* ── MAIN CHARTS ── */}
        <div style={{display:"grid",gridTemplateColumns:"2fr 1fr",gap:16,marginBottom:16}}>
          <Panel title="Altitude (ft) & Airspeed (kt)" accent="#06b6d4">
            <div style={{display:"flex",gap:16,marginBottom:10}}>
              {[{c:"#06b6d4",l:"Altitude"},{c:"#f97316",l:"Airspeed"}].map(({c,l})=>(
                <div key={l} style={{display:"flex",alignItems:"center",gap:6}}>
                  <div style={{width:16,height:2,background:c,borderRadius:1}}/>
                  <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#94a3b8"}}>{l}</span>
                </div>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={chartData} margin={{top:4,right:4,left:-10,bottom:0}}>
                <defs>
                  <linearGradient id="gA" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#06b6d4" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="gS" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#f97316" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.03)" strokeDasharray="3 3"/>
                <XAxis dataKey="t" hide/>
                <YAxis yAxisId="a" tick={{fill:"#64748b",fontSize:9,fontFamily:"JetBrains Mono"}} width={45}/>
                <YAxis yAxisId="s" orientation="right" tick={{fill:"#64748b",fontSize:9,fontFamily:"JetBrains Mono"}} width={40}/>
                <Tooltip content={<Tip/>}/>
                <Area yAxisId="a" type="monotone" dataKey="alt" name="ALT(ft)" stroke="#06b6d4" fill="url(#gA)" strokeWidth={1.5} dot={false}/>
                <Area yAxisId="s" type="monotone" dataKey="spd" name="SPD(kt)" stroke="#f97316" fill="url(#gS)" strokeWidth={1.5} dot={false}/>
              </AreaChart>
            </ResponsiveContainer>
          </Panel>

          {/* Alert stream */}
          <Panel title="Alert Stream" accent="#ef4444">
            <div style={{display:"flex",flexDirection:"column",gap:8,maxHeight:244,overflowY:"auto"}}>
              <AnimatePresence>
                {alerts.length === 0 ? (
                  <div style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:200,gap:10}}>
                    <div style={{width:36,height:36,borderRadius:"50%",background:"rgba(16,185,129,0.1)",border:"1px solid rgba(16,185,129,0.2)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:18}}>✓</div>
                    <p style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#1e293b",letterSpacing:"0.12em"}}>ALL SYSTEMS NOMINAL</p>
                  </div>
                ) : alerts.map((a,i) => {
                  const s = SEV[a.severity] ?? {bg:"rgba(99,102,241,0.08)",border:"rgba(99,102,241,0.3)",text:"#a5b4fc",dot:"#6366f1"};
                  return (
                    <motion.div key={a.code+i} initial={{opacity:0,x:16}} animate={{opacity:1,x:0}} exit={{opacity:0,x:-16}}
                      style={{background:s.bg,border:`1px solid ${s.border}`,borderRadius:10,padding:"10px 12px",display:"flex",alignItems:"flex-start",gap:10}}>
                      <div style={{width:6,height:6,borderRadius:"50%",background:s.dot,marginTop:4,flexShrink:0,boxShadow:`0 0 6px ${s.dot}`}}/>
                      <div>
                        <p style={{fontFamily:"'JetBrains Mono',monospace",fontSize:9,color:"#64748b",marginBottom:2}}>{a.code}</p>
                        <p style={{fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:s.text,fontWeight:600}}>{a.message}</p>
                        <p style={{fontFamily:"'JetBrains Mono',monospace",fontSize:9,color:"#64748b",marginTop:2}}>{a.field}: {a.value}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </Panel>
        </div>

        {/* ── SECONDARY CHARTS ── */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:16,marginBottom:16}}>
          <Panel title="Engine Temperature (°C)" accent="#f97316">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData} margin={{top:4,right:4,left:-10,bottom:0}}>
                <CartesianGrid stroke="rgba(255,255,255,0.03)" strokeDasharray="3 3"/>
                <XAxis dataKey="t" hide/>
                <YAxis domain={[60,140]} tick={{fill:"#64748b",fontSize:9,fontFamily:"JetBrains Mono"}} width={35}/>
                <Tooltip content={<Tip/>}/>
                <ReferenceLine y={125} stroke="rgba(239,68,68,0.5)" strokeDasharray="4 3" label={{value:"CRIT",position:"right",fill:"#ef4444",fontSize:8,fontFamily:"JetBrains Mono"}}/>
                <ReferenceLine y={115} stroke="rgba(245,158,11,0.4)" strokeDasharray="4 3" label={{value:"WARN",position:"right",fill:"#f59e0b",fontSize:8,fontFamily:"JetBrains Mono"}}/>
                <Line type="monotone" dataKey="tmp" name="Temp(°C)" stroke="#f97316" strokeWidth={1.5} dot={false}/>
              </LineChart>
            </ResponsiveContainer>
          </Panel>

          <Panel title="Fuel Level (%)" accent="#a78bfa">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData} margin={{top:4,right:4,left:-10,bottom:0}}>
                <defs>
                  <linearGradient id="gF" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#a78bfa" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a78bfa" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.03)" strokeDasharray="3 3"/>
                <XAxis dataKey="t" hide/>
                <YAxis domain={[0,100]} tick={{fill:"#64748b",fontSize:9,fontFamily:"JetBrains Mono"}} width={35}/>
                <Tooltip content={<Tip/>}/>
                <ReferenceLine y={20} stroke="rgba(245,158,11,0.4)" strokeDasharray="4 3"/>
                <Area type="monotone" dataKey="fuel" name="Fuel(%)" stroke="#a78bfa" fill="url(#gF)" strokeWidth={1.5} dot={false}/>
              </AreaChart>
            </ResponsiveContainer>
          </Panel>

          <Panel title="Risk Score" accent="#6366f1">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData} margin={{top:4,right:4,left:-10,bottom:0}}>
                <defs>
                  <linearGradient id="gR" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.35}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.03)" strokeDasharray="3 3"/>
                <XAxis dataKey="t" hide/>
                <YAxis domain={[0,100]} tick={{fill:"#64748b",fontSize:9,fontFamily:"JetBrains Mono"}} width={35}/>
                <Tooltip content={<Tip/>}/>
                <ReferenceLine y={75} stroke="rgba(239,68,68,0.4)" strokeDasharray="4 3"/>
                <ReferenceLine y={50} stroke="rgba(245,158,11,0.3)" strokeDasharray="4 3"/>
                <Area type="monotone" dataKey="risk" name="Risk" stroke="#6366f1" fill="url(#gR)" strokeWidth={1.5} dot={false}/>
              </AreaChart>
            </ResponsiveContainer>
          </Panel>
        </div>

        {/* ── ATTITUDE ROW ── */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:14,marginBottom:28}}>
          {[
            {label:"Pitch", value:f?.pitch, warn:Math.abs(f?.pitch??0)>20, unit:"°"},
            {label:"Roll",  value:f?.roll,  warn:Math.abs(f?.roll??0)>30,  unit:"°"},
            {label:"Yaw",   value:f?.yaw,   warn:false,                     unit:"°"},
          ].map(({label,value,warn,unit})=>(
            <div key={label} style={{
              background:"rgba(10,14,26,0.95)",
              border:`1px solid ${warn?"rgba(245,158,11,0.35)":"rgba(255,255,255,0.05)"}`,
              borderRadius:14,padding:"16px 20px",display:"flex",justifyContent:"space-between",alignItems:"center",
            }}>
              <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:"#64748b",letterSpacing:"0.12em",textTransform:"uppercase"}}>{label}</span>
              <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:24,fontWeight:700,color:warn?"#fbbf24":"#94a3b8"}}>
                {value!=null?(value>0?"+":"")+value.toFixed(1):"---"}<span style={{fontSize:12,color:"#64748b"}}>{unit}</span>
              </span>
            </div>
          ))}
        </div>

        {/* ── FOOTER ── */}
        <div style={{textAlign:"center",paddingBottom:8}}>
          <p style={{fontFamily:"'JetBrains Mono',monospace",fontSize:9,color:"#94a3b8",letterSpacing:"0.18em",textTransform:"uppercase"}}>
            FlightSense AI · {f?.callsign ?? "---"} · Frame #{f?.id} · {phase} · {f?.flight_state ?? "—"} · {new Date().toLocaleTimeString()}
          </p>
        </div>

      </div>
    </>
  );
}