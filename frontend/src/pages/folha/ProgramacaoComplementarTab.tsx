/**
 * ProgramacaoComplementarTab — Onda 3.5 (ADR-0019).
 *
 * Lançamentos explícitos de uma folha complementar: o operador escolhe o
 * servidor, a rubrica (provento ou desconto) e informa o valor à mão. Sem
 * incidência automática (ver ADR-0019). Aparece só quando a folha é do tipo
 * "complementar".
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
import {
  useComplementarItens,
  useCreateComplementarItem,
  useDeleteComplementarItem,
} from "@/lib/queries/complementar";
import { useVinculosAtivos } from "@/lib/queries/ferias";
import { useRubricasList } from "@/lib/queries/rubricas";

export function ProgramacaoComplementarTab({ folhaId }: { folhaId: number }) {
  const { data: itens, isLoading } = useComplementarItens(folhaId);
  const { data: vinculos } = useVinculosAtivos();
  const { data: rubricas } = useRubricasList({ ativo: true, ordering: "codigo" });
  const createItem = useCreateComplementarItem(folhaId);
  const deleteItem = useDeleteComplementarItem(folhaId);

  const [vinculo, setVinculo] = useState("");
  const [rubrica, setRubrica] = useState("");
  const [valor, setValor] = useState("");

  async function adicionar() {
    if (!vinculo || !rubrica) {
      toast.error("Selecione o servidor e a rubrica.");
      return;
    }
    if (!valor || Number(valor) <= 0) {
      toast.error("Informe um valor maior que zero.");
      return;
    }
    try {
      await createItem.mutateAsync({
        folha: folhaId,
        vinculo: Number(vinculo),
        rubrica: Number(rubrica),
        valor: Number(valor).toFixed(2),
      });
      toast.success("Lançamento adicionado.");
      setValor("");
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

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Folha complementar paga diferenças da competência com valores informados
        à mão. Não há incidência automática — se houver INSS/IRRF complementar,
        lance-o como desconto explícito.
      </p>

      <div className="rounded-md border bg-card p-3 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-muted-foreground">Servidor</label>
          <Select value={vinculo} onValueChange={setVinculo} disabled={createItem.isPending}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione…" />
            </SelectTrigger>
            <SelectContent>
              {(vinculos?.results ?? []).map((v) => (
                <SelectItem key={v.id} value={String(v.id)}>
                  {v.servidor_nome} · {v.cargo_nome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-muted-foreground">Rubrica</label>
          <Select value={rubrica} onValueChange={setRubrica} disabled={createItem.isPending}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione…" />
            </SelectTrigger>
            <SelectContent>
              {(rubricas?.results ?? []).map((r) => (
                <SelectItem key={r.id} value={String(r.id)}>
                  {r.codigo} · {r.nome} ({r.tipo})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-32">
          <label className="text-xs text-muted-foreground">Valor (R$)</label>
          <Input
            type="number"
            min={0}
            step="0.01"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
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
              <TableHead>Rubrica</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead className="text-right">Valor</TableHead>
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
                  Nenhum lançamento. Adicione acima e depois calcule a folha.
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
                <TableCell className="text-sm">
                  <span className="font-mono text-xs">{i.rubrica_codigo}</span> · {i.rubrica_nome}
                </TableCell>
                <TableCell className="text-sm">{i.rubrica_tipo}</TableCell>
                <TableCell className="text-right font-mono text-sm">{i.valor}</TableCell>
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
