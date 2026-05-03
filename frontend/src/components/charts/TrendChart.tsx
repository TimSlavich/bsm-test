import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTranslation } from "react-i18next";

import { EmptyState } from "../ui";
import { CATEGORY_COLOR, CATEGORY_ORDER, categoryI18nKey } from "../../lib/categories";
import type { TrendPoint } from "../../lib/api";

interface TrendChartProps {
  data: TrendPoint[];
}

export function TrendChart({ data }: TrendChartProps) {
  const { t } = useTranslation();

  if (data.length < 2) {
    return (
      <EmptyState
        title={t("charts.trend.empty_title")}
        description={
          <>
            {t("charts.trend.empty_hint")}
            <br />
            <code>uv run seed-history --days 7</code>
          </>
        }
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: -10 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--text-muted)" }} stroke="var(--border)" />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--text-muted)" }}
          stroke="var(--border)"
          unit="%"
          domain={[0, 100]}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            background: "var(--card-elevated)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" iconSize={8} />
        {CATEGORY_ORDER.map((c) => (
          <Area
            key={c}
            type="monotone"
            stackId="1"
            dataKey={c}
            name={t(categoryI18nKey(c))}
            stroke={CATEGORY_COLOR[c]}
            fill={CATEGORY_COLOR[c]}
            fillOpacity={0.55}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
