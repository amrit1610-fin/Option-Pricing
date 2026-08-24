"use client";

import React from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, loading: () => <div className="text-gray-600 text-xs italic">Loading visualization module...</div> });

interface TerminalChartProps {
  type: "PAYOFF" | "PROBABILITY" | "CONVERGENCE" | "GREEKS" | "PATHS";
  data?: any;
}

export default function TerminalChart({ type, data }: TerminalChartProps) {
  // If no chart data object exists at all
  if (!data) {
    return <div className="flex h-full w-full items-center justify-center text-gray-600 text-sm italic">Awaiting execution data...</div>;
  }

  // Handle both UPPERCASE (React state) and lowercase (Python backend) keys
  const chartData = data[type] || data[type.toLowerCase()];

  if (!chartData) {
     return <div className="flex h-full w-full items-center justify-center text-term-red text-sm italic">Chart data for {type} not found in backend response.</div>;
  }

  const layoutTemplate = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#9ca3af", family: "monospace", size: 12 }, // Increased font size here too
    margin: { t: 10, r: 10, b: 25, l: 40 },
    xaxis: { 
      gridcolor: "#374151", 
      zerolinecolor: "#4b5563",
      tickfont: { color: "#d97706" }
    },
    yaxis: { 
      gridcolor: "#374151", 
      zerolinecolor: "#4b5563",
      tickfont: { color: "#d97706" }
    },
    showlegend: false,
    hovermode: "closest",
    autosize: true
  };

  return (
    <div className="absolute inset-0 w-full h-full">
      <Plot
        data={chartData.data}
        layout={{ ...layoutTemplate, ...chartData.layout }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler={true}
      />
    </div>
  );
}