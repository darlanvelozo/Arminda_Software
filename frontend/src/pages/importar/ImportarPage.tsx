/**
 * ImportarPage — Onda 1.6b.
 *
 * Upload CSV/XLSX para enriquecer cadastros pré-eSocial em massa.
 * Fluxo:
 *   1. Operador anexa o arquivo.
 *   2. Escolhe identificador (matrícula ou CPF).
 *   3. Clica "Pré-visualizar" → backend faz dry_run e devolve preview.
 *   4. Confere preview; se OK, clica "Aplicar".
 *   5. Resultado: contagem + erros + colunas ignoradas.
 *
 * Não cria servidor novo — só atualiza cadastros existentes.
 */

import { useRef, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  FileSpreadsheet,
  Loader2,
  Upload,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { extractDomainErrorMessage } from "@/lib/api";
import {
  useImportarServidoresCsv,
  type ImportCsvResultado,
} from "@/lib/queries/servidores";

type ColunaIdentificador = "matricula" | "cpf";

export default function ImportarPage() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [coluna, setColuna] = useState<ColunaIdentificador>("matricula");
  const [resultado, setResultado] = useState<ImportCsvResultado | null>(null);
  const [resultadoTipo, setResultadoTipo] = useState<"preview" | "aplicado" | null>(null);

  const importar = useImportarServidoresCsv();

  async function rodar(dryRun: boolean) {
    if (!file) {
      toast.error("Anexe um arquivo CSV ou XLSX primeiro.");
      return;
    }
    try {
      const r = await importar.mutateAsync({
        file,
        colunaIdentificador: coluna,
        dryRun,
      });
      setResultado(r);
      setResultadoTipo(dryRun ? "preview" : "aplicado");
      if (!dryRun) {
        toast.success(`Aplicado: ${r.atualizados} servidor(es) atualizado(s).`);
      }
    } catch (err) {
      toast.error(extractDomainErrorMessage(err) ?? "Falha ao processar o arquivo.");
    }
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
          <FileSpreadsheet className="h-5 w-5 text-muted-foreground" />
          Importar planilha
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Enriquece cadastros de servidores em massa a partir de CSV ou XLSX.
          Não cria servidor novo — só atualiza o que já existe. Use o modo
          pré-visualizar antes de aplicar.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">1. Arquivo</CardTitle>
          <CardDescription>
            Colunas reconhecidas: matricula, cpf, tipo_logradouro, logradouro,
            numero, bairro, cidade, uf, cep, raca, nome_da_mae, nome_do_pai,
            estado_civil, grau_de_instrucao, nacionalidade, pis, email,
            telefone. Colunas desconhecidas são ignoradas (sem erro).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-end gap-3">
            <div className="flex-1">
              <Label className="text-xs">Anexar arquivo</Label>
              <div className="flex items-center gap-2 mt-1">
                <input
                  ref={inputRef}
                  type="file"
                  accept=".csv,.xlsx,.xlsm,text/csv"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="block w-full text-sm file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:bg-muted file:text-foreground hover:file:bg-muted/80"
                />
              </div>
              {file && (
                <p className="text-xs text-muted-foreground mt-1">
                  Selecionado: <strong>{file.name}</strong> ({Math.round(file.size / 1024)} KB)
                </p>
              )}
            </div>
            <div className="sm:w-56">
              <Label className="text-xs">Identificador</Label>
              <Select
                value={coluna}
                onValueChange={(v) => setColuna(v as ColunaIdentificador)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="matricula">Matrícula</SelectItem>
                  <SelectItem value="cpf">CPF</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-2 border-t pt-4">
            <Button
              variant="outline"
              disabled={!file || importar.isPending}
              onClick={() => rodar(true)}
              className="flex-1"
            >
              {importar.isPending && resultadoTipo !== "aplicado" ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Upload className="h-4 w-4 mr-1" />
              )}
              Pré-visualizar (não aplica)
            </Button>
            <Button
              disabled={!file || !resultado || resultadoTipo === "aplicado" || importar.isPending}
              onClick={() => rodar(false)}
              className="flex-1"
            >
              {importar.isPending && resultadoTipo === "preview" ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <ArrowRight className="h-4 w-4 mr-1" />
              )}
              Aplicar de verdade
            </Button>
          </div>
        </CardContent>
      </Card>

      {resultado && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base inline-flex items-center gap-2">
              {resultadoTipo === "aplicado" ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  Importação aplicada
                </>
              ) : (
                <>
                  <Upload className="h-5 w-5 text-amber-500" />
                  Pré-visualização (nada aplicado ainda)
                </>
              )}
            </CardTitle>
            <CardDescription>
              {resultado.total_linhas} linha{resultado.total_linhas === 1 ? "" : "s"}
              {" · "}
              <strong className="text-foreground">{resultado.atualizados}</strong> com mudança
              {" · "}
              {resultado.ignorados_servidor_nao_encontrado} servidor(es) não encontrado(s)
              {" · "}
              {resultado.ignorados_sem_mudanca} sem alteração
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {resultado.colunas_aceitas_mapeadas.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-xs text-muted-foreground mr-1">Reconhecidas:</span>
                {resultado.colunas_aceitas_mapeadas.map((c) => (
                  <Badge key={c} variant="success">
                    {c}
                  </Badge>
                ))}
              </div>
            )}

            {resultado.colunas_ignoradas.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-xs text-muted-foreground mr-1">Ignoradas:</span>
                {resultado.colunas_ignoradas.map((c) => (
                  <Badge key={c} variant="muted">
                    {c}
                  </Badge>
                ))}
              </div>
            )}

            {resultado.erros.length > 0 && (
              <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm space-y-1">
                <div className="inline-flex items-center gap-2 text-destructive font-medium">
                  <AlertCircle className="h-4 w-4" />
                  {resultado.erros.length} erro{resultado.erros.length === 1 ? "" : "s"}
                </div>
                <ul className="text-xs space-y-1 text-destructive/90 list-disc pl-5">
                  {resultado.erros.slice(0, 10).map((e, i) => (
                    <li key={i}>
                      Linha {e.linha}: {e.mensagem}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {resultado.preview.length > 0 && (
              <div className="rounded-md border bg-card overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[80px]">Linha</TableHead>
                      <TableHead className="w-[140px]">Identificador</TableHead>
                      <TableHead>Mudanças</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {resultado.preview.map((p) => (
                      <TableRow key={p.linha}>
                        <TableCell className="font-mono text-xs tabular-nums">
                          {p.linha}
                        </TableCell>
                        <TableCell className="font-mono text-xs">{p.identificador}</TableCell>
                        <TableCell>
                          <div className="space-y-0.5">
                            {Object.keys(p.depois).map((campo) => (
                              <div key={campo} className="text-xs">
                                <span className="font-mono text-muted-foreground">{campo}:</span>{" "}
                                <span className="line-through text-muted-foreground">
                                  {String(p.antes[campo] ?? "—")}
                                </span>{" "}
                                <ArrowRight className="inline h-3 w-3 mx-0.5" />{" "}
                                <strong>{String(p.depois[campo])}</strong>
                              </div>
                            ))}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {resultado.preview.length === 50 && (
                  <p className="text-xs text-muted-foreground px-3 py-2 border-t">
                    Mostrando os primeiros 50 — total de mudanças: {resultado.atualizados}.
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
