/**
 * ProgramacaoLicencaPremioTab — Onda 3.4.
 *
 * Gestão dos itens de uma folha de licença-prêmio: lista os servidores com
 * meses/dias a indenizar e permite adicionar/remover. Aparece só quando a
 * folha é do tipo "licenca_premio".
 */

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { extractDomainErrorMessage } from "@/lib/api";
import { useVinculosAtivos } from "@/lib/queries/ferias";
import {
  useCreateLpItem,
  useDeleteLpItem,
  useLpItens,
} from "@/lib/queries/licenca-premio";

export function ProgramacaoLicencaPremioTab({ folhaId }: { folhaId: number }) {
  const { data: itens, isLoading } = useLpItens(folhaId);
  const { data: vinculos } = useVinculosAtivos();
  const createItem = useCreateLpItem(folhaId);
  const deleteItem = useDeleteLpItem(folhaId);

  const [vinculo, setVinculo] = useState("");
  const [meses, setMeses] = useState("3");
  const [dias, setDias] = useState("0");

  async function adicionar() {
    if (!vinculo) {
      toast.error("Selecione um servidor.");
      return;
    }
    try {
      await createItem.mutateAsync({
        folha: folhaId,
        vinculo: Number(vinculo),
        meses: Number(meses) || 0,
        dias: Number(dias) || 0,
      });
      toast.success("Servidor adicionado.");
      setVinculo("");
      setMeses("3");
      setDias("0");
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao adicionar.");
    }
  }

  async function remover(id: number) {
    try {
      await deleteItem.mutateAsync(id);
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao remover.");
    }
  }

  const jaProgramados = new Set((itens?.results ?? []).map((i) => i.vinculo));
  const disponiveis = (vinculos?.results ?? []).filter((v) => !jaProgramados.has(v.id));

  return (
    <div className="space-y-4">
      <div className="rounded-md border bg-card p-3 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[220px]">
          <label className="text-xs text-muted-foreground">Servidor</label>
          <Select value={vinculo} onValueChange={setVinculo} disabled={createItem.isPending}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione…" />
            </SelectTrigger>
            <SelectContent>
              {disponiveis.map((v) => (
                <SelectItem key={v.id} value={String(v.id)}>
                  {v.servidor_nome} · {v.cargo_nome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-24">
          <label className="text-xs text-muted-foreground">Meses</label>
          <Input
            type="number"
            min={0}
            value={meses}
            onChange={(e) => setMeses(e.target.value)}
            disabled={createItem.isPending}
          />
        </div>
        <div className="w-24">
          <label className="text-xs text-muted-foreground">Dias</label>
          <Input
            type="number"
            min={0}
            max={29}
            value={dias}
            onChange={(e) => setDias(e.target.value)}
            disabled={createItem.isPending}
          />
        </div>
        <Button onClick={adicionar} disabled={createItem.isPending}>
          Adicionar
        </Button>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Servidor</TableHead>
              <TableHead>Cargo</TableHead>
              <TableHead className="text-right">Meses</TableHead>
              <TableHead className="text-right">Dias</TableHead>
              <TableHead className="text-right">Ação</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                  Carregando…
                </TableCell>
              </TableRow>
            )}
            {!isLoading && (itens?.results.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                  Nenhum servidor programado. Adicione acima e depois calcule a folha.
                </TableCell>
              </TableRow>
            )}
            {itens?.results.map((i) => (
              <TableRow key={i.id}>
                <TableCell>
                  <div className="flex flex-col">
                    <span className="text-sm">{i.servidor_nome}</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      {i.servidor_matricula}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-sm">{i.cargo ?? "—"}</TableCell>
                <TableCell className="text-right font-mono text-sm">{i.meses}</TableCell>
                <TableCell className="text-right font-mono text-sm">{i.dias}</TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-destructive"
                    onClick={() => i.id && remover(i.id)}
                    disabled={deleteItem.isPending}
                  >
                    Remover
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
