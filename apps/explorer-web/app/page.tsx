import Link from "next/link";
import {
  ArrowRight,
  Activity,
  BookOpen,
  Database,
  GitBranch,
  MessagesSquare,
} from "lucide-react";
import { registry, VERTICALS } from "@/lib/registry";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const VERTICAL_TAGLINES: Record<string, string> = {
  BFSI: "Payments, cards, lending, capital markets, AML, treasury.",
  Insurance: "Underwriting, claims, policy admin, reinsurance, actuarial.",
  Retail: "Stores, ecommerce, returns, last-mile, dark stores.",
  RCG: "Pricing, supply chain, loyalty across consumer goods.",
  CPG: "Demand, trade promotion, brand, retail execution.",
  TTH: "Airlines, hotels, ride-share, rentals, ground ops.",
  Manufacturing: "Shop floor, MES, BOM, supply chain visibility.",
  LifeSciences: "Trials, pharmacovigilance, medical devices, supply chain.",
  Healthcare: "EHR, revenue cycle, telehealth, imaging, engagement.",
  Telecom: "Network ops, BSS/OSS, billing, churn, 5G slicing, QoE.",
  Media: "Ad tech, programmatic, content metadata, SaaS metrics.",
  Energy: "Grid, trading, EV charging, renewables, carbon accounting.",
  Utilities: "Smart metering, outages, gas, water, asset health.",
  PublicSector: "Benefits, court, tax, transit, emergency response.",
  HiTech: "FinOps, telemetry, marketplaces, EDA, DevRel, yield.",
  ProfessionalServices: "Time, billing, legal matters, audit, knowledge.",
};

export default function HomePage() {
  const reg = registry();
  const counts = new Map<string, number>();
  const kpiCounts = new Map<string, number>();
  for (const s of reg.subdomains) {
    counts.set(s.vertical, (counts.get(s.vertical) ?? 0) + 1);
    kpiCounts.set(s.vertical, (kpiCounts.get(s.vertical) ?? 0) + (s.kpis?.length ?? 0));
  }
  const totalKpis = reg.subdomains.reduce((n, s) => n + (s.kpis?.length ?? 0), 0);
  const totalEntities = reg.subdomains.reduce((n, s) => n + (s.dataModel?.entities?.length ?? 0), 0);

  return (
    <div className="space-y-10">
      {/* Hero band */}
      <section className="rounded-xl border bg-gradient-to-br from-accent/40 via-card to-card p-6 md:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>Deep Dom