/**
 * DocumentoUploadSheet — Bloco 1.5.
 *
 * Sheet para upload de documento digitalizado de um servidor.
 * Aceita PDF e imagens (jpg/png) até 10 MB.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { extractDomainErrorMessage } from "@/lib/api";
import { useUploadDocumento } from "@/lib/queries/documentos";

const TIPOS = [
  { value: "rg", label: "RG" },
  { value: "cpf", label: "CPF" },
  { value: "titulo_eleitor", label: "Título de eleitor" },
  { value: "carteira_trabalho", label: "Carteira de trabalho" },
  { value: "certificado", label: "Certificado/Diploma" },
  { value: "comprovante_residencia", label: "Comprovante de residência" },
  { value: "outro", label: "Outro" },
] as const;

const ACEITOS = ["application/pdf", "image/jpeg", "image/png"];
const MAX_BYTES = 10 * 1024 * 1024;

const schema = z.object({
  tipo: z.enum([
    "rg",
    "cpf",
    "titulo_eleitor",
    "carteira_trabalho",
    "certificado",
    "comprovante_residencia",
    "outro",
  ]),
  descricao: z.string().max(200, "Descrição deve ter no máximo 200 caracteres."),
});

type FormValues = z.infer<typeof schema>;

interface DocumentoUploadSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  servidorId: number;
}

export function DocumentoUploadSheet({
  open,
  onOpenChange,
  servidorId,
}: DocumentoUploadSheetProps) {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [arquivoErro, setArquivoErro] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { tipo: "outro", descricao: "" },
  });

  useEffect(() => {
    if (open) {
      form.reset({ tipo: "outro", descricao: "" });
      setArquivo(null);
      setArquivoErro(null);
      if (inputRef.current) inputRef.current.value = "";
    }
  }, [open, form]);

  const uploadMutation = useUploadDocumento();
  const isSubmitting = uploadMutation.isPending;

  function pickFile(file: File | null) {
    setArquivoErro(null);
    if (!file) {
      setArquivo(null);
      return;
    }
    if (!ACEITOS.includes(file.type)) {
      setArquivoErro("Formato não suportado. Use PDF, JPG ou PNG.");
      setArquivo(null);
      return;
    }
    if (file.size > MAX_BYTES) {
      setArquivoErro("Arquivo maior que 10 MB.");
      setArquivo(null);
      return;
    }
    setArquivo(file);
  }

  async function onSubmit(values: FormValues) {
    if (!arquivo) {
      setArquivoErro("Selecione um arquivo.");
      return;
    }
    try {
      await uploadMutation.mutateAsync({
        servidor: servidorId,
        tipo: values.tipo,
        descricao: values.descricao,
        arquivo,
      });
      toast.success("Documento enviado.");
      onOpenChange(false);
    } catch (err) {
      toast.error(extractDomainErrorMessage(err) ?? "Falha no upload.");
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md flex flex-col">
        <SheetHeader>
          <SheetTitle>Enviar documento</SheetTitle>
          <SheetDescription>
            PDF, JPG ou PNG. Tamanho máximo: 10 MB.
          </SheetDescription>
        </SheetHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="mt-6 flex-1 overflow-y-auto space-y-5"
            noValidate
          >
            <FormField
              control={form.control}
              name="tipo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={isSubmitting}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {TIPOS.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="descricao"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Descrição (opcional)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Ex.: RG frente"
                      autoComplete="off"
                      disabled={isSubmitting}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Arquivo</label>
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf,image/jpeg,image/png"
                disabled={isSubmitting}
                onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border file:border-input file:bg-background file:text-sm file:font-medium hover:file:bg-accent file:cursor-pointer"
              />
              {arquivo && (
                <p className="text-xs text-muted-foreground">
                  {arquivo.name} · {Math.round(arquivo.size / 1024)} KB
                </p>
              )}
              {arquivoErro && <p className="text-sm text-destructive">{arquivoErro}</p>}
            </div>

            <SheetFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting || !arquivo}>
                {isSubmitting ? "Enviando..." : "Enviar"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
