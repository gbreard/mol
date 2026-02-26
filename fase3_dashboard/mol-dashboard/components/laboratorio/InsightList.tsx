import React from "react";

export const InsightList = ({ children }: { children: React.ReactNode }) => (
  <ul className="space-y-3 list-none">{children}</ul>
);

export const InsightItem = ({
  text,
  highlight,
}: {
  text: string;
  highlight?: boolean;
}) => (
  <li
    className={`flex items-start gap-3 transition-all duration-200 ${highlight ? "font-semibold" : ""}`}
  >
    <span
      className={`mt-1.5 h-1.5 w-1.5 rounded-full flex-shrink-0 ${highlight ? "bg-amber-600" : "bg-gray-400"}`}
    />
    <p
      className={`text-sm leading-relaxed flex-1 ${highlight ? "text-gray-900" : "text-gray-700"}`}
    >
      {text}
    </p>
  </li>
);
