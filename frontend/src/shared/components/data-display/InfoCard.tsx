import type { ReactNode } from "react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";

interface InfoCardProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

/** Card de conteúdo simples (título + descrição + corpo) — para blocos informativos genéricos, não uma métrica (ver `StatCard`). */
export function InfoCard({ title, description, children, className }: InfoCardProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
