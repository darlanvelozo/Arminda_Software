/**
 * EmConstrucaoPage — placeholder para áreas que entram na Onda 1.3b.
 */

import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function EmConstrucaoPage({ area }: { area: string }) {
  return (
    <div className="max-w-xl mx-auto pt-8">
      <Card>
        <CardHeader>
          <CardTitle>{area}</CardTitle>
          <CardDescription>
            Esta área está em construção. Será entregue na próxima onda do Bloco 1.3.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild variant="outline">
            <Link to="/">Voltar ao dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
