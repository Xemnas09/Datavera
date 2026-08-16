"use client";

import React from "react";
import ReactECharts from "echarts-for-react";

interface EChartViewerProps {
  options: Record<string, any>;
  height?: string;
}

export const EChartViewer: React.FC<EChartViewerProps> = ({
  options,
  height = "380px",
}) => {
  if (!options) return null;

  return (
    <div className="w-full bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
      <ReactECharts
        option={options}
        style={{ height, width: "100%" }}
        opts={{ renderer: "canvas" }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
};
