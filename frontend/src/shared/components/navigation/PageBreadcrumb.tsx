import { Fragment } from "react";
import { Link } from "react-router-dom";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/shared/components/ui/breadcrumb";

export interface PageBreadcrumbItem {
  label: string;
  /** Omitido no último item (página atual, não navegável). */
  href?: string;
}

/**
 * Breadcrumb declarativo genérico sobre `ui/breadcrumb.tsx` — para páginas que sabem
 * sua própria trilha estaticamente (ex.: Issue detail: Workspace > Issues > FD-42).
 * Independente do breadcrumb dinâmico de `Topbar.tsx` (que deriva a trilha da URL
 * atual); os dois resolvem casos diferentes e não devem ser unificados à força.
 */
export function PageBreadcrumb({ items }: { items: PageBreadcrumbItem[] }) {
  return (
    <Breadcrumb>
      <BreadcrumbList>
        {items.map((item, index) => (
          <Fragment key={`${item.label}-${index}`}>
            {index > 0 && <BreadcrumbSeparator />}
            <BreadcrumbItem>
              {item.href ? (
                <BreadcrumbLink asChild>
                  <Link to={item.href}>{item.label}</Link>
                </BreadcrumbLink>
              ) : (
                <BreadcrumbPage>{item.label}</BreadcrumbPage>
              )}
            </BreadcrumbItem>
          </Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
