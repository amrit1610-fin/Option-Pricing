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
  
  // Includes both PAYOFF and PROBABILITY now
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

  const handlePriceCalculation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    addLog(`Initiating calculation for ${ticker} | Strike: ${strike}`);

    try {
      // Uses the live URL in production, and localhost during local development
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
        <div className="border border-term-border bg-term-panel p-2 flex flex-col">
          <h2 className="text-white text-xs mb-2 border-b border-term-border pb-1 font-bold">DES &lt;GO&gt; - CONTRACT &amp; MARKET SPECIFICATIONS</h2>
          <div className="flex flex-col gap-1 text-xs justify-around flex-grow">
            <div className="flex justify-between border-b border-gray-900 pb-0.5"><span className="text-gray-400">EXERCISE STYLE:</span><span className="text-term-red font-bold">{data ? data.contract_details.exercise_style : "--"}</span></div>
            <div className="flex justify-between border-b border-gray-900 pb-0.5"><span className="text-gray-400">UNDERLYING SPOT:</span><span className="text-term-amber">{data ? `$${data.contract_details.spot_price.toFixed(2)}` : "--"}</span></div>
            <div className="flex justify-between border-b border-gray-900 pb-0.5"><span className="text-gray-400">TARGET STRIKE:</span><span className="text-term-amber">{data ? `$${data.contract_details.strike_price.toFixed(2)}` : "--"}</span></div>
            <div className="flex justify-between border-b border-gray-900 pb-0.5"><span className="text-gray-400">TIME TO EXPIRY (YRS):</span><span className="text-term-amber">{data ? data.contract_details.time_to_expiry.toFixed(4) : "--"}</span></div>
            <div className="flex justify-between border-b border-gray-900 pb-0.5"><span className="text-gray-400">MARKET MID-PRICE:</span><span className="text-white font-bold">{data ? `$${data.contract_details.market_price.toFixed(2)}` : "--"}</span></div>
            <div className="flex justify-between"><span className="text-gray-400">CALCULATED TRUE IV:</span><span className="text-term-green font-bold">{data ? `${(data.contract_details.implied_volatility * 100).toFixed(2)}%` : "--"}</span></div>
          </div>
        </div>

        <div className="border border-term-border bg-term-panel p-2 flex flex-col overflow-y-auto">
          <h2 className="text-white text-xs mb-2 border-b border-term-border pb-1 font-bold">PRC &lt;GO&gt; - VALUATION &amp; RISK SENSITIVITIES</h2>
          <div className="grid grid-cols-2 gap-4 text-xs">
            {data ? (
              Object.entries(data.results).map(([modelName, metrics]) => (
                <div key={modelName} className="mb-2">
                  <div className="text-gray-400 mb-1 border-b border-term-border font-bold">{modelName}</div>
                  <div className="flex justify-between"><span>PRICE</span><span className="text-term-green font-bold">${metrics.price.toFixed(4)}</span></div>
                  <div className="flex justify-between"><span>DELTA</span><span className={metrics.delta < 0 ? "text-term-red" : "text-term-green"}>{metrics.delta.toFixed(4)}</span></div>
                  <div className="flex justify-between"><span>GAMMA</span><span className="text-term-amber">{metrics.gamma.toFixed(4)}</span></div>
                  <div className="flex justify-between"><span>THETA</span><span className="text-term-red">{metrics.theta.toFixed(4)}</span></div>
                  <div className="flex justify-between"><span>VEGA</span><span className="text-term-amber">{metrics.vega.toFixed(4)}</span></div>
                  <div className="flex justify-between"><span>RHO</span><span className="text-term-amber">{metrics.rho.toFixed(4)}</span></div>
                </div>
              ))
            ) : (
              <div className="text-gray-600 italic col-span-2">Awaiting calculation...</div>
            )}
          </div>
        </div>

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
          <div className="flex-grow min-h-0">
            <TerminalChart type={activeTab} data={data?.charts} />
          </div>
        </div>

        <div className="border border-term-border bg-term-panel p-2 flex flex-col">
          <div className="flex justify-between items-center mb-2 border-b border-term-border pb-1">
            <h2 className="text-white text-xs font-bold">SYS &lt;GO&gt; - EXECUTION LOGS</h2>
            <button onClick={clearLogs} className="text-term-red hover:bg-term-red hover:text-black border border-term-red px-1 text-[10px] transition-colors">[CLEAR]</button>
          </div>
          <div className="text-[11px] text-gray-400 flex flex-col gap-1 overflow-y-auto min-h-0 flex-grow">
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