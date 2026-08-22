"use client";
import React from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface TerminalChartProps {
  type: "PAYOFF" | "CONVERGENCE" | "GREEKS" | "PATHS";
  data?: {
    strikes: number[];
    deltas: number[];
    convergence_steps: number[];
    binomial_prices: number[];
    mc_paths: number[][];
  };
}

export default function TerminalChart({ type, data }: TerminalChartProps) {
  const layoutBase = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "monospace", color: "#FFB000", size: 10 },
    margin: { t: 15, r: 15, l: 35, b: 25 },
    xaxis: { gridcolor: "#222222", zerolinecolor: "#444444" },
    yaxis: { gridcolor: "#222222", zerolinecolor: "#444444" },
    showlegend: false,
  };

  if (type === "PAYOFF") {
    const trace = {
      x: data ? data.strikes : [1, 2, 3],
      y: data ? data.deltas.map(d => Math.abs(d) * 100) : [10, 20, 30], // Proxy curve for payoff
      type: "scatter" as const,
      mode: "lines+markers" as const,
      line: { color: "#00FF00", width: 2 },
      marker: { size: 4 },
    };
    return <Plot data={[trace]} layout={layoutBase} useResizeHandler className="w-full h-full" />;
  }

  if (type === "PATHS" && data?.mc_paths) {
    const traces = data.mc_paths.map((path, i) => ({
      y: path,
      type: "scatter" as const,
      mode: "lines" as const,
      line: { color: i % 2 === 0 ? "#00FF00" : "#FFB000", width: 1, opacity: 0.6 },
    }));
    return <Plot data={traces} layout={layoutBase} useResizeHandler className="w-full h-full" />;
  }

  if (type === "GREEKS" && data) {
    const trace = {
      x: data.strikes,
      y: data.deltas,
      type: "scatter" as const,
      mode: "lines+markers" as const,
      line: { color: "#FF00FF", width: 2 },
      marker: { size: 5 },
    };
    return <Plot data={[trace]} layout={{ ...layoutBase, yaxis: { ...layoutBase.yaxis, title: "Delta" } }} useResizeHandler className="w-full h-full" />;
  }

  if (type === "CONVERGENCE" && data) {
    const traceTree = {
      x: data.convergence_steps,
      y: data.binomial_prices,
      type: "scatter" as const,
      mode: "lines+markers" as const,
      line: { color: "#00FFFF", width: 2 },
      name: "Binomial Tree",
    };

    // Calculate a flat reference line for Black-Scholes (using the last/most accurate binomial price or baseline)
    const bsPrice = data.binomial_prices[data.binomial_prices.length - 1];
    const traceBS = {
      x: [data.convergence_steps[0], data.convergence_steps[data.convergence_steps.length - 1]],
      y: [bsPrice, bsPrice],
      type: "scatter" as const,
      mode: "lines" as const,
      line: { color: "#FF3333", width: 2, dash: "dash" as const },
      name: "BS Benchmark",
    };

    return <Plot data={[traceTree, traceBS]} layout={{ ...layoutBase, showlegend: true, legend: { font: { color: "white", size: 9 }, x: 0.5, y: 0.9 } }} useResizeHandler className="w-full h-full" />;
  }

  return (
    <div className="flex items-center justify-center h-full text-gray-600 text-xs italic">
      Awaiting execution data...
    </div>
  );
}