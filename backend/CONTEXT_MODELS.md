# backend/CONTEXT_MODELS.md — Regras da camada de Models

> Regras para tudo que vive em `apps/<app>/models.py`.
> **Antes de criar/alterar qualquer model, ler este arquivo + [`backend/CONTEXT.md`](CONTEXT.md) + `apps/<app>/CONTEXT.md` (se existir).**

---

## 1. O que models são (e o que não são)

### São
- Estrutura de dados persistida no PostgreSQL.
- Restrições de integridade (constraints, unique, check).
- Querysets/managers customizados (ex: `Servidor.objects.ativos()`).
- Métodos triviais derivados de campos próprios (ex: `def idade(self) -> int`).
- Auditoria via `simple-history` (a partir do Bloco 1).

### Não são
- ❌ Lugar para regra de negócio (ex: cálculo de INSS, aprovação de folha) — vai para `services/`.
- ❌ Lugar para chamadas externas (eSocial, e-mail, fila Celery) — vai para `services/` ou `tasks.py`.
- ❌ Lugar para validação que dependa de outros agregados (ex: "servidor não pode ter dois vínculos do mesmo tipo") — vai para `services/`.

---

## 2. Modelo base

Todo model que represente entidade de domínio com auditoria deve herdar de `apps.core.models.TimeStampedModel`:

```python
from apps.core.models import TimeStampedModel

class Cargo(TimeStampedModel):
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name="cargos")
    codigo = models.CharField(max_length=20)
    # ...
```

Esse modelo abstrato já provê: `criado_em`, `atualizado_em`, `criado_por`, `atualizado_por`. **Não duplique** esses campos.

Modelos puramente técnicos (logs internos, tabelas de cache) podem herdar de `models.Model` direto.

---

## 3. Convenções de nomenclatura

### Classe
- **PascalCase**, singular, em **português** quando termo de domínio brasileiro: `Servidor`, `Cargo`, `Lotacao`, `VinculoFuncional`, `Rubrica`, `Folha`, `Lancamento`.
- **Sem acentos** no nome da classe (limitação histórica respeitada — `Lotacao` e não `Lotação`).

### Campos
- **snake_case** sempre.
- **Domínio brasileiro:** `cpf`, `pis_pasep`, `competencia`, `data_admissao`, `salario_base`. **Manter consistência com models existentes.**
- **Booleans** começam com substantivo descritivo: `ativo`, `incide_inss`, **não** `is_active`/`has_incidencia`. Convenção do projeto.
- **Datas** usam `data_<algo>` (`data_nascimento`, `data_admissao`, `data_demissao`).
- **Decimais financeiros:** sempre `DecimalField(max_digits=N, decimal_places=2)` — **nunca** `FloatField`.

### `verbose_name` e `verbose_name_plural`
- Sempre em português, minúsculo, sem acento (consistente com base existente):
  ```python
  class Meta:
      verbose_name = "servidor"
      verbose_name_plural = "servidores"
  ```

### `related_name`
- Plural do nome do model que aponta, em **português**: `related_name="vinculos"`, `related_name="lancamentos"`. Já adotado.
- Sempre explícito. Sem `related_name` o Django gera nomes ruins.

---

## 4. ForeignKeys e relacionamentos

### `on_delete` — escolha consciente
- `CASCADE` — quando o filho não tem sentido sem o pai (ex: `Lancamento` sem `Folha`). Usado em quase todos os FK para `Municipio` (excluir tenant remove tudo).
- `PROTECT` — quando exclusão do pai deve ser bloqueada para preservar histórico (ex: `Lancamento.servidor` — apagar servidor que tem lançamento é proibido).
- `SET_NULL` — auditoria (ex: `criado_por` permite que o usuário seja deletado sem apagar o histórico).

**Regra:** revisar caso a caso, **nunca** padrão preguiçoso.

### Multi-tenant
Todo model **tenant** (não-shared) tem FK para `Municipio`:
```python
municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name="<plural>")
```
A partir do Bloco 1, com `django-tenants` ativo, o filtro por `municipio` será **implícito** via `search_path`. Antes disso (e em código administrativo), filtrar **explicitamente**.

### Unique constraints multi-tenant
Toda unicidade de domínio é **por tenant**, não global:
```python
class Meta:
    unique_together = [("municipio", "codigo")]
    # ou (Django 5+):
    constraints = [
        models.UniqueConstraint(fields=["municipio", "codigo"], name="cargo_codigo_por_municipio"),
    ]
```

---

## 5. Choices

- Definir como **list of tuples** ou **TextChoices** (preferível em código novo):
```python
class Regime(models.TextChoices):
    ESTATUTARIO = "estatutario", "Estatutário"
    CELETISTA = "celetista", "Celetista"
    COMISSIONADO = "comissionado", "Comissionado"
    TEMPORARIO = "temporario", "Temporário"
    ESTAGIARIO = "estagiario", "Estagiário"

class VinculoFuncional(TimeStampedModel):
    regime = models.CharField(max_length=30, choices=Regime.choices)
```

- **Códigos em snake_case sem acento** (`"estatutario"`); **labels com acento** (`"Estatutário"`).
- Migrar gradualmente os models existentes para `TextChoices` quando tocar neles. **Não** fazer um refactor big-bang.

---

## 6. Decimais e dinheiro

> **Folha de pagamento é financeiro. Tolerância zero para erro de arredondamento.**

- **Sempre `DecimalField`**, nunca `FloatField`.
- Padrão de armazenamento: `max_digits=12, decimal_places=2` para valores monetários até R$ 9.999.999.999,99.
- Padrão para totais agregados: `max_digits=14, decimal_places=2`.
- Padrão para referências/quantidades/percentuais: `max_digits=10, decimal_places=4` (já usado em `Lancamento.referencia`).

### Cálculo
- Em código Python, importar `from decimal import Decimal, ROUND_HALF_EVEN`.
- **Não** misturar `Decimal` com `float` na mesma expressão.
- Arredondamento **sempre** explícito ao persistir:
  ```python
  valor = (salario * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
  ```
- Regra fiscal específica (ex: arredondamento legal do INSS) fica no service, **documentada** na docstring.

---

## 7. Querysets e managers customizados

Lógica de filtro reutilizável vai em **QuerySet customizado**, não em service:

```python
class ServidorQuerySet(models.QuerySet):
    def ativos(self):
        return self.filter(ativo=True)

    def por_lotacao(self, lotacao):
        return self.filter(vinculos__lotacao=lotacao, vinculos__ativo=True).distinct()


class Servidor(TimeStampedModel):
    # ...
    objects = ServidorQuerySet.as_manager()
```

**Por quê:** queryset customizado é encadeável (`Servidor.objects.ativos().por_lotacao(x)`), service não.

**O que NÃO vai em queryset:** lógica que dependa de objeto não-Django (chamada externa, cálculo financeiro complexo, regra de processo).

---

## 8. Métodos no model

Permitido em models:

```python
class Servidor(TimeStampedModel):
    # ...
    def idade(self) -> int:
        from datetime import date
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    @property
    def vinculo_principal(self) -> "VinculoFuncional | None":
        return self.vinculos.filter(ativo=True).order_by("data_admissao").first()
```

Proibido em models (vai para service):

```python
# ❌ ERRADO — lógica de processo no model
class Servidor(TimeStampedModel):
    def admitir(self, cargo, lotacao, data, ...):
        # cria vínculo, gera evento eSocial S-2200, envia e-mail...
        ...
```

→ correto: `apps.people.services.admissao.admitir_servidor(...)`.

---

## 9. `__str__`

- Sempre implementar.
- Curto, identificador (matrícula, código, nome), em texto plano.
- Padrão atual: `f"{self.matricula} - {self.nome}"` ou `f"{self.codigo} - {self.nome}"`.

---

## 10. Validação

### No model (light)
- `MinValueValidator`, `MaxValueValidator`, `RegexValidator`.
- `unique_together`, `UniqueConstraint`, `CheckConstraint`.
- `clean()` para validação que envolve **só campos próprios** do model.

### No service (heavy)
- Validação cross-objeto, regra de negócio, validação que dependa de estado externo.

### Não confiar só no `clean()`
- `clean()` **não** é chamado automaticamente em `save()`. Se quiser garantir, chamar `full_clean()` antes de salvar — ou validar no service.
- DRF Serializer roda validação separadamente; serializer é fronteira HTTP, **não** substitui regra de negócio.

---

## 11. Migrations

- Geradas com nome descritivo: `python manage.py makemigrations people --name adiciona_cbo_em_cargo`.
- Revisar **a migration gerada** antes de commitar — Django às vezes gera `AlterField` desnecessário.
- **Backfill de dados** em migration separada (data migration), não acoplada à structural.
- Migration que muda tipo/renomeia coluna: plano de rollback no PR + marcador **⚠ BREAKING** no `CHANGELOG.md`.

```python
# data migration exemplo
from django.db import migrations

def preencher_cbo_padrao(apps, schema_editor):
    Cargo = apps.get_model("people", "Cargo")
    Cargo.objects.filter(cbo="").update(cbo="9999-99")

def reverter(apps, schema_editor):
    pass  # backfill é idempotente; reversão é no-op

class Migration(migrations.Migration):
    dependencies = [("people", "0002_adiciona_cbo_em_cargo")]
    operations = [migrations.RunPython(preencher_cbo_padrao, reverter)]
```

---

## 12. Auditoria (simple-history) — Bloco 1+

A ativar quando descomentarmos `simple_history` em `INSTALLED_APPS` e middleware. Padrão:

```python
from simple_history.models import HistoricalRecords

class Servidor(TimeStampedModel):
    # ...
    history = HistoricalRecords(excluded_fields=["atualizado_em"])
```

- Apenas em models de domínio com mudanças relevantes (não em `Lancamento`, que é gerado por cálculo — usar versionamento de `Folha`).
- `excluded_fields` evita ruído de timestamps automáticos.

---

## 13. Models existentes — referência

Já implementados no Bloco 0:

| App | Models |
|-----|--------|
| `core` | `TimeStampedModel` (abstrato), `Municipio`, `ConfiguracaoGlobal` |
| `people` | `Cargo`, `Lotacao`, `Servidor`, `VinculoFuncional`, `Dependente`, `Documento` |
| `payroll` | `Rubrica`, `Folha`, `Lancamento` |
| `reports` | `RelatorioGerado` |

**Antes de criar um model novo, verifique se já existe.** Antes de mexer em um existente, consulte o `CHANGELOG.md` para entender o histórico.

---

## 14. Checklist antes de commitar mudança em model

- [ ] `CharField`/`DecimalField` com tamanhos/precisão definidos.
- [ ] FK com `on_delete` consciente e `related_name` em português plural.
- [ ] `Meta` com `ordering`, `verbose_name`, `verbose_name_plural`.
- [ ] `unique_together` ou `UniqueConstraint` por tenant onde aplicável.
- [ ] `__str__` implementado.
- [ ] Migration gerada com nome descritivo e revisada.
- [ ] Teste de model em `apps/<app>/tests/test_models.py`.
- [ ] Entrada no `CHANGELOG.md`.
- [ ] `ruff check .` verde.
