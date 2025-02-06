from django.db import models
from django.core.exceptions import ValidationError

class Empresa(models.Model):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=14,unique=True)

    def __str__(self):
        return f"{self.nome} - {self.cnpj}"

class PER(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='per_docs')
    versao_perdcomp = models.CharField(max_length=10, blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    numero_perdcomp = models.CharField(max_length=50, unique=True)
    nome_empresarial = models.CharField(max_length=255, blank=True, null=True)
    data_criacao = models.DateField(blank=True, null=True)
    data_transmissao = models.DateField(blank=True, null=True)
    tipo_documento = models.CharField(max_length=50, blank=True, null=True)
    tipo_credito = models.CharField(max_length=50, blank=True, null=True)
    perdcomp_retificador = models.CharField(max_length=50, blank=True, null=True)
    numero_perdcomp_retificador = models.CharField(max_length=50,blank=True,null=True)
    credito_oriundo_de_acao_judicial = models.CharField(max_length=50, blank=True, null=True)
    tipo_da_conta = models.CharField(max_length=50, blank=True, null=True)
    banco = models.CharField(max_length=50, blank=True, null=True)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=20, blank=True, null=True)
    qualificacao = models.CharField(max_length=255, blank=True, null=True)
    pessoa_juridica_extinta_por_liquidacao_voluntaria = models.CharField(max_length=50, blank=True, null=True)
    nome_responsavel_da_pessoa_juridica_perante_rfb = models.CharField(max_length=255, blank=True, null=True)
    cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = models.CharField(max_length=20, blank=True, null=True)
    nome_responsavel_pelo_preechimento = models.CharField(max_length=255, blank=True, null=True)
    cpf_do_responsavel_pelo_preenchimento = models.CharField(max_length=20, blank=True, null=True)
    informado_em_processo_admistrativo_anterior = models.CharField(max_length=50, blank=True, null=True)
    informado_em_outro_perdcomp = models.CharField(max_length=50, blank=True, null=True)
    situacao_especial_do_titular_credito = models.CharField(max_length=50, blank=True, null=True)
    credito_sucedido = models.CharField(max_length=50, blank=True, null=True)
    valor_original_do_credito_inicial = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    credito_original = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_do_pedido_restituicao = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    periodo_de_apuracao_origem_credito = models.CharField(max_length=50, blank=True, null=True)
    cnpj_do_pagamento_origem_credito = models.CharField(max_length=20, blank=True, null=True)
    codigo_da_receita = models.CharField(max_length=50, blank=True, null=True)
    grupo_do_tributo = models.CharField(max_length=50, blank=True, null=True)
    data_de_arrecadacao = models.DateField(blank=True, null=True)
    valor_do_principal = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_da_multa = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_do_juros = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_total_origem_credito = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    forma_tributacao_lucro = models.CharField(max_length=50, blank=True, null=True)
    forma_apuracao = models.CharField(max_length=50, blank=True, null=True)
    exercicio = models.CharField(max_length=50,blank=True,null=True)
    data_inicial_periodo = models.DateField(blank=True, null=True)
    data_final_periodo = models.DateField(blank=True, null=True)
    imposto_devido = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    total_parcelas_composicao_credito = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_do_saldo_negativo = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    dcomp_inicial = models.ForeignKey('Dcomp', on_delete=models.SET_NULL, null=True, related_name='per_docs')

    def __str__(self):
        return f"PER {self.numero_perdcomp} - {self.nome_empresarial}"

class Dcomp(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='dcomp_docs')
    versao_perdcomp = models.CharField(max_length=10, blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    numero_perdcomp = models.CharField(max_length=50, unique=True)#
    numero_perdcomp_inicial = models.ForeignKey(PER, on_delete=models.SET_NULL, null=True, related_name='dcomp_inicial_docs')
    nome_empresarial = models.CharField(max_length=255, blank=True, null=True)
    data_criacao = models.DateField(blank=True, null=True)
    data_transmissao = models.DateField(blank=True, null=True)
    tipo_documento = models.CharField(max_length=50, blank=True, null=True)
    tipo_credito = models.CharField(max_length=50, blank=True, null=True)
    perdcomp_retificador = models.CharField(max_length=50, blank=True, null=True)
    numero_perdcomp_retificador = models.CharField(max_length=50,blank=True,null=True)
    credito_oriundo_de_acao_judicial = models.BooleanField(default=False)
    qualificacao = models.CharField(max_length=255, blank=True, null=True)
    pessoa_juridica_extinta_por_liquidacao_voluntaria = models.BooleanField(default=False)
    nome_responsavel_da_pessoa_juridica_perante_rfb = models.CharField(max_length=255, blank=True, null=True)
    cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = models.CharField(max_length=20, blank=True, null=True)
    nome_responsavel_pelo_preechimento = models.CharField(max_length=255, blank=True, null=True)
    cpf_do_responsavel_pelo_preenchimento = models.CharField(max_length=20, blank=True, null=True)
    informado_em_processo_admistrativo_anterior = models.BooleanField(default=False)#
    informado_em_outro_perdcomp = models.BooleanField(default=False)#
    situacao_especial_do_titular_credito = models.CharField(max_length=50, blank=True, null=True)
    credito_sucedido = models.BooleanField(default=False)#
    forma_tributacao_lucro = models.CharField(max_length=50,blank=True,null=True)
    forma_apuracao = models.CharField(max_length=50,blank=True,null=True)
    exercicio = models.CharField(max_length=50,blank=True,null=True)
    data_inicial_periodo = models.DateField(blank=True,null=True)
    data_final_periodo = models.DateField(blank=True,null=True)
    selic_acumulada = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)#
    imposto_devido = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True)
    total_parcelas_composicao_credito = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True)
    valor_saldo_negativo = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True)
    valor_original_do_credito_inicial = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    credito_original = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)#
    credito_atualizado = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    total_dos_debitos = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    total_do_credito_original_utilizado_neste_documento = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    saldo_do_credito_original = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    periodo_de_apuracao_origem_credito = models.CharField(max_length=50, blank=True, null=True)
    cnpj_do_pagamento_origem_credito = models.CharField(max_length=20, blank=True, null=True)
    codigo_da_receita = models.CharField(max_length=50, blank=True, null=True)
    grupo_do_tributo = models.CharField(max_length=50, blank=True, null=True)
    data_de_arrecadacao = models.DateField(blank=True, null=True)
    valor_do_principal = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_da_multa = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_do_juros = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_total_origem_credito = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    debitos = models.ManyToManyField('DcompDebitos', related_name='dcomp_docs')

    def __str__(self):
        return f"DCOMP {self.numero_perdcomp} - {self.nome_empresarial}"

class DcompDebitos(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='debitos_docs')
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    numero_dcomp = models.CharField(max_length=50)
    nome_empresarial = models.CharField(max_length=255, blank=True, null=True)
    grupo_tributo = models.CharField(max_length=255, blank=True, null=True)
    codigo_da_receita_denominacao = models.CharField(max_length=255, blank=True, null=True)
    periodo_da_apuracao = models.CharField(max_length=50, blank=True, null=True)
    periodicidade = models.CharField(max_length=50, blank=True, null=True)
    data_de_vencimento_do_tributo_quota = models.DateField(blank=True, null=True)
    periocidade_dctf_web = models.CharField(max_length=50, blank=True, null=True)
    periodo_apuracao_dctfweb = models.CharField(max_length=50, blank=True, null=True)
    valor_principal = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_multa = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_juros = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    valor_total = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['numero_dcomp', 'grupo_tributo', 'codigo_da_receita_denominacao','periodo_da_apuracao'],
                                    name='unique_dcomp_debitos')
        ]

    def __str__(self):
        return f"Débito {self.numero_dcomp} - {self.nome_empresarial}"

class PerCanc(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='canc_docs')
    versao_perdcomp = models.CharField(max_length=10, blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    numero_perdcomp = models.CharField(max_length=50, blank=True, null=True)
    nome_empresarial = models.CharField(max_length=255, blank=True, null=True)
    data_criacao = models.DateField(blank=True, null=True)
    data_transmissao = models.DateField(blank=True, null=True)
    tipo_documento = models.CharField(max_length=50, blank=True, null=True)
    tipo_credito = models.CharField(max_length=50, blank=True, null=True)
    numero_perdcomp_a_cancelar = models.CharField(max_length=50, blank=True, null=True)
    credito_oriundo_de_acao_judicial = models.BooleanField(default=False)
    pessoa_juridica_extinta_por_liquidacao_voluntaria = models.BooleanField(default=False)
    nome_responsavel_da_pessoa_juridica_perante_rfb = models.CharField(max_length=255, blank=True, null=True)
    cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = models.CharField(max_length=20, blank=True, null=True)
    nome_responsavel_pelo_preechimento = models.CharField(max_length=255, blank=True, null=True)
    cpf_do_responsavel_pelo_preenchimento = models.CharField(max_length=20, blank=True, null=True)

    # Relacionamentos opcionais
    per_relacionado = models.ForeignKey(
        PER,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelamentos_per'
    )
    dcomp_relacionado = models.ForeignKey(
        Dcomp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelamentos_dcomp'
    )

    def clean(self):
        """
        Valida que apenas uma das chaves (per_relacionado ou dcomp_relacionado) pode ser preenchida.
        """
        if self.per_relacionado and self.dcomp_relacionado:
            raise ValidationError("Apenas um dos campos 'per_relacionado' ou 'dcomp_relacionado' pode ser preenchido.")
        if not self.per_relacionado and not self.dcomp_relacionado:
            raise ValidationError("Pelo menos um dos campos 'per_relacionado' ou 'dcomp_relacionado' deve ser preenchido.")

    def __str__(self):
        return f"Cancelamento: {self.numero_perdcomp} - {self.nome_empresarial}"





