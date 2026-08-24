"use client";
import React, { useState } from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function TerminalChart({ type, data }: { type: string, data?: any }) {
  const [activeGreek, setActiveGreek] = useState<"deltas"|"gammas"|"thetas"|"vegas"|"rhos">("deltas");
  const [convType, setConvType] = useState<"BINOMIAL"|"MC">("BINOMIAL");

  // Increased bottom and left margins to ensure titles are visible
  const layoutBase = {
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "monospace", color: "#FFB000", size: 10 },
    margin: { t: 30, r: 15, l: 60, b: 50 }, 
    xaxis: { gridcolor: "#222222", zerolinecolor: "#444444", automargin: true, title: { text: "", font: { size: 11, color: "#888" } } },
    yaxis: { gridcolor: "#222222", zerolinecolor: "#444444", automargin: true, title: { text: "", font: { size: 11, color: "#888" } } },
    showlegend: false,
  };

  if (!data) return <div className="flex items-center justify-center h-full text-gray-600 text-xs italic">Awaiting execution data...</div>;

  // 0. The true Dollar Payoff Curve
  if (type === "PAYOFF") {
    const spots = data.payoff_spots || [];
    const payoffs = data.payoffs || [];
    const trace = { 
      x: spots, y: payoffs, type: "scatter" as const, mode: "lines" as const, 
      line: { color: "#00FF00", width: 2 } 
    };
    return <Plot data={[trace]} layout={{ ...layoutBase, xaxis: { ...layoutBase.xaxis, title: "Underlying Spot Price ($)" }, yaxis: { ...layoutBase.yaxis, title: "Dollar Payoff ($)" } }} useResizeHandler className="w-full h-full" />;
  }

  // 1. The ITM Probability Curve (Delta proxy)
  if (type === "PROBABILITY") {
    const strikes = data.strikes || [];
    const deltas = data.deltas || [];
    const trace = { 
      x: strikes, y: deltas.map((d: number) => Math.abs(d) * 100), 
      type: "scatter" as const, mode: "lines+markers" as const, line: { color: "#FF00FF", width: 2 }, marker: { size: 4 } 
    };
    return <Plot data={[trace]} layout={{ ...layoutBase, xaxis: { ...layoutBase.xaxis, title: "Strike Price ($)" }, yaxis: { ...layoutBase.yaxis, title: "ITM Probability (%)" } }} useResizeHandler className="w-full h-full" />;
  }

  if (type === "PATHS") {
    const neonColors = ["#00FF00", "#FFB000", "#00FFFF", "#FF00FF", "#FFFF00", "#FF3333", "#33FFCC", "#CC33FF"];
    const mcPaths = data.mc_paths || [];
    const traces = mcPaths.map((path: number[], i: number) => ({ 
      y: path, type: "scatter" as const, mode: "lines" as const, line: { color: neonColors[i % neonColors.length], width: 1, opacity: 0.6 } 
    }));
    return <Plot data={traces} layout={{ ...layoutBase, xaxis: { ...layoutBase.xaxis, title: "Time Steps (dt)" }, yaxis: { ...layoutBase.yaxis, title: "Simulated Spot Price ($)" } }} useResizeHandler className="w-full h-full" />;
  }

  if (type === "GREEKS") {
    const greekColors = { deltas: "#00FF00", gammas: "#00FFFF", thetas: "#FF3333", vegas: "#FFB000", rhos: "#FF00FF" };
    const strikes = data.strikes || [];
    const activeData = data[activeGreek] || [];
    
    const trace = { 
      x: strikes, y: activeData, type: "scatter" as const, mode: "lines+markers" as const, line: { color: greekColors[activeGreek], width: 2 }, marker: { size: 5 } 
    };
    return (
      <div className="relative w-full h-full">
        <div className="absolute top-0 right-2 z-10 flex gap-2 text-[9px]">
          {(["deltas", "gammas", "thetas", "vegas", "rhos"] as const).map(g => (
            <button key={g} onClick={() => setActiveGreek(g)} className={`px-1 border ${activeGreek === g ? 'bg-term-amber text-black border-term-amber' : 'text-gray-400 border-gray-600'}`}>{g.toUpperCase()}</button>
          ))}
        </div>
        <Plot data={[trace]} layout={{ ...layoutBase, xaxis: { ...layoutBase.xaxis, title: "Strike Price ($)" }, yaxis: { ...layoutBase.yaxis, title: activeGreek.toUpperCase() } }} useResizeHandler className="w-full h-full" />
      </div>
    );
  }

  if (type === "CONVERGENCE") {
    const isBinomial = convType === "BINOMIAL";
    const binomX = data.convergence_steps || [];
    const mcX = data.mc_sim_counts || [];
    const currentX = isBinomial ? binomX : mcX;
    
    const xStart = currentX.length > 0 ? currentX[0] : 0;
    const xEnd = currentX.length > 0 ? currentX[currentX.length - 1] : 100;
    const bsPrice = data.bs_price || 0;

    const bsTrace = { 
      x: [xStart, xEnd], y: [bsPrice, bsPrice], type: "scatter" as const, mode: "lines" as const, 
      line: { color: "#FF3333", width: 2, dash: "dash" as const }, name: "BS Benchmark" 
    };
    
    let traces: any[] = [bsTrace];
    
    if (isBinomial && data.binomial_prices) {
      traces.push({ x: binomX, y: data.binomial_prices, type: "scatter" as const, mode: "lines+markers" as const, line: { color: "#FFB000", width: 2 }, name: "Binomial" });
    } else if (!isBinomial && data.mc_prices) {
      traces.push(
        { x: mcX, y: data.mc_upper, type: "scatter" as const, mode: "lines" as const, line: { color: "#004444", width: 0 }, showlegend: false, name: "Upper Bound", hoverinfo: "skip" },
        { x: mcX, y: data.mc_lower, type: "scatter" as const, mode: "lines" as const, fill: "tonexty", fillcolor: "rgba(0, 255, 255, 0.1)", line: { color: "#004444", width: 0 }, showlegend: false, name: "Lower Bound", hoverinfo: "skip" },
        { x: mcX, y: data.mc_prices, type: "scatter" as const, mode: "lines+markers" as const, line: { color: "#00FFFF", width: 2 }, name: "MC Mean" }
      );
    }

    return (
      <div className="relative w-full h-full">
        <div className="absolute top-0 right-2 z-10 flex gap-2 text-[9px]">
          <button onClick={() => setConvType("BINOMIAL")} className={`px-1 border ${convType === "BINOMIAL" ? 'bg-term-amber text-black border-term-amber' : 'text-gray-400 border-gray-600'}`}>BINOMIAL</button>
          <button onClick={() => setConvType("MC")} className={`px-1 border ${convType === "MC" ? 'bg-term-amber text-black border-term-amber' : 'text-gray-400 border-gray-600'}`}>MONTE CARLO</button>
        </div>
        <Plot data={traces} layout={{ ...layoutBase, showlegend: true, legend: { font: { color: "white", size: 9 }, orientation: "h", x: 0.1, y: 1.15 }, xaxis: { ...layoutBase.xaxis, title: isBinomial ? "Tree Steps (N)" : "Simulated Paths" }, yaxis: { ...layoutBase.yaxis, title: "Calculated Price ($)" } }} useResizeHandler className="w-full h-full" />
      </div>
    );
  }

  return null;
}