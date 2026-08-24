"use client";

import React, { useState } from "react";
import TerminalChart from "../components/TerminalChart";

interface PricingResponse {
  status: string;
  contract_details: {
    spot_price: number;
    strike_price: number;
    risk_free_rate: number;
    time_to_expiry: number;
    implied_volatility: number;
    market_price: number;
    exercise_style: string;
  };
  results: Record<string, {
    price: number;
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  }>;
  charts?: any;
}

export default function TerminalDashboard() {
  const [ticker, setTicker] = useState("^SPX");
  const [expiry, setExpiry] = useState("2026-08-28");
  const [strike, setStrike] = useState<number>(7700.0);
  const [optionType, setOptionType] = useState<string>("put");

  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<PricingResponse | null>(null);

  const [activeTab, setActiveTab] = useState<"PAYOFF" | "PROBABILITY" | "CONVERGENCE" | "GREEKS" | "PATHS">("PAYOFF");

  const [logs, setLogs] = useState<string[]>([
    "[SYS] Pricing Terminal initialized.",
    "[SYS] Auto-Routing Engine Active. Press <EXECUTE>.",
  ]);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, `[${timestamp}] ${msg}`]);
  };

  const clearLogs = () => setLogs([]);

  const getGreekInterpretations = (metrics: any) => {
    if (!metrics) return [];

    const d = metrics.delta;
    const g = metrics.gamma;
    const t = metrics.theta;
    const v = metrics.vega;
    const price = metrics.price || 0.01; // Prevent division by zero

    // 1. DELTA
    let deltaMsg = "";
    const absD = Math.abs(d);
    const dir = d > 0 ? "Long" : "Short";
    if (absD >= 0.8) {
      deltaMsg = `Deep ITM. Behaves highly like a ${dir} stock position. ~${(absD * 100).toFixed(0)}% implied probability of expiring ITM.`;
    } else if (absD >= 0.4 && absD <= 0.6) {
      deltaMsg = `At-The-Money. Peak directional uncertainty with roughly a coin-flip (~${(absD * 100).toFixed(0)}%) probability of expiring ITM.`;
    } else if (absD <= 0.2) {
      deltaMsg = `Far OTM. Mostly extrinsic value. Requires an aggressive directional move to realize intrinsic worth.`;
    } else {
      deltaMsg = `Moderate directional exposure. Market implies a ~${(absD * 100).toFixed(0)}% probability of expiring ITM.`;
    }

    // 2. GAMMA
    let gammaMsg = "";
    if (g > Math.abs(d) * 0.1) {
      gammaMsg = `High convexity (Gamma Risk). Delta is highly unstable and will accelerate aggressively on spot movements.`;
    } else {
      gammaMsg = `Stable convexity. A $1 up-move shifts Delta mildly to ${(d + g).toFixed(4)}.`;
    }

    // 3. THETA
    let thetaMsg = "";
    const dailyBleedPct = Math.abs(t) / price;
    if (dailyBleedPct > 0.05) {
      thetaMsg = `SEVERE decay. Bleeding ${(dailyBleedPct * 100).toFixed(1)}% of total premium per day. Avoid holding over weekends.`;
    } else if (dailyBleedPct < 0.005) {
      thetaMsg = `Minimal daily time decay ($${Math.abs(t).toFixed(2)}/day). Mostly insulated from short-term Theta burn.`;
    } else {
      thetaMsg = `Standard decay curve, losing $${Math.abs(t).toFixed(2)} of extrinsic value per day.`;
    }

    // 4. VEGA
    let vegaMsg = "";
    const vegaImpact = (v / 100) / price;
    if (vegaImpact > 0.1) {
      vegaMsg = `High IV Crush Risk. A 1% drop in Implied Volatility wipes out ${(vegaImpact * 100).toFixed(1)}% of the premium.`;
    } else {
      vegaMsg = `A 1% IV expansion adds $${(v / 100).toFixed(2)} to premium. Volatility shocks have moderate impact.`;
    }

    return [
      `DELTA: ${deltaMsg}`,
      `GAMMA: ${gammaMsg}`,
      `THETA: ${thetaMsg}`,
      `VEGA: ${vegaMsg}`
    ];
  };

  const handlePriceCalculation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    addLog(`Initiating calculation for ${ticker} | Strike: ${strike}`);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

      const response = await fetch(`${API_URL}/api/price`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: ticker.trim(),
          expiration_date: expiry.trim(),
          strike_price: Number(strike),
          option_type: optionType.toLowerCase(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to fetch pricing data");
      }

      const result: PricingResponse = await response.json();
      setData(result);
      addLog(`[SUCCESS] Detected ${result.contract_details.exercise_style} style. Models executed successfully.`);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error occurred";
      addLog(`[ERROR] ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-term-bg text-term-amber font-mono p-1 flex flex-col select-none">
      {/* COMMAND BAR */}
      <form
        onSubmit={handlePriceCalculation}
        className="h-10 border border-term-border bg-term-panel flex items-center px-2 text-xs gap-3 mb-1"
      >
        <span className="text-gray-500 font-bold">CMD&gt;</span>
        <div className="flex items-center gap-1">
          <span className="text-gray-400">TICKER:</span>
          <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="bg-black border border-term-border px-1 text-term-amber uppercase w-20 outline-none" />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-gray-400">EXPIRY:</span>
          <input type="text" value={expiry} onChange={(e) => setExpiry(e.target.value)} className="bg-black border border-term-border px-1 text-term-amber w-28 outline-none" placeholder="YYYY-MM-DD" />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-gray-400">STRIKE:</span>
          <input type="number" value={strike} onChange={(e) => setStrike(parseFloat(e.target.value))} className="bg-black border border-term-border px-1 text-term-amber w-24 outline-none" />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-gray-400">TYPE:</span>
          <select value={optionType} onChange={(e) => setOptionType(e.target.value)} className="bg-black border border-term-border px-1 text-term-amber outline-none">
            <option value="put">PUT</option>
            <option value="call">CALL</option>
          </select>
        </div>
        <button type="submit" disabled={loading} className="bg-term-amber text-black font-bold px-3 py-0.5 hover:bg-yellow-400 disabled:opacity-50">
          {loading ? "CALCULATING..." : "<EXECUTE>"}
        </button>
        <span className="ml-auto text-term-green flex items-center gap-1 text-[11px]">
          <span className="inline-block w-2 h-2 rounded-full bg-term-green animate-pulse"></span>
          ONLINE
        </span>
      </form>

      <div className="grid grid-cols-2 grid-rows-2 gap-1 flex-grow overflow-hidden">
        
        {/* DES PANEL - DENSE LAYOUT */}
        <div className="border border-term-border bg-term-panel p-2 flex flex-col">
          <h2 className="text-white text-xs mb-2 border-b border-term-border pb-1 font-bold">DES &lt;GO&gt; - CONTRACT SPECIFICATIONS</h2>
          <div className="flex flex-col gap-0 text-xs flex-grow">
            <div className="flex justify-between bg-gray-900 px-1 py-0.5"><span className="text-gray-400">EXERCISE STYLE:</span><span className="text-term-red font-bold">{data ? data.contract_details.exercise_style.toUpperCase() : "--"}</span></div>
            <div className="flex justify-between px-1 py-0.5"><span className="text-gray-400">MULTIPLIER:</span><span className="text-white">100</span></div>
            <div className="flex justify-between bg-gray-900 px-1 py-0.5"><span className="text-gray-400">UNDERLYING SPOT:</span><span className="text-term-amber">{data ? `$${data.contract_details.spot_price.toFixed(2)}` : "--"}</span></div>
            <div className="flex justify-between px-1 py-0.5"><span className="text-gray-400">TARGET STRIKE:</span><span className="text-term-amber">{data ? `$${data.contract_details.strike_price.toFixed(2)}` : "--"}</span></div>
            <div className="flex justify-between bg-gray-900 px-1 py-0.5"><span className="text-gray-400">MONEYNESS:</span><span className="text-white">{data ? `${((data.contract_details.spot_price / data.contract_details.strike_price - 1) * 100).toFixed(2)}%` : "--"}</span></div>
            <div className="flex justify-between px-1 py-0.5"><span className="text-gray-400">DTE / YEARS:</span><span className="text-term-amber">{data ? `${Math.round(data.contract_details.time_to_expiry * 365)} / ${data.contract_details.time_to_expiry.toFixed(4)}` : "--"}</span></div>
            <div className="flex justify-between bg-gray-900 px-1 py-0.5"><span className="text-gray-400">DIVIDEND YIELD:</span><span className="text-white">0.00%</span></div>
            <div className="flex justify-between px-1 py-0.5"><span className="text-gray-400">MARKET MID-PRICE:</span><span className="text-white font-bold">{data ? `$${data.contract_details.market_price.toFixed(2)}` : "--"}</span></div>
            <div className="flex justify-between bg-gray-900 px-1 py-0.5"><span className="text-gray-400">CALCULATED TRUE IV:</span><span className="text-term-green font-bold">{data ? `${(data.contract_details.implied_volatility * 100).toFixed(2)}%` : "--"}</span></div>
          </div>
        </div>

        {/* PRC PANEL - RISK MATRIX & INTERPRETER */}
        <div className="border border-term-border bg-term-panel p-2 flex flex-col overflow-y-auto">
          <h2 className="text-white text-xs mb-2 border-b border-term-border pb-1 font-bold">PRC &lt;GO&gt; - VALUATION &amp; RISK MATRIX</h2>
          
          <div className="grid grid-cols-4 gap-1 text-[11px] mb-2 border-b border-gray-800 pb-2">
            <div className="col-span-1 text-gray-500 font-bold border-r border-gray-800 pr-1">METRIC</div>
            <div className="col-span-1 text-gray-400 font-bold text-right">BSM</div>
            <div className="col-span-1 text-gray-400 font-bold text-right">BINOMIAL</div>
            <div className="col-span-1 text-gray-400 font-bold text-right">MONTE CARLO</div>
            
            {['price', 'delta', 'gamma', 'theta', 'vega', 'rho'].map((metric, idx) => (
              <React.Fragment key={metric}>
                <div className={`col-span-1 text-gray-400 uppercase border-r border-gray-800 pr-1 ${idx % 2 === 0 ? 'bg-gray-900' : ''}`}>{metric}</div>
                {['BLACK-SCHOLES', 'BINOMIAL TREE', 'MONTE CARLO'].map((model) => (
                  <div key={`${model}-${metric}`} className={`col-span-1 text-right font-mono ${idx % 2 === 0 ? 'bg-gray-900' : ''} ${metric === 'price' ? 'text-term-green font-bold' : 'text-term-amber'}`}>
                    {data && data.results[model] ? data.results[model][metric as keyof typeof data.results[string]].toFixed(4) : "--"}
                  </div>
                ))}
              </React.Fragment>
            ))}
          </div>

          <div className="text-[10px] text-gray-400 flex flex-col gap-1 mt-auto bg-black p-1 border border-gray-800">
            <span className="text-term-amber font-bold mb-1">REAL-WORLD SENSITIVITIES:</span>
            {data ? (
              getGreekInterpretations(data.results['BLACK-SCHOLES'] || data.results['BINOMIAL TREE'] || data.results['MONTE CARLO']).map((text, i) => (
                <div key={i} className="leading-tight"><span className="text-white">&gt;</span> {text}</div>
              ))
            ) : (
              <div className="italic text-gray-600">Awaiting execution data to generate interpretations...</div>
            )}
          </div>
        </div>

        {/* GRPH PANEL */}
        <div className="border border-term-border bg-term-panel p-2 flex flex-col">
          <div className="flex justify-between items-center mb-2 border-b border-term-border pb-1">
            <h2 className="text-white text-xs font-bold">GRPH &lt;GO&gt; - VISUALIZATION</h2>
            <div className="flex gap-3 text-[10px]">
              {(["PAYOFF", "PROBABILITY", "CONVERGENCE", "GREEKS", "PATHS"] as const).map((tab) => (
                <button 
                  key={tab} 
                  onClick={() => setActiveTab(tab)}
                  className={`hover:text-white transition-colors ${activeTab === tab ? "text-term-amber border-b border-term-amber" : "text-gray-500"}`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-grow min-h-0 relative">
             {/* Note: Ensure TerminalChart cleanly accepts null data gracefully */}
            <TerminalChart type={activeTab} data={data?.charts} />
          </div>
        </div>

        {/* SYS PANEL */}
        <div className="border border-term-border bg-term-panel p-2 flex flex-col">
          <div className="flex justify-between items-center mb-2 border-b border-term-border pb-1">
            <h2 className="text-white text-xs font-bold">SYS &lt;GO&gt; - EXECUTION LOGS</h2>
            <button onClick={clearLogs} className="text-term-red hover:bg-term-red hover:text-black border border-term-red px-1 text-[10px] transition-colors">[CLEAR]</button>
          </div>
          <div className="text-[11px] text-gray-400 flex flex-col gap-1 overflow-y-auto min-h-0 flex-grow font-mono">
            {logs.length === 0 ? (
              <span className="text-gray-600 italic">Logs cleared...</span>
            ) : (
              logs.map((log, idx) => (
                <p key={idx} className={log.includes("[SUCCESS]") ? "text-term-green" : log.includes("[ERROR]") ? "text-term-red" : "text-gray-400"}>{log}</p>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}