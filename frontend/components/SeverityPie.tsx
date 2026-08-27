"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Sector } from "recharts";
import { useState } from "react";
import type { Severity } from "@/lib/types";
import { SEVERITY_COLOR, SEVERITY_LABEL, SEVERITY_DESC, SEVERITY_ORDER } from "@/lib/constants";

interface Props {
  counts: Record<Severity, number>;
  active: Severity | "all";
  onPick: (s: Severity) => void;
}

export function SeverityPie({ counts, active, onPick }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const total = SEVERITY_ORDER.reduce((a, s) => a + (counts[s] || 0), 0);

  const rows = SEVERITY_ORDER.map((s) => ({
    key: s,
    name: SEVERITY_LABEL[s],
    value: counts[s] || 0,
    color: SEVERITY_COLOR[s],
    pct: total > 0 ? ((counts[s] || 0) / total) * 100 : 0,
  }));

  const renderActive = (props: any) => {
    const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props;
    return (
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        stroke="#0d0d0f"
        strokeWidth={2}
      />
    );
  };

  return (
    <div className="pie">
      <div className="pie__chart">
        <ResponsiveContainer width="100%" height={210}>
          <PieChart>
            <Pie
              data={rows}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={58}
              outerRadius={92}
              paddingAngle={2}
              stroke="#0d0d0f"
              strokeWidth={2}
              startAngle={90}
              endAngle={-270}
              activeIndex={hover ?? undefined}
              activeShape={renderActive}
              onMouseEnter={(_, i) => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onClick={(_, i) => onPick(rows[i].key)}
            >
              {rows.map((r) => (
                <Cell
                  key={r.key}
                  fill={r.color}
                  opacity={active === "all" || active === r.key ? 1 : 0.28}
                  cursor="pointer"
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pie__center">
          <div className="pie__total">{total}</div>
          <div className="pie__totlabel">POTHOLES</div>
        </div>
      </div>

      <ul className="legend">
        {rows.map((r) => (
          <li
            key={r.key}
            className={`legend__row ${active === r.key ? "legend__row--on" : ""}`}
            onClick={() => onPick(r.key)}
          >
            <span className="legend__swatch" style={{ background: r.color }} />
            <span className="legend__name">{r.name}</span>
            <span className="legend__desc">{SEVERITY_DESC[r.key]}</span>
            <span className="legend__val">
              {r.value}
              <em>{r.pct.toFixed(0)}%</em>
            </span>
          </li>
        ))}
      </ul>

      <p className="pie__note">
        Severity is an ordinal estimate from a single camera — it fuses
        perspective-corrected pothole size, interior-shadow depth cue, and model
        confidence. Not a metric depth measurement.
      </p>
    </div>
  );
}
