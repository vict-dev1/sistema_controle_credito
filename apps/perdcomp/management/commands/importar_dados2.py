from django.core.management.base import BaseCommand
from perdcomp.models import Dcomp, Empresa, PER, PerCanc
import fitz
import os
import re
from datetime import datetime
from decimal import Decimal


class Command(BaseCommand):
    help = "Importa informações de PDFS de Dcomp e salva no banco de dados."

    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            required=True,
            help="Caminho do diretório contendo os arquivos PDF para processamento."
        )

    def read_pdf(self, file_path):
        try:
            document = fitz.open(file_path)
            pdf_text = ""
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                pdf_text += page.get_text()
            return pdf_text
        except Exception as e:
            self.stderr.write(f"Erro ao ler o PDF '{file_path}': {str(e)}")
            return None

    def read_pdfs_in_directory(self, directory_path):
        all_text = []
        try:
            for filename in os.listdir(directory_path):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(directory_path, filename)
                    self.stdout.write(f"Lendo arquivo: {file_path}")
                    pdf_text = self.read_pdf(file_path)
                    if pdf_text:
                        all_text.append(pdf_text)
            return all_text
        except Exception as e:
            self.stderr.write(f"Erro ao processar o diretório '{directory_path}': {str(e)}")
            return []

    def converter_data(self, data_str):
        # Verificar se o argumento é None ou não é uma string
        if not data_str:
            print("Erro: Nenhuma data foi fornecida (valor é None ou vazio).")
            return None

        # Tentativa de conversão da string de data
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            print(f"Erro ao converter a data. Formato inválido: '{data_str}'. Esperado: DD/MM/AAAA.")
            return None

    def converter_valor(self, valor_str):
        if valor_str is None:
            self.stderr.write("Erro: valor_str é None.")
            return None

        try:
            # Verifica se o valor é uma string antes de aplicar transformações
            if isinstance(valor_str, str):
                # Remove o símbolo % caso exista
                if '%' in valor_str:
                    valor_str = valor_str.replace('%', '')

                # Substitui pontos e vírgulas para o formato correto
                valor_str = valor_str.replace('.', '').replace(',', '.')

            # Converte para Decimal, independente se era string ou não
            return Decimal(valor_str)

        except Exception as e:
            self.stderr.write(f"Erro ao processar Declaração de Compensação Saldo Negativo de IRPJ: {str(e)}")
            self.stderr.write(f"Variável que causou o erro: valor_str com valor: {valor_str}")
            raise  # Re-levanta a exceção para não continuar com o erro.

    def converter_para_booleano(self, valor_str):
        # Verificar se o valor é None ou vazio
        if not valor_str:
            return None  # Retorna None se o valor for None ou vazio

        # Garantir que o valor é uma string antes de chamar strip() e lower()
        valor_str = str(valor_str).strip().lower()

        if valor_str in ['sim', 'yes', 'true', 'Sim', 'SIM']:
            return True
        elif valor_str in ['não', 'no', 'false', 'Não', 'NÃO']:
            return False
        else:
            return None

    def identificar_tipo_documento(self, texto):
        # Primeiro verifica se o documento é do tipo "Pedido de Restituição, Ressarcimento ou Reembolso e Declaração de Compensação"
        if "PEDIDO DE RESTITUIÇÃO, RESSARCIMENTO OU REEMBOLSO E DECLARAÇÃO DE COMPENSAÇÃO" in texto:
            # Classifica dentro do contexto de "Pedido de Restituição e Declaração de Compensação"
            if "Pedido de Restituição" in texto:
                return "Pedido de Restituição"

            elif "Pedido de Cancelamento" in texto:
                return "Pedido de Cancelamento"

            elif "Declaração de Compensação" in texto:
                return "Declaração de Compensação"
            else:
                return "Tipo Específico Não Identificado"
        return "Documento Não Reconhecido"

    def identificar_tipo_credito(self,texto):
        if "Saldo Negativo de IRPJ" in texto:
            return "Saldo Negativo de IRPJ"
        elif "Saldo Negativo de CSLL" in texto:
            return "Saldo Negativo de CSLL"
        elif "Pagamento Indevido ou a Maior" in texto:
            return "Pagamento Indevido ou a Maior"

        return "Crédito Desconhecido"

    def handle(self, *args, **options):
        directory_path = options['directory']

        if not os.path.exists(directory_path):
            self.stderr.write(f"Erro: O diretório especificado '{directory_path}' não existe.")
            return

        textos = self.read_pdfs_in_directory(directory_path)

        if not textos:
            self.stdout.write("Nenhum texto extraído dos PDFs. Verifique os arquivos no diretório.")
            return

        # Separar textos por tipo de documento e tipo de crédito

        #PER
        pedidos_restituicao_pagamento_indevido_ou_maior = []
        pedidos_restituicao_saldo_negativo_csll = []
        pedidos_restituicao_saldo_negativo_irpj = []

        #DCOMP
        declaracoes_compensacao_pagamento_indevido_ou_maior = []
        declaracoes_compensacao_saldo_negativo_irpj = []
        declaracoes_compensacao_saldo_negativo_csll = []

        #Pedido de cancelamento
        pedido_cancelamento = []

        for texto in textos:
            tipo_documento = self.identificar_tipo_documento(texto)
            tipo_credito = self.identificar_tipo_credito(texto)

            if tipo_documento == "Pedido de Restituição":

                if tipo_credito == "Saldo Negativo de IRPJ":
                    pedidos_restituicao_saldo_negativo_irpj.append(texto)

                elif tipo_credito == "Saldo Negativo de CSLL":
                    pedidos_restituicao_saldo_negativo_csll.append(texto)

                elif tipo_credito == "Pagamento Indevido ou a Maior":
                    pedidos_restituicao_pagamento_indevido_ou_maior.append(texto)

            elif tipo_documento == "Declaração de Compensação":
                if tipo_credito == "Pagamento Indevido ou a Maior":
                    declaracoes_compensacao_pagamento_indevido_ou_maior.append(texto)

                elif tipo_credito == "Saldo Negativo de IRPJ":
                    declaracoes_compensacao_saldo_negativo_irpj.append(texto)

                elif tipo_credito == "Saldo Negativo de CSLL":
                    declaracoes_compensacao_saldo_negativo_csll.append(texto)

            elif tipo_documento == "Pedido de Cancelamento":
                pedido_cancelamento.append(texto)

        self.stderr.write(
            f"dcomp pagamento indevido a maior:{len(declaracoes_compensacao_pagamento_indevido_ou_maior)}"
        )
        self.stderr.write(
            f"dcomp saldo negativo csll:{len(declaracoes_compensacao_saldo_negativo_csll)}"
        )
        self.stderr.write(
            f"dcomp saldo negativo irpj: {len(declaracoes_compensacao_saldo_negativo_irpj)}.")

        self.stderr.write(
            f"per pagamento indevido ou a maior: {len(pedidos_restituicao_pagamento_indevido_ou_maior)}.")

        self.stderr.write(
            f"per saldo negativo irpj:{len(pedidos_restituicao_saldo_negativo_irpj)}"
        )
        self.stderr.write(
            f"per saldo negativo csll:{len(pedidos_restituicao_saldo_negativo_csll)}"
        )
        self.stderr.write(
            f"pedido de cancelamento:{len(pedido_cancelamento)}"
        )

        # Processar "Pedido de Restituição - pagamento indevido ou a maior"
        for texto in pedidos_restituicao_pagamento_indevido_ou_maior:
            self.processar_pedido_restituicao(texto)

        # Processar pedido restituicao_saldo_negativo_irpj
        for texto in pedidos_restituicao_saldo_negativo_irpj:
            self.processar_pedido_restituicao_saldo_negativo_irpj(texto)

        # Processar Pedido Restituição Saldo Negativo CSLL
        for texto in pedidos_restituicao_saldo_negativo_csll:
            self.processar_pedido_restituicao_saldo_negativo_csll(texto)

        # Processar "Declaração de Compensação - pagamento indevido ou a maior"
        for texto in declaracoes_compensacao_pagamento_indevido_ou_maior:
            self.processar_declaracao_compensacao(texto)

        #Processar "Declaração de Compensação - Saldo Negativo IRPJ"
        for texto in declaracoes_compensacao_saldo_negativo_irpj:
            self.processar_declaracao_compensacao_saldo_negativo_irpj(texto)

        # Processar "Declaração de Compensação - Saldo Negativo CSLL"
        for texto in declaracoes_compensacao_saldo_negativo_csll:
            self.processar_declaracao_compensacao_saldo_negativo_csll(texto)

        for texto in pedido_cancelamento:
            self.processar_pedido_cancelamento(texto)

    def processar_pedido_restituicao(self, texto):
        try:
            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # CNPJ
            cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()  # Remove formatações

            # Número da perdcomp
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Nome empresariaL
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            if not cnpj or not perdcomp_number:
                self.stderr.write("Erro: CNPJ ou Número de PER não encontrados no texto.")
                return

            # Verificar se a empresa já existe no banco
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )

            if created:
                self.stdout.write(f"Empresa criada: {empresa}")
            else:
                self.stdout.write(f"Empresa já existente: {empresa}")

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None
            data_de_criacao = self.converter_data(data_de_criacao)

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None
            data_de_transmissao = self.converter_data(data_de_transmissao)

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_retificador_match = re.search(r'PER/DCOMP Retificador\n([^\n]+)', texto)
            perdcomp_retificador = perdcomp_retificador_match.group(1) if perdcomp_retificador_match else None
            perdcomp_retificador = self.converter_para_booleano(perdcomp_retificador)

            # Número PER/DCOMP Retificador

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)', texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None
            credito_oriundo_de_acao_judicial = self.converter_para_booleano(credito_oriundo_de_acao_judicial)

            # Tipo de Conta
            tipo_de_conta_match = re.search(r'Tipo da Conta\n([^\n]+)', texto)
            tipo_da_conta = tipo_de_conta_match.group(1) if tipo_de_conta_match else None

            # Banco
            banco_match = re.search(r'Banco\n([^\n]+)', texto)
            banco = banco_match.group(1) if banco_match else None

            # Agência
            agencia_match = re.search(r'Agência\n([^\n]+)', texto)
            agencia = agencia_match.group(1) if agencia_match else None

            # Conta
            conta_match = re.search(r'N° Conta\n([^\n]+)', texto)
            conta = conta_match.group(1) if conta_match else None

            # Qualificação do Contribuinte
            qualificacao_match = re.search(r'Qualificação do Contribuinte\n([^\n]+)', texto)
            qualificacao = qualificacao_match.group(1) if qualificacao_match else None

            # Pessoa Jurídica Extinta por Liquidação Voluntária
            pessoa_juridica_extinta_por_liquidacao_voluntaria_match = re.search(
                r'Pessoa Jurídica Extinta por Liquidação Voluntária\n([^\n]+)', texto)
            pessoa_juridica_extinta_por_liquidacao_voluntaria = pessoa_juridica_extinta_por_liquidacao_voluntaria_match.group(
                1) if pessoa_juridica_extinta_por_liquidacao_voluntaria_match else None
            pessoa_juridica_extinta_por_liquidacao_voluntaria = self.converter_para_booleano(
                pessoa_juridica_extinta_por_liquidacao_voluntaria)

            # Nome Responsável da Pessoa Jurídica Perante a RFB
            nome_responsavel_da_pessoa_juridica_perante_rfb_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n([^\n]+)', texto)
            nome_responsavel_da_pessoa_juridica_perante_rfb = nome_responsavel_da_pessoa_juridica_perante_rfb_match.group(
                1) if nome_responsavel_da_pessoa_juridica_perante_rfb_match else None

            # CPF do Responsável da Pessoa Jurídica Perante a RFB
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match.group(
                1) if cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match else None

            # Dados do Responsável pelo Preenchimento
            nome_responsavel_pelo_preechimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n([^\n]+)', texto)
            nome_responsavel_pelo_preechimento = nome_responsavel_pelo_preechimento_match.group(
                1) if nome_responsavel_pelo_preechimento_match else None

            # CPF do responsável pelo preechimento
            cpf_do_responsavel_pelo_preenchimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_pelo_preenchimento = cpf_do_responsavel_pelo_preenchimento_match.group(
                1) if cpf_do_responsavel_pelo_preenchimento_match else None

            # Informado em Processo Administrativo Anterior
            informado_em_processo_admistrativo_anterior_match = re.search(
                r'Informado em Processo Administrativo Anterior\n([^\n]+)', texto)
            informado_em_processo_admistrativo_anterior = informado_em_processo_admistrativo_anterior_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_processo_admistrativo_anterior = self.converter_para_booleano(
                informado_em_processo_admistrativo_anterior)

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_outro_perdcomp_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_outro_perdcomp = self.converter_para_booleano(informado_em_outro_perdcomp)

            # Situação Especial do Titular do Crédito
            situacao_especial_do_titular_credito_match = re.search(
                r'Situação Especial do Titular do Crédito\n([^\n]+)', texto)
            situacao_especial_do_titular_credito = situacao_especial_do_titular_credito_match.group(
                1) if situacao_especial_do_titular_credito_match else None
            situacao_especial_do_titular_credito = self.converter_para_booleano(situacao_especial_do_titular_credito)

            # Crédito de Sucedido
            credito_sucedido_match = re.search(r'Crédito de Sucedida\n([^\n]+)', texto)
            credito_sucedido = credito_sucedido_match.group(1) if credito_sucedido_match else None
            credito_sucedido = self.converter_para_booleano(credito_sucedido)

            # Valor Original do Crédito Inicial
            valor_original_do_credito_inicial_match = re.search(r'Valor Original do Crédito Inicial\n([^\n]+)',
                                                                texto)
            valor_original_do_credito_inicial = valor_original_do_credito_inicial_match.group(
                1) if valor_original_do_credito_inicial_match else None
            valor_original_do_credito_inicial = self.converter_valor(valor_original_do_credito_inicial)

            # Crédito Original na Data da Entrega
            credito_original_match = re.search(r'([^\n]+)\nCrédito Original na Data da Entrega', texto)
            credito_original = credito_original_match.group(1) if credito_original_match else None
            credito_original = self.converter_valor(credito_original)

            # Valor do Pedido de Restituição
            valor_do_pedido_restituicao_match = re.search(r'Valor do Pedido de Restituição\n([^\n]+)', texto)
            valor_do_pedido_restituicao = valor_do_pedido_restituicao_match.group(
                1) if valor_do_pedido_restituicao_match else None
            valor_do_pedido_restituicao = self.converter_valor(valor_do_pedido_restituicao)

            # Período de Apuração
            periodo_de_apuracao_origem_credito_match = re.search(r'([^\n]+)\nPeríodo de Apuração', texto)
            periodo_de_apuracao_origem_credito = periodo_de_apuracao_origem_credito_match.group(
                1) if periodo_de_apuracao_origem_credito_match else None
            periodo_de_apuracao_origem_credito = self.converter_data(periodo_de_apuracao_origem_credito)

            # CNPJ do Pagamento
            cnpj_do_pagamento_origem_credito_match = re.search(r'([^\n]+)\nCNPJ do Pagamento', texto)
            cnpj_do_pagamento_origem_credito = cnpj_do_pagamento_origem_credito_match.group(
                1) if cnpj_do_pagamento_origem_credito_match else None

            # Código da Receita
            codigo_da_receita_match = re.search(r'Código da Receita\n([^\n]+)', texto)
            codigo_da_receita = codigo_da_receita_match.group(1) if codigo_da_receita_match else None

            # Grupo de Tributo
            grupo_do_tributo_match = re.search(r'Grupo de Tributo\n([^\n]+)', texto)
            grupo_do_tributo = grupo_do_tributo_match.group(1) if grupo_do_tributo_match else None

            # Data de Arrecadação
            data_de_arrecadacao_match = re.search(r'Data de Arrecadação\n([^\n]+)', texto)
            data_de_arrecadacao = data_de_arrecadacao_match.group(1) if data_de_arrecadacao_match else None
            data_de_arrecadacao = self.converter_data(data_de_arrecadacao)

            # Valor do Principal
            valor_do_principal_match = re.search(r'Valor do Principal\n([^\n]+)', texto)
            valor_do_principal = valor_do_principal_match.group(1) if valor_do_principal_match else None
            valor_do_principal = self.converter_valor(valor_do_principal)

            # Valor da Multa
            valor_da_multa_match = re.search(r'Valor da Multa\n([^\n]+)', texto)
            valor_da_multa = valor_da_multa_match.group(1) if valor_da_multa_match else None
            valor_da_multa = self.converter_valor(valor_da_multa)

            # Valor dos Juros
            valor_do_juros_match = re.search(r'([^\n]+)\nValor dos Juros', texto)
            valor_do_juros = valor_do_juros_match.group(1) if valor_do_juros_match else None
            valor_do_juros = self.converter_valor(valor_do_juros)

            # Valor Total
            valor_total_origem_credito_match = re.search(r'Valor Total\n([^\n]+)', texto)
            valor_total_origem_credito = valor_total_origem_credito_match.group(
                1) if valor_total_origem_credito_match else None
            valor_total_origem_credito = self.converter_valor(valor_total_origem_credito)

            per = PER.objects.create(
                empresa=empresa,
                versao_perdcomp=perdcomp_version,
                cnpj=cnpj,
                numero_perdcomp=perdcomp_number,
                nome_empresarial=nome_empresarial,
                data_criacao=data_de_criacao,
                data_transmissao=data_de_transmissao,
                tipo_documento=tipo_documento,
                tipo_credito=tipo_credito,
                perdcomp_retificador=perdcomp_retificador,
                credito_oriundo_de_acao_judicial=credito_oriundo_de_acao_judicial,
                tipo_da_conta=tipo_da_conta,
                banco=banco,
                agencia=agencia,
                conta=conta,
                qualificacao=qualificacao,
                pessoa_juridica_extinta_por_liquidacao_voluntaria=pessoa_juridica_extinta_por_liquidacao_voluntaria,
                nome_responsavel_da_pessoa_juridica_perante_rfb=nome_responsavel_da_pessoa_juridica_perante_rfb,
                cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB=cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                nome_responsavel_pelo_preechimento=nome_responsavel_pelo_preechimento,
                cpf_do_responsavel_pelo_preenchimento=cpf_do_responsavel_pelo_preenchimento,
                informado_em_processo_admistrativo_anterior=informado_em_processo_admistrativo_anterior,
                informado_em_outro_perdcomp=informado_em_outro_perdcomp,
                situacao_especial_do_titular_credito=situacao_especial_do_titular_credito,
                credito_sucedido=credito_sucedido,
                valor_original_do_credito_inicial=valor_original_do_credito_inicial,
                credito_original=credito_original,
                valor_do_pedido_restituicao=valor_do_pedido_restituicao,
                periodo_de_apuracao_origem_credito=periodo_de_apuracao_origem_credito,
                cnpj_do_pagamento_origem_credito=cnpj_do_pagamento_origem_credito,
                codigo_da_receita=codigo_da_receita,
                grupo_do_tributo=grupo_do_tributo,
                data_de_arrecadacao=data_de_arrecadacao,
                valor_do_principal=valor_do_principal,
                valor_da_multa=valor_da_multa,
                valor_do_juros=valor_do_juros,
                valor_total_origem_credito=valor_total_origem_credito,
            )
            self.stdout.write(f"Per registrado: {per}")
        except Exception as e:
            self.stderr.write(f"Erro ao processar per: {str(e)}")

    def processar_pedido_cancelamento(self,texto):
        try:
            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # CNPJ
            cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()  # Remove formatações
            print(f"CNPJ extraído: {cnpj} (tamanho: {len(cnpj)})")

            # Número da perdcomp
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Nome empresarial
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            if not cnpj or not perdcomp_number:
                self.stderr.write("Erro: CNPJ ou Número de PER não encontrados no texto.")
                return

            # Verificar se a empresa já existe no banco
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )

            if created:
                self.stdout.write(f"Empresa criada: {empresa}")
            else:
                self.stdout.write(f"Empresa já existente: {empresa}")

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None
            data_de_criacao = self.converter_data(data_de_criacao)

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None
            data_de_transmissao = self.converter_data(data_de_transmissao)

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_cancelamento_match = re.search(r'Número do PER/DCOMP a Cancelar\n([^\n]+)', texto)
            perdcomp_cancelamento = perdcomp_cancelamento_match.group(1) if perdcomp_cancelamento_match else None

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)', texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None
            credito_oriundo_de_acao_judicial = self.converter_para_booleano(credito_oriundo_de_acao_judicial)

            # Pessoa Jurídica Extinta por Liquidação Voluntária
            pessoa_juridica_extinta_por_liquidacao_voluntaria_match = re.search(
                r'Pessoa Jurídica Extinta por Liquidação Voluntária\n([^\n]+)', texto)
            pessoa_juridica_extinta_por_liquidacao_voluntaria = pessoa_juridica_extinta_por_liquidacao_voluntaria_match.group(
                1) if pessoa_juridica_extinta_por_liquidacao_voluntaria_match else None
            pessoa_juridica_extinta_por_liquidacao_voluntaria = self.converter_para_booleano(pessoa_juridica_extinta_por_liquidacao_voluntaria)


            # Nome Responsável da Pessoa Jurídica Perante a RFB
            nome_responsavel_da_pessoa_juridica_perante_rfb_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n([^\n]+)', texto)
            nome_responsavel_da_pessoa_juridica_perante_rfb = nome_responsavel_da_pessoa_juridica_perante_rfb_match.group(
                1) if nome_responsavel_da_pessoa_juridica_perante_rfb_match else None


            # CPF do Responsável da Pessoa Jurídica Perante a RFB
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match.group(
                1) if cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match else None

            # Dados do Responsável pelo Preenchimento
            nome_responsavel_pelo_preechimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n([^\n]+)', texto)
            nome_responsavel_pelo_preechimento = nome_responsavel_pelo_preechimento_match.group(
                1) if nome_responsavel_pelo_preechimento_match else None

            # CPF do responsável pelo preechimento
            cpf_do_responsavel_pelo_preenchimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_pelo_preenchimento = cpf_do_responsavel_pelo_preenchimento_match.group(
                1) if cpf_do_responsavel_pelo_preenchimento_match else None

            # Verificar a existência de PER relacionado
            per_relacionado = PER.objects.filter(numero_perdcomp=perdcomp_cancelamento).first()

            # Verificar a existência de Dcomp relacionado
            dcomp_relacionado = Dcomp.objects.filter(numero_perdcomp=perdcomp_cancelamento).first()

            canc = PerCanc.objects.create(
                empresa=empresa,
                versao_perdcomp=perdcomp_version,
                cnpj=cnpj,
                numero_perdcomp=perdcomp_number,
                nome_empresarial=nome_empresarial,
                data_criacao=data_de_criacao,
                data_transmissao=data_de_transmissao,
                tipo_documento=tipo_documento,
                tipo_credito=tipo_credito,
                numero_perdcomp_a_cancelar=perdcomp_cancelamento,
                credito_oriundo_de_acao_judicial=credito_oriundo_de_acao_judicial,
                pessoa_juridica_extinta_por_liquidacao_voluntaria=pessoa_juridica_extinta_por_liquidacao_voluntaria,
                nome_responsavel_da_pessoa_juridica_perante_rfb=nome_responsavel_da_pessoa_juridica_perante_rfb,
                cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB=cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                nome_responsavel_pelo_preechimento=nome_responsavel_pelo_preechimento,
                cpf_do_responsavel_pelo_preenchimento=cpf_do_responsavel_pelo_preenchimento,
                per_relacionado=per_relacionado,
                dcomp_relacionado=dcomp_relacionado
            )

            self.stdout.write(f"Pedido de Cancelamento registrado: {perdcomp_number}")
            self.stdout.write(f"Processando Pedido de Cancelamento registrado: versão {perdcomp_version}, CNPJ {cnpj}, Perdcomp a Cancelar {perdcomp_cancelamento}")

        except Exception as e:
            self.stderr.write(f"Erro ao processar Pedido de Cancelamento: {str(e)}")

    def processar_pedido_restituicao_saldo_negativo_irpj(self,texto):
        try:
            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # CNPJ
            cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()  # Remove formatações
            print(f"CNPJ extraído: {cnpj} (tamanho: {len(cnpj)})")

            # Número da perdcomp
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Nome empresariaL
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            if not cnpj or not perdcomp_number:
                self.stderr.write("Erro: CNPJ ou Número de PER não encontrados no texto.")
                return

            # Verificar se a empresa já existe no banco
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )

            if created:
                self.stdout.write(f"Empresa criada: {empresa}")
            else:
                self.stdout.write(f"Empresa já existente: {empresa}")

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None
            data_de_criacao = self.converter_data(data_de_criacao)

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None
            data_de_transmissao = self.converter_data(data_de_transmissao)

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_retificador_match = re.search(r'PER/DCOMP Retificador\n([^\n]+)', texto)
            perdcomp_retificador = perdcomp_retificador_match.group(1) if perdcomp_retificador_match else None
            perdcomp_retificador = self.converter_para_booleano(perdcomp_retificador)

            # Número PER/DCOMP Retificador

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)', texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None
            credito_oriundo_de_acao_judicial = self.converter_para_booleano(credito_oriundo_de_acao_judicial)

            # Tipo de Conta
            tipo_de_conta_match = re.search(r'Tipo da Conta\n([^\n]+)', texto)
            tipo_da_conta = tipo_de_conta_match.group(1) if tipo_de_conta_match else None

            # Banco
            banco_match = re.search(r'Banco\n([^\n]+)', texto)
            banco = banco_match.group(1) if banco_match else None

            # Agência
            agencia_match = re.search(r'Agência\n([^\n]+)', texto)
            agencia = agencia_match.group(1) if agencia_match else None

            # Conta
            conta_match = re.search(r'N° Conta\n([^\n]+)', texto)
            conta = conta_match.group(1) if conta_match else None

            # Qualificação do Contribuinte
            qualificacao_match = re.search(r'Qualificação do Contribuinte\n([^\n]+)', texto)
            qualificacao = qualificacao_match.group(1) if qualificacao_match else None

            # Pessoa Jurídica Extinta por Liquidação Voluntária
            pessoa_juridica_extinta_por_liquidacao_voluntaria_match = re.search(
                r'Pessoa Jurídica Extinta por Liquidação Voluntária\n([^\n]+)', texto)
            pessoa_juridica_extinta_por_liquidacao_voluntaria = pessoa_juridica_extinta_por_liquidacao_voluntaria_match.group(
                1) if pessoa_juridica_extinta_por_liquidacao_voluntaria_match else None
            pessoa_juridica_extinta_por_liquidacao_voluntaria = self.converter_para_booleano(
                pessoa_juridica_extinta_por_liquidacao_voluntaria)

            # Nome Responsável da Pessoa Jurídica Perante a RFB
            nome_responsavel_da_pessoa_juridica_perante_rfb_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n([^\n]+)', texto)
            nome_responsavel_da_pessoa_juridica_perante_rfb = nome_responsavel_da_pessoa_juridica_perante_rfb_match.group(
                1) if nome_responsavel_da_pessoa_juridica_perante_rfb_match else None

            # CPF do Responsável da Pessoa Jurídica Perante a RFB
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match.group(
                1) if cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match else None

            # Dados do Responsável pelo Preenchimento
            nome_responsavel_pelo_preechimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n([^\n]+)', texto)
            nome_responsavel_pelo_preechimento = nome_responsavel_pelo_preechimento_match.group(
                1) if nome_responsavel_pelo_preechimento_match else None

            # CPF do responsável pelo preechimento
            cpf_do_responsavel_pelo_preenchimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_pelo_preenchimento = cpf_do_responsavel_pelo_preenchimento_match.group(
                1) if cpf_do_responsavel_pelo_preenchimento_match else None

            # Informado em Processo Administrativo Anterior
            informado_em_processo_admistrativo_anterior_match = re.search(
                r'Informado em Processo Administrativo anterior\n([^\n]+)', texto)
            informado_em_processo_admistrativo_anterior = informado_em_processo_admistrativo_anterior_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_processo_admistrativo_anterior = self.converter_para_booleano(
                informado_em_processo_admistrativo_anterior)

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_outro_perdcomp_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_outro_perdcomp = self.converter_para_booleano(informado_em_outro_perdcomp)

            # Crédito de Sucedido
            credito_sucedido_match = re.search(r'Crédito de Sucedida\n([^\n]+)', texto)
            credito_sucedido = credito_sucedido_match.group(1) if credito_sucedido_match else None
            credito_sucedido = self.converter_para_booleano(credito_sucedido)

            # Forma de Tributação do Lucro
            forma_tributacao_lucro_match = re.search(r'Forma de Tributação do Lucro\n([^\n]+)', texto)
            forma_tributacao_lucro = forma_tributacao_lucro_match.group(1) if forma_tributacao_lucro_match else None

            # Forma de Apuração
            forma_apuracao_match = re.search(r'Forma de Apuração\n([^\n]+)', texto)
            forma_apuracao = forma_apuracao_match.group(1) if forma_apuracao_match else None

            # Exercício
            exercicio_match = re.search(r'Exercício\n([^\n]+)', texto)
            exercicio = exercicio_match.group(1) if exercicio_match else None

            # Data incial do período
            data_inicial_periodo_match = re.search(r'Data Inicial do Período\n([^\n]+)', texto)
            data_inicial_periodo = data_inicial_periodo_match.group(1) if data_inicial_periodo_match else None
            data_inicial_periodo = self.converter_data(data_inicial_periodo)

            # Data final do período
            data_final_periodo_match = re.search(r'Data Final do Período\n([^\n]+)', texto)
            data_final_periodo = data_final_periodo_match.group(1) if data_final_periodo_match else None
            data_final_periodo = self.converter_data(data_final_periodo)

            # Imposto Devido
            imposto_devido_match = re.search(r'Imposto Devido\n([^\n]+)', texto)
            imposto_devido = imposto_devido_match.group(1) if imposto_devido_match else None
            imposto_devido = self.converter_valor(imposto_devido)

            # Total das parcelas de composição do crédito
            total_das_parcelas_composicao_credito_match = re.search(
                r'Total das Parcelas de Composição do Crédito\n([^\n]+)', texto)
            total_das_parcelas_composicao_credito = total_das_parcelas_composicao_credito_match.group(
                1) if total_das_parcelas_composicao_credito_match else None
            total_das_parcelas_composicao_credito = self.converter_valor(total_das_parcelas_composicao_credito)

            # Valor do saldo Negativo
            valor_do_saldo_negativo_match = re.search(r'Valor do Saldo Negativo\n([^\n]+)', texto)
            valor_do_saldo_negativo = valor_do_saldo_negativo_match.group(1) if valor_do_saldo_negativo_match else None
            valor_do_saldo_negativo = self.converter_valor(valor_do_saldo_negativo)

            # Crédito original na da da entrega
            credito_original_match = re.search(r'([^\n]+)\nCrédito Original na Data da Entrega', texto)
            credito_original = credito_original_match.group(1) if credito_original_match else None
            credito_original = self.converter_valor(credito_original)

            # Valor do pedido de restituição
            valor_do_pedido_restituicao_match = re.search(r'Valor do Pedido de Restituição\n([^\n]+)', texto)
            valor_do_pedido_restituicao = valor_do_pedido_restituicao_match.group(
                1) if valor_do_pedido_restituicao_match else None
            valor_do_pedido_restituicao = self.converter_valor(valor_do_pedido_restituicao)


            per = PER.objects.create(
                empresa=empresa,
                versao_perdcomp=perdcomp_version,
                cnpj=cnpj,
                numero_perdcomp=perdcomp_number,
                nome_empresarial=nome_empresarial,
                data_criacao=data_de_criacao,
                data_transmissao=data_de_transmissao,
                tipo_documento=tipo_documento,
                tipo_credito=tipo_credito,
                perdcomp_retificador=perdcomp_retificador,
                credito_oriundo_de_acao_judicial=credito_oriundo_de_acao_judicial,
                tipo_da_conta=tipo_da_conta,
                banco=banco,
                agencia=agencia,
                conta=conta,
                qualificacao=qualificacao,
                pessoa_juridica_extinta_por_liquidacao_voluntaria=pessoa_juridica_extinta_por_liquidacao_voluntaria,
                nome_responsavel_da_pessoa_juridica_perante_rfb=nome_responsavel_da_pessoa_juridica_perante_rfb,
                cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB=cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                nome_responsavel_pelo_preechimento=nome_responsavel_pelo_preechimento,
                cpf_do_responsavel_pelo_preenchimento=cpf_do_responsavel_pelo_preenchimento,
                informado_em_processo_admistrativo_anterior=informado_em_processo_admistrativo_anterior,
                informado_em_outro_perdcomp=informado_em_outro_perdcomp,
                credito_sucedido=credito_sucedido,
                forma_tributacao_lucro=forma_tributacao_lucro,
                forma_apuracao=forma_apuracao,
                exercicio=exercicio,
                data_inicial_periodo=data_inicial_periodo,
                data_final_periodo=data_final_periodo,
                imposto_devido=imposto_devido,
                total_parcelas_composicao_credito=total_das_parcelas_composicao_credito,
                valor_do_saldo_negativo=valor_do_saldo_negativo,
                credito_original=credito_original,
                valor_do_pedido_restituicao=valor_do_pedido_restituicao
            )
            self.stdout.write(f"Per registrado: {per}")
        except Exception as e:
                self.stderr.write(f"Erro ao processar PER: {str(e)}")

    def processar_pedido_restituicao_saldo_negativo_csll(self,texto):
        try:
            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # CNPJ
            cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            cnpj = cnpj_match.group(1) if cnpj_match else None
            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()  # Remove formatações
            print(f"CNPJ extraído: {cnpj} (tamanho: {len(cnpj)})")

            # Número da perdcomp
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Nome empresariaL
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            if not cnpj or not perdcomp_number:
                self.stderr.write("Erro: CNPJ ou Número de PER não encontrados no texto.")
                return

            # Verificar se a empresa já existe no banco
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )

            if created:
                self.stdout.write(f"Empresa criada: {empresa}")
            else:
                self.stdout.write(f"Empresa já existente: {empresa}")

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None
            data_de_criacao = self.converter_data(data_de_criacao)

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None
            data_de_transmissao = self.converter_data(data_de_transmissao)

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_retificador_match = re.search(r'PER/DCOMP Retificador\n([^\n]+)', texto)
            perdcomp_retificador = perdcomp_retificador_match.group(1) if perdcomp_retificador_match else None
            perdcomp_retificador = self.converter_para_booleano(perdcomp_retificador)

            # Número PER/DCOMP Retificador

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)', texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None
            credito_oriundo_de_acao_judicial = self.converter_para_booleano(credito_oriundo_de_acao_judicial)

            # Tipo de Conta
            tipo_de_conta_match = re.search(r'Tipo da Conta\n([^\n]+)', texto)
            tipo_da_conta = tipo_de_conta_match.group(1) if tipo_de_conta_match else None

            # Banco
            banco_match = re.search(r'Banco\n([^\n]+)', texto)
            banco = banco_match.group(1) if banco_match else None

            # Agência
            agencia_match = re.search(r'Agência\n([^\n]+)', texto)
            agencia = agencia_match.group(1) if agencia_match else None

            # Conta
            conta_match = re.search(r'N° Conta\n([^\n]+)', texto)
            conta = conta_match.group(1) if conta_match else None

            # Qualificação do Contribuinte
            qualificacao_match = re.search(r'Qualificação do Contribuinte\n([^\n]+)', texto)
            qualificacao = qualificacao_match.group(1) if qualificacao_match else None

            # Pessoa Jurídica Extinta por Liquidação Voluntária
            pessoa_juridica_extinta_por_liquidacao_voluntaria_match = re.search(
                r'Pessoa Jurídica Extinta por Liquidação Voluntária\n([^\n]+)', texto)
            pessoa_juridica_extinta_por_liquidacao_voluntaria = pessoa_juridica_extinta_por_liquidacao_voluntaria_match.group(
                1) if pessoa_juridica_extinta_por_liquidacao_voluntaria_match else None
            pessoa_juridica_extinta_por_liquidacao_voluntaria = self.converter_para_booleano(
                pessoa_juridica_extinta_por_liquidacao_voluntaria)

            # Nome Responsável da Pessoa Jurídica Perante a RFB
            nome_responsavel_da_pessoa_juridica_perante_rfb_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n([^\n]+)', texto)
            nome_responsavel_da_pessoa_juridica_perante_rfb = nome_responsavel_da_pessoa_juridica_perante_rfb_match.group(
                1) if nome_responsavel_da_pessoa_juridica_perante_rfb_match else None

            # CPF do Responsável da Pessoa Jurídica Perante a RFB
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match.group(
                1) if cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match else None

            # Dados do Responsável pelo Preenchimento
            nome_responsavel_pelo_preechimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n([^\n]+)', texto)
            nome_responsavel_pelo_preechimento = nome_responsavel_pelo_preechimento_match.group(
                1) if nome_responsavel_pelo_preechimento_match else None

            # CPF do responsável pelo preechimento
            cpf_do_responsavel_pelo_preenchimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_pelo_preenchimento = cpf_do_responsavel_pelo_preenchimento_match.group(
                1) if cpf_do_responsavel_pelo_preenchimento_match else None

            # Informado em Processo Administrativo Anterior
            informado_em_processo_admistrativo_anterior_match = re.search(
                r'Informado em Processo Administrativo anterior\n([^\n]+)', texto)
            informado_em_processo_admistrativo_anterior = informado_em_processo_admistrativo_anterior_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_processo_admistrativo_anterior = self.converter_para_booleano(
                informado_em_processo_admistrativo_anterior)

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_processo_admistrativo_anterior_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_outro_perdcomp = self.converter_para_booleano(informado_em_outro_perdcomp)

            # Crédito de Sucedido
            credito_sucedido_match = re.search(r'Crédito de Sucedida\n([^\n]+)', texto)
            credito_sucedido = credito_sucedido_match.group(1) if credito_sucedido_match else None
            credito_sucedido = self.converter_para_booleano(credito_sucedido)

            # Forma de Tributação do Lucro
            forma_tributacao_lucro_match = re.search(r'Forma de Tributação no Período\n([^\n]+)', texto)
            forma_tributacao_lucro = forma_tributacao_lucro_match.group(1) if forma_tributacao_lucro_match else None

            # Forma de Apuração
            forma_apuracao_match = re.search(r'Forma de Apuração\n([^\n]+)', texto)
            forma_apuracao = forma_apuracao_match.group(1) if forma_apuracao_match else None

            # Exercício
            exercicio_match = re.search(r'Exercício\n([^\n]+)', texto)
            exercicio = exercicio_match.group(1) if exercicio_match else None

            # Data incial do período
            data_inicial_periodo_match = re.search(r'Data Inicial do Período\n([^\n]+)', texto)
            data_inicial_periodo = data_inicial_periodo_match.group(1) if data_inicial_periodo_match else None
            data_inicial_periodo = self.converter_data(data_inicial_periodo)

            # Data final do período
            data_final_periodo_match = re.search(r'Data Final do Período\n([^\n]+)', texto)
            data_final_periodo = data_final_periodo_match.group(1) if data_final_periodo_match else None
            data_final_periodo = self.converter_data(data_final_periodo)

            # CSLL Devida
            imposto_devido_match = re.search(r'CSLL Devida\n([^\n]+)', texto)
            imposto_devido = imposto_devido_match.group(1) if imposto_devido_match else None
            imposto_devido = self.converter_valor(imposto_devido)

            # Total das parcelas de composição do crédito
            total_das_parcelas_composicao_credito_match = re.search(
                r'([^\n]+)\nTotal das Parcelas de Composição do Crédito', texto)
            total_das_parcelas_composicao_credito = total_das_parcelas_composicao_credito_match.group(
                1) if total_das_parcelas_composicao_credito_match else None
            total_das_parcelas_composicao_credito = self.converter_valor(total_das_parcelas_composicao_credito)

            # Valor do saldo Negativo
            valor_do_saldo_negativo_match = re.search(r'Valor do Saldo Negativo\n([^\n]+)', texto)
            valor_do_saldo_negativo = valor_do_saldo_negativo_match.group(1) if valor_do_saldo_negativo_match else None
            valor_do_saldo_negativo = self.converter_valor(valor_do_saldo_negativo)

            # Crédito original na da da entrega
            credito_original_match = re.search(r'([^\n]+)\nCrédito Original na Data da Entrega', texto)
            credito_original = credito_original_match.group(1) if credito_original_match else None
            credito_original = self.converter_valor(credito_original)

            # Valor do pedido de restituição
            valor_do_pedido_restituicao_match = re.search(r'([^\n]+)\nValor do Pedido de Restituição', texto)
            valor_do_pedido_restituicao = valor_do_pedido_restituicao_match.group(
                1) if valor_do_pedido_restituicao_match else None
            valor_do_pedido_restituicao = self.converter_valor(valor_do_pedido_restituicao)


            per = PER.objects.create(
                empresa=empresa,
                versao_perdcomp=perdcomp_version,
                cnpj=cnpj,
                numero_perdcomp=perdcomp_number,
                nome_empresarial=nome_empresarial,
                data_criacao=data_de_criacao,
                data_transmissao=data_de_transmissao,
                tipo_documento=tipo_documento,
                tipo_credito=tipo_credito,
                perdcomp_retificador=perdcomp_retificador,
                credito_oriundo_de_acao_judicial=credito_oriundo_de_acao_judicial,
                tipo_da_conta=tipo_da_conta,
                banco=banco,
                agencia=agencia,
                conta=conta,
                qualificacao=qualificacao,
                pessoa_juridica_extinta_por_liquidacao_voluntaria=pessoa_juridica_extinta_por_liquidacao_voluntaria,
                nome_responsavel_da_pessoa_juridica_perante_rfb=nome_responsavel_da_pessoa_juridica_perante_rfb,
                cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB=cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                nome_responsavel_pelo_preechimento=nome_responsavel_pelo_preechimento,
                cpf_do_responsavel_pelo_preenchimento=cpf_do_responsavel_pelo_preenchimento,
                informado_em_processo_admistrativo_anterior=informado_em_processo_admistrativo_anterior,
                informado_em_outro_perdcomp=informado_em_outro_perdcomp,
                credito_sucedido=credito_sucedido,
                forma_tributacao_lucro=forma_tributacao_lucro,
                forma_apuracao=forma_apuracao,
                exercicio=exercicio,
                data_inicial_periodo=data_inicial_periodo,
                data_final_periodo=data_final_periodo,
                imposto_devido=imposto_devido,
                total_parcelas_composicao_credito=total_das_parcelas_composicao_credito,
                valor_do_saldo_negativo=valor_do_saldo_negativo,
                credito_original=credito_original,
                valor_do_pedido_restituicao=valor_do_pedido_restituicao
            )
            self.stdout.write(f"PER registrado: {per}")
        except Exception as e:
                self.stderr.write(f"Erro ao processar PER: {str(e)}")

    def processar_declaracao_compensacao(self,texto):
        try:
            # CNPJ
            cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            cnpj = cnpj_match.group(1) if cnpj_match else None

            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()  # Remove formatações

            print(f"CNPJ extraído: {cnpj} (tamanho: {len(cnpj)})")
            print(f"\n")

            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # Número da DCOMP
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Número da PER
            numero_perdcomp_inicial_match = re.search(r'N° do PER/DCOMP Inicial\n([^\n]+)', texto)
            numero_perdcomp_inicial = numero_perdcomp_inicial_match.group(
                1) if numero_perdcomp_inicial_match else None

            if numero_perdcomp_inicial:
                try:
                    per_instance = PER.objects.get(numero_perdcomp=numero_perdcomp_inicial)
                except PER.DoesNotExist:
                    self.stderr.write(
                        f"PER não encontrado para o número: {numero_perdcomp_inicial}. Criando um novo...")
                    per_instance = PER.objects.create(numero=numero_perdcomp_inicial)
            else:
                per_instance = None

            # Nome empresarial
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            if not cnpj or not perdcomp_number:
                self.stderr.write("Erro: CNPJ ou Número de PER não encontrados no texto.")
                return

                # Verificar se a empresa já existe no banco
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )

            if created:
                self.stdout.write(f"Empresa criada: {empresa}")
            else:
                self.stdout.write(f"Empresa já existente: {empresa}")

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None
            data_de_criacao = self.converter_data(data_de_criacao)

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None
            data_de_transmissao = self.converter_data(data_de_transmissao)

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_retificador_match = re.search(r'PER/DCOMP Retificador\n([^\n]+)', texto)
            perdcomp_retificador = perdcomp_retificador_match.group(1) if perdcomp_retificador_match else None
            perdcomp_retificador = self.converter_para_booleano(perdcomp_retificador)

            # Número PER/DCOMP Retificador
            numero_perdcomp_retificador_match = re.search(r'N° PER/DCOMP Retificado\n([^\n]+)', texto)
            numero_perdcomp_retificador = numero_perdcomp_retificador_match.group(
                1) if numero_perdcomp_retificador_match else None

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)',
                                                               texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None
            credito_oriundo_de_acao_judicial = self.converter_para_booleano(credito_oriundo_de_acao_judicial)

            # Qualificação do Contribuinte
            qualificacao_match = re.search(r'Qualificação do Contribuinte\n([^\n]+)', texto)
            qualificacao = qualificacao_match.group(1) if qualificacao_match else None

            # Pessoa Jurídica Extinta por Liquidação Voluntária
            pessoa_juridica_extinta_por_liquidacao_voluntaria_match = re.search(
                r'Pessoa Jurídica Extinta por Liquidação Voluntária\n([^\n]+)', texto)
            pessoa_juridica_extinta_por_liquidacao_voluntaria = pessoa_juridica_extinta_por_liquidacao_voluntaria_match.group(
                1) if pessoa_juridica_extinta_por_liquidacao_voluntaria_match else None
            pessoa_juridica_extinta_por_liquidacao_voluntaria = self.converter_para_booleano(
                pessoa_juridica_extinta_por_liquidacao_voluntaria)

            # Nome Responsável da Pessoa Jurídica Perante a RFB
            nome_responsavel_da_pessoa_juridica_perante_rfb_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n([^\n]+)', texto)
            nome_responsavel_da_pessoa_juridica_perante_rfb = nome_responsavel_da_pessoa_juridica_perante_rfb_match.group(
                1) if nome_responsavel_da_pessoa_juridica_perante_rfb_match else None

            # CPF do Responsável da Pessoa Jurídica Perante a RFB
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match.group(
                1) if cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match else None

            # Dados do Responsável pelo Preenchimento
            nome_responsavel_pelo_preechimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n([^\n]+)', texto)
            nome_responsavel_pelo_preechimento = nome_responsavel_pelo_preechimento_match.group(
                1) if nome_responsavel_pelo_preechimento_match else None

            # CPF do responsável pelo preechimento
            cpf_do_responsavel_pelo_preenchimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_pelo_preenchimento = cpf_do_responsavel_pelo_preenchimento_match.group(
                1) if cpf_do_responsavel_pelo_preenchimento_match else None

            # Informado em Processo Administrativo Anterior
            informado_em_processo_admistrativo_anterior_match = re.search(
                r'Informado em Processo Administrativo Anterior\n([^\n]+)', texto)
            informado_em_processo_admistrativo_anterior = informado_em_processo_admistrativo_anterior_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_processo_admistrativo_anterior = self.converter_para_booleano(
                informado_em_processo_admistrativo_anterior)

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_outro_perdcomp_match.group(
                1) if informado_em_outro_perdcomp_match else None
            informado_em_outro_perdcomp = self.converter_para_booleano(informado_em_outro_perdcomp)

            # Situação Especial do Titular do Crédito
            situacao_especial_do_titular_credito_match = re.search(
                r'Situação Especial do Titular do Crédito\n([^\n]+)', texto)
            situacao_especial_do_titular_credito = situacao_especial_do_titular_credito_match.group(
                1) if situacao_especial_do_titular_credito_match else None

            situacao_especial_do_titular_credito = self.converter_para_booleano(situacao_especial_do_titular_credito)

            # Selic Acumulada
            selic_acumulada_match = re.search(r'Selic Acumulada\n([^\n]+)', texto)
            selic_acumulada = selic_acumulada_match.group(1) if selic_acumulada_match else None
            selic_acumulada = self.converter_para_booleano(selic_acumulada)

            # Crédito de Sucedido
            credito_sucedido_match = re.search(r'Crédito de Sucedida\n([^\n]+)', texto)
            credito_sucedido = credito_sucedido_match.group(1) if credito_sucedido_match else None
            credito_sucedido = self.converter_para_booleano(credito_sucedido)

            # Valor Original do Crédito Inicial
            valor_original_do_credito_inicial_match = re.search(r'Valor Original do Crédito Inicial\n([^\n]+)',
                                                                texto)
            valor_original_do_credito_inicial = valor_original_do_credito_inicial_match.group(
                1) if valor_original_do_credito_inicial_match else None
            valor_original_do_credito_inicial = self.converter_valor(valor_original_do_credito_inicial)

            # Crédito Original na Data da Entrega
            credito_original_match = re.search(r'([^\n]+)\nCrédito Original na Data da Entrega', texto)
            credito_original = credito_original_match.group(1) if credito_original_match else None
            credito_original = self.converter_valor(credito_original)

            # Crédito Atualizado
            credito_atualizado_match = re.search(r'Crédito Atualizado\n([^\n]+)', texto)
            credito_atualizado = credito_atualizado_match.group(1) if credito_atualizado_match else None
            credito_atualizado = self.converter_valor(credito_atualizado)

            # Total dos débitos deste documento
            total_dos_debitos_deste_documento_match = re.search(r'Total dos Débitos deste Documento\n([^\n]+)',
                                                                texto)
            total_dos_debitos = total_dos_debitos_deste_documento_match.group(
                1) if total_dos_debitos_deste_documento_match else None
            total_dos_debitos = self.converter_valor(total_dos_debitos)

            # Total do Crédito Original Utilizado neste Documento
            total_do_credito_original_utilizado_neste_documento_match = re.search(
                r'Total do Crédito Original Utilizado neste Documento\n([^\n]+)', texto)
            total_do_credito_original_utilizado_neste_documento = total_do_credito_original_utilizado_neste_documento_match.group(
                1) if total_do_credito_original_utilizado_neste_documento_match else None
            total_do_credito_original_utilizado_neste_documento = self.converter_valor(
                total_do_credito_original_utilizado_neste_documento)

            # Saldo do Crédito Original
            saldo_do_credito_original_match = re.search(r'Saldo do Crédito Original\n([^\n]+)', texto)
            saldo_do_credito_original = saldo_do_credito_original_match.group(
                1) if saldo_do_credito_original_match else None
            saldo_do_credito_original = self.converter_valor(saldo_do_credito_original)

            # Período de Apuração
            periodo_de_apuracao_origem_credito_match = re.search(r'([^\n]+)\nPeríodo de Apuração', texto)
            periodo_de_apuracao_origem_credito = periodo_de_apuracao_origem_credito_match.group(
                1) if periodo_de_apuracao_origem_credito_match else None
            periodo_de_apuracao_origem_credito = self.converter_data(periodo_de_apuracao_origem_credito)

            # CNPJ do Pagamento
            cnpj_do_pagamento_origem_credito_match = re.search(r'([^\n]+)\nCNPJ do Pagamento', texto)
            cnpj_do_pagamento_origem_credito = cnpj_do_pagamento_origem_credito_match.group(
                1) if cnpj_do_pagamento_origem_credito_match else None

            # Código da Receita
            codigo_da_receita_match = re.search(r'Código da Receita\n([^\n]+)', texto)
            codigo_da_receita = codigo_da_receita_match.group(1) if codigo_da_receita_match else None

            # Grupo de Tributo
            grupo_do_tributo_match = re.search(r'Grupo de Tributo\n([^\n]+)', texto)
            grupo_do_tributo = grupo_do_tributo_match.group(1) if grupo_do_tributo_match else None

            # Data de Arrecadação
            data_de_arrecadacao_match = re.search(r'Data de Arrecadação\n([^\n]+)', texto)
            data_de_arrecadacao = data_de_arrecadacao_match.group(1) if data_de_arrecadacao_match else None
            data_de_arrecadacao = self.converter_data(data_de_arrecadacao)

            # Valor do Principal
            valor_do_principal_match = re.search(r'Valor do Principal\n([^\n]+)', texto)
            valor_do_principal = valor_do_principal_match.group(1) if valor_do_principal_match else None
            valor_do_principal = self.converter_valor(valor_do_principal)

            # Valor da Multa
            valor_da_multa_match = re.search(r'Valor da Multa\n([^\n]+)', texto)
            valor_da_multa = valor_da_multa_match.group(1) if valor_da_multa_match else None
            valor_da_multa = self.converter_valor(valor_da_multa)

            # Valor dos Juros
            valor_do_juros_match = re.search(r'([^\n]+)\nValor dos Juros', texto)
            valor_do_juros = valor_do_juros_match.group(1) if valor_do_juros_match else None
            valor_do_juros = self.converter_valor(valor_do_juros)

            # Valor Total
            valor_total_origem_credito_match = re.search(r'Valor Total\n([^\n]+)', texto)
            valor_total_origem_credito = valor_total_origem_credito_match.group(
                1) if valor_total_origem_credito_match else None
            valor_total_origem_credito = self.converter_valor(valor_total_origem_credito)

            # Salvar os dados no banco de dados
            dcomp = Dcomp.objects.create(
                empresa=empresa,
                versao_perdcomp=perdcomp_version,
                cnpj=cnpj,
                numero_perdcomp=perdcomp_number,
                numero_perdcomp_inicial=per_instance,
                nome_empresarial=nome_empresarial,
                data_criacao=data_de_criacao,
                data_transmissao=data_de_transmissao,
                tipo_documento=tipo_documento,
                tipo_credito=tipo_credito,
                perdcomp_retificador=perdcomp_retificador,
                numero_perdcomp_retificador=numero_perdcomp_retificador,
                credito_oriundo_de_acao_judicial=credito_oriundo_de_acao_judicial,
                qualificacao=qualificacao,
                pessoa_juridica_extinta_por_liquidacao_voluntaria=pessoa_juridica_extinta_por_liquidacao_voluntaria,
                nome_responsavel_da_pessoa_juridica_perante_rfb=nome_responsavel_da_pessoa_juridica_perante_rfb,
                cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB=cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                nome_responsavel_pelo_preechimento=nome_responsavel_pelo_preechimento,
                cpf_do_responsavel_pelo_preenchimento=cpf_do_responsavel_pelo_preenchimento,
                informado_em_processo_admistrativo_anterior=informado_em_processo_admistrativo_anterior,
                informado_em_outro_perdcomp=informado_em_outro_perdcomp,
                situacao_especial_do_titular_credito=situacao_especial_do_titular_credito,
                credito_sucedido=credito_sucedido,
                selic_acumulada=selic_acumulada,
                valor_original_do_credito_inicial=valor_original_do_credito_inicial,
                credito_original=credito_original,
                credito_atualizado=credito_atualizado,
                total_dos_debitos=total_dos_debitos,
                total_do_credito_original_utilizado_neste_documento=total_do_credito_original_utilizado_neste_documento,
                saldo_do_credito_original=saldo_do_credito_original,
                periodo_de_apuracao_origem_credito=periodo_de_apuracao_origem_credito,
                cnpj_do_pagamento_origem_credito=cnpj_do_pagamento_origem_credito,
                codigo_da_receita=codigo_da_receita,
                grupo_do_tributo=grupo_do_tributo,
                data_de_arrecadacao=data_de_arrecadacao,
                valor_do_principal=valor_do_principal,
                valor_da_multa=valor_da_multa,
                valor_do_juros=valor_do_juros,
                valor_total_origem_credito=valor_total_origem_credito
            )
            self.stdout.write(f"Dcomp registrada: {dcomp}")
            self.stdout.write(f"Processando Declaração de Compensação: versão {perdcomp_version}, CNPJ {cnpj}")
        except Exception as e:
            self.stderr.write(f"Erro ao processar Declaração de Compensação: {str(e)}")

    def processar_declaracao_compensacao_saldo_negativo_irpj(self,texto):
        try:
            # CNPJ
            cnpj_match = re.search(r'CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)

            # Extraindo o CNPJ se encontrado
            cnpj = cnpj_match.group(1) if cnpj_match else None
            self.stderr.write(
                f"cnpj: {cnpj}.")
            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()

            print(f"CNPJ extraído: {cnpj} (tamanho: {len(cnpj)})")

            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # Número da DCOMP
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Número da PER
            numero_perdcomp_inicial_match = re.search(r'N° do PER/DCOMP Inicial\n([^\n]+)', texto)
            numero_perdcomp_inicial = numero_perdcomp_inicial_match.group(
                1) if numero_perdcomp_inicial_match else None

            if numero_perdcomp_inicial:
                try:
                    per_instance = PER.objects.get(numero_perdcomp=numero_perdcomp_inicial)
                except PER.DoesNotExist:
                    self.stderr.write(
                        f"PER não encontrado para o número: {numero_perdcomp_inicial}. Criando um novo...")
                    per_instance = PER.objects.create(numero=numero_perdcomp_inicial)
            else:
                per_instance = None

            # Nome empresarial
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            if not cnpj or not perdcomp_number:
                self.stderr.write("Erro: CNPJ ou Número de PER não encontrados no texto.")
                return

                # Verificar se a empresa já existe no banco
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )
            self.stdout.write(f"cnpj: {cnpj}")


            if created:
                self.stdout.write(f"Empresa criada: {empresa}")
            else:
                self.stdout.write(f"Empresa já existente: {empresa}")

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None
            data_de_criacao = self.converter_data(data_de_criacao)

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None
            data_de_transmissao = self.converter_data(data_de_transmissao)

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_retificador_match = re.search(r'PER/DCOMP Retificador\n([^\n]+)', texto)
            perdcomp_retificador = perdcomp_retificador_match.group(1) if perdcomp_retificador_match else None
            perdcomp_retificador = self.converter_para_booleano(perdcomp_retificador)

            # Número PER/DCOMP Retificador
            numero_perdcomp_retificador_match = re.search(r'N° PER/DCOMP Retificado\n([^\n]+)', texto)
            numero_perdcomp_retificador = numero_perdcomp_retificador_match.group(
                1) if numero_perdcomp_retificador_match else None

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)',
                                                               texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None
            credito_oriundo_de_acao_judicial = self.converter_para_booleano(credito_oriundo_de_acao_judicial)

            # Qualificação do Contribuinte
            qualificacao_match = re.search(r'Qualificação do Contribuinte\n([^\n]+)', texto)
            qualificacao = qualificacao_match.group(1) if qualificacao_match else None

            # Pessoa Jurídica Extinta por Liquidação Voluntária
            pessoa_juridica_extinta_por_liquidacao_voluntaria_match = re.search(
                r'Pessoa Jurídica Extinta por Liquidação Voluntária\n([^\n]+)', texto)
            pessoa_juridica_extinta_por_liquidacao_voluntaria = pessoa_juridica_extinta_por_liquidacao_voluntaria_match.group(
                1) if pessoa_juridica_extinta_por_liquidacao_voluntaria_match else None
            pessoa_juridica_extinta_por_liquidacao_voluntaria = self.converter_para_booleano(
                pessoa_juridica_extinta_por_liquidacao_voluntaria)

            # Nome Responsável da Pessoa Jurídica Perante a RFB
            nome_responsavel_da_pessoa_juridica_perante_rfb_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n([^\n]+)', texto)
            nome_responsavel_da_pessoa_juridica_perante_rfb = nome_responsavel_da_pessoa_juridica_perante_rfb_match.group(
                1) if nome_responsavel_da_pessoa_juridica_perante_rfb_match else None

            # CPF do Responsável da Pessoa Jurídica Perante a RFB
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match.group(
                1) if cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match else None

            # Dados do Responsável pelo Preenchimento
            nome_responsavel_pelo_preechimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n([^\n]+)', texto)
            nome_responsavel_pelo_preechimento = nome_responsavel_pelo_preechimento_match.group(
                1) if nome_responsavel_pelo_preechimento_match else None

            # CPF do responsável pelo preechimento
            cpf_do_responsavel_pelo_preenchimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_pelo_preenchimento = cpf_do_responsavel_pelo_preenchimento_match.group(
                1) if cpf_do_responsavel_pelo_preenchimento_match else None

            # Tentativa de encontrar "Informado em Processo Administrativo Anterior"
            informado_em_processo_admistrativo_anterior_match = re.search(
                r'Informado em Processo Administrativo Anterior\n([^\n]+)', texto)

            # Caso não encontre, tenta "Informado em Processo Administrativo anterior"
            if not informado_em_processo_admistrativo_anterior_match:
                informado_em_processo_admistrativo_anterior_match = re.search(
                    r'Informado em Processo Administrativo anterior\n([^\n]+)', texto)

            # Captura o valor encontrado ou define como None
            informado_em_processo_admistrativo_anterior = (
                informado_em_processo_admistrativo_anterior_match.group(1)
                if informado_em_processo_admistrativo_anterior_match
                else None
            )
            informado_em_processo_admistrativo_anterior = self.converter_para_booleano(informado_em_processo_admistrativo_anterior)

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_outro_perdcomp_match.group(
                1) if informado_em_outro_perdcomp_match else None
            informado_em_outro_perdcomp = self.converter_para_booleano(informado_em_outro_perdcomp)

            # Crédito de Sucedido
            credito_sucedido_match = re.search(r'Crédito de Sucedida\n([^\n]+)', texto)
            credito_sucedido = credito_sucedido_match.group(1) if credito_sucedido_match else None
            credito_sucedido = self.converter_para_booleano(credito_sucedido)

            # Forma de Tributação do Lucro
            forma_tributacao_lucro_match = re.search(r'Forma de Tributação do Lucro\n([^\n]+)', texto)
            forma_tributacao_lucro = forma_tributacao_lucro_match.group(1) if forma_tributacao_lucro_match else None

            # Forma de Apuração
            forma_apuracao_match = re.search(r'Forma de Apuração\n([^\n]+)', texto)
            forma_apuracao = forma_apuracao_match.group(1) if forma_apuracao_match else None

            # Exercício
            exercicio_match = re.search(r'Exercício\n([^\n]+)', texto)
            exercicio = exercicio_match.group(1) if exercicio_match else None

            # Data incial do período
            data_inicial_periodo_match = re.search(r'Data Inicial do Período\n([^\n]+)', texto)
            data_inicial_periodo = data_inicial_periodo_match.group(1) if data_inicial_periodo_match else None
            data_inicial_periodo = self.converter_data(data_inicial_periodo)

            # Data final do período
            data_final_periodo_match = re.search(r'Data Final do Período\n([^\n]+)', texto)
            data_final_periodo = data_final_periodo_match.group(1) if data_final_periodo_match else None
            data_final_periodo = self.converter_data(data_final_periodo)

            # Selic Acumulada
            selic_acumulada_match = re.search(r'Selic Acumulada\n([^\n]+)', texto)
            selic_acumulada = selic_acumulada_match.group(1) if selic_acumulada_match else None
            selic_acumulada = self.converter_valor(selic_acumulada)

            # Imposto Devido
            imposto_devido_match = re.search(r'Imposto Devido\n([^\n]+)', texto)

            if not imposto_devido_match:
                imposto_devido_match = re.search(r'CSLL Devida\n([^\n]+)', texto)

            imposto_devido = imposto_devido_match.group(1) if imposto_devido_match else None
            imposto_devido = self.converter_valor(imposto_devido)

            # Total das Parcelas de composição do Crédito
            total_das_parcelas_composicao_credito_match = re.search(
                r'Total das Parcelas de Composição do Crédito\n([^\n]+)', texto)
            total_das_parcelas_composicao_credito = total_das_parcelas_composicao_credito_match.group(
                1) if total_das_parcelas_composicao_credito_match else None
            total_das_parcelas_composicao_credito = self.converter_valor(total_das_parcelas_composicao_credito)

            # Valor do Saldo Negativo
            valor_do_saldo_negativo_match = re.search(r'Valor do Saldo Negativo\n([^\n]+)', texto)
            valor_do_saldo_negativo = valor_do_saldo_negativo_match.group(1) if valor_do_saldo_negativo_match else None
            valor_do_saldo_negativo = self.converter_valor(valor_do_saldo_negativo)

            # Crédito Original na data de entrega
            credito_original_match = re.search(r'([^\n]+)\nCrédito Original na Data da Entrega', texto)
            credito_original = credito_original_match.group(1) if credito_original_match else None
            credito_original = self.converter_valor(credito_original)

            # Crédito Atualizado
            credito_atualizado_match = re.search(r'Crédito Atualizado\n([^\n]+)', texto)
            credito_atualizado = credito_atualizado_match.group(1) if credito_atualizado_match else None
            credito_atualizado = self.converter_valor(credito_atualizado)

            # Procura a posição de "Total dos Débitos deste Documento" no texto
            total_dos_debitos_deste_documento_match = re.match(r'Total dos Débitos deste Documento\n([^\n]+)', texto)

            if not total_dos_debitos_deste_documento_match:
                # Caso não encontre, tenta "Total dos Débitos desta DCOMP"
                total_dos_debitos_deste_documento_match = re.search(r'Total dos débitos desta DCOMP', texto)
                if total_dos_debitos_deste_documento_match:
                    # Divide o texto em linhas para buscar o valor
                    linhas = texto.splitlines()
                    linha_inicial = texto.count('\n', 0,
                                                total_dos_debitos_deste_documento_match.start()) + 1  # Linha do cabeçalho
                    linha_alvo = linha_inicial + 4  # O valor está 2 linhas abaixo do cabeçalho
                    total_dos_debitos = linhas[linha_alvo].strip() if linha_alvo < len(linhas) else None
                else:
                    # Nenhum dos cabeçalhos foi encontrado
                    total_dos_debitos = None
            else:
                # Caso "Total dos Débitos deste Documento" seja encontrado, captura diretamente
                total_dos_debitos = total_dos_debitos_deste_documento_match.group(1)

            total_dos_debitos = self.converter_valor(total_dos_debitos)

            # Total do Crédito Original Utilizado neste Documento
            total_do_credito_original_utilizado_neste_documento_match = re.search(
                r'Total do Crédito Original Utilizado nesta DCOMP\n([^\n]+)', texto)
            total_do_credito_original_utilizado_neste_documento = total_do_credito_original_utilizado_neste_documento_match.group(
                1) if total_do_credito_original_utilizado_neste_documento_match else None

            total_do_credito_original_utilizado_neste_documento = self.converter_valor(total_do_credito_original_utilizado_neste_documento)

            # Saldo do Crédito Original
            saldo_do_credito_original_match = re.search(r'Saldo do Crédito Original\n([^\n]+)', texto)
            saldo_do_credito_original = saldo_do_credito_original_match.group(
                1) if saldo_do_credito_original_match else None
            saldo_do_credito_original = self.converter_valor(saldo_do_credito_original)

            # Salvar os dados no banco de dados
            dcomp = Dcomp.objects.create(
                empresa=empresa,
                versao_perdcomp=perdcomp_version,
                cnpj=cnpj,
                numero_perdcomp=perdcomp_number,
                numero_perdcomp_inicial=per_instance,
                nome_empresarial=nome_empresarial,
                data_criacao=data_de_criacao,
                data_transmissao=data_de_transmissao,
                tipo_documento=tipo_documento,
                tipo_credito=tipo_credito,
                perdcomp_retificador=perdcomp_retificador,
                numero_perdcomp_retificador=numero_perdcomp_retificador,
                credito_oriundo_de_acao_judicial=credito_oriundo_de_acao_judicial,
                qualificacao=qualificacao,
                pessoa_juridica_extinta_por_liquidacao_voluntaria=pessoa_juridica_extinta_por_liquidacao_voluntaria,
                nome_responsavel_da_pessoa_juridica_perante_rfb=nome_responsavel_da_pessoa_juridica_perante_rfb,
                cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB=cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                nome_responsavel_pelo_preechimento=nome_responsavel_pelo_preechimento,
                cpf_do_responsavel_pelo_preenchimento=cpf_do_responsavel_pelo_preenchimento,
                informado_em_processo_admistrativo_anterior=informado_em_processo_admistrativo_anterior,
                informado_em_outro_perdcomp=informado_em_outro_perdcomp,
                credito_sucedido=credito_sucedido,
                forma_tributacao_lucro=forma_tributacao_lucro,
                forma_apuracao=forma_apuracao,
                exercicio=exercicio,
                data_inicial_periodo=data_inicial_periodo,
                data_final_periodo=data_final_periodo,
                selic_acumulada=selic_acumulada,
                imposto_devido=imposto_devido,
                total_parcelas_composicao_credito=total_das_parcelas_composicao_credito,
                valor_saldo_negativo=valor_do_saldo_negativo,
                credito_original=credito_original,
                credito_atualizado=credito_atualizado,
                total_dos_debitos=total_dos_debitos,
                total_do_credito_original_utilizado_neste_documento=total_do_credito_original_utilizado_neste_documento,
                saldo_do_credito_original=saldo_do_credito_original,
            )
            self.stdout.write(f"Dcomp registrada: {dcomp}")
            self.stdout.write(f"Processando Declaração de Compensação Saldo Negativo de IRPJ: versão {perdcomp_version}, CNPJ {cnpj}")
        except Exception as e:
            err_variable = str(e)
            self.stderr.write(
                f"Erro ao processar Declaração de Compensação Saldo Negativo de IRPJ: {err_variable}. Variável envolvida: {e.args}")

    def processar_declaracao_compensacao_saldo_negativo_csll(self,texto):

        try:
            # CNPJ
            cnpj_match = re.search(r'CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)

            # Extraindo o CNPJ se encontrado
            cnpj = cnpj_match.group(1) if cnpj_match else None
            self.stderr.write(
                f"cnpj: {cnpj}.")
            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()

            print(f"CNPJ extraído: {cnpj} (tamanho: {len(cnpj)})")

            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # Número da DCOMP
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Número da PER
            numero_perdcomp_inicial_match = re.search(r'N° do PER/DCOMP Inicial\n([^\n]+)', texto)
            numero_perdcomp_inicial = numero_perdcomp_inicial_match.group(
                1) if numero_perdcomp_inicial_match else None

            if numero_perdcomp_inicial:
                try:
                    per_instance = PER.objects.get(numero_perdcomp=numero_perdcomp_inicial)
                except PER.DoesNotExist:
                    self.stderr.write(
                        f"PER não encontrado para o número: {numero_perdcomp_inicial}. Criando um novo...")
                    per_instance = PER.objects.create(numero=numero_perdcomp_inicial)
            else:
                per_instance = None

            # Nome empresarial
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            if not cnpj or not perdcomp_number:
                self.stderr.write("Erro: CNPJ ou Número de PER não encontrados no texto.")
                return

                # Verificar se a empresa já existe no banco
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )
            self.stdout.write(f"cnpj: {cnpj}")

            if created:
                self.stdout.write(f"Empresa criada: {empresa}")
            else:
                self.stdout.write(f"Empresa já existente: {empresa}")

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None
            data_de_criacao = self.converter_data(data_de_criacao)

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None
            data_de_transmissao = self.converter_data(data_de_transmissao)

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_retificador_match = re.search(r'PER/DCOMP Retificador\n([^\n]+)', texto)
            perdcomp_retificador = perdcomp_retificador_match.group(1) if perdcomp_retificador_match else None
            perdcomp_retificador = self.converter_para_booleano(perdcomp_retificador)

            # Número PER/DCOMP Retificador
            numero_perdcomp_retificador_match = re.search(r'N° PER/DCOMP Retificado\n([^\n]+)', texto)
            numero_perdcomp_retificador = numero_perdcomp_retificador_match.group(
                1) if numero_perdcomp_retificador_match else None

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)',
                                                               texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None
            credito_oriundo_de_acao_judicial = self.converter_para_booleano(credito_oriundo_de_acao_judicial)

            # Qualificação do Contribuinte
            qualificacao_match = re.search(r'Qualificação do Contribuinte\n([^\n]+)', texto)
            qualificacao = qualificacao_match.group(1) if qualificacao_match else None

            # Pessoa Jurídica Extinta por Liquidação Voluntária
            pessoa_juridica_extinta_por_liquidacao_voluntaria_match = re.search(
                r'Pessoa Jurídica Extinta por Liquidação Voluntária\n([^\n]+)', texto)
            pessoa_juridica_extinta_por_liquidacao_voluntaria = pessoa_juridica_extinta_por_liquidacao_voluntaria_match.group(
                1) if pessoa_juridica_extinta_por_liquidacao_voluntaria_match else None
            pessoa_juridica_extinta_por_liquidacao_voluntaria = self.converter_para_booleano(
                pessoa_juridica_extinta_por_liquidacao_voluntaria)

            # Nome Responsável da Pessoa Jurídica Perante a RFB
            nome_responsavel_da_pessoa_juridica_perante_rfb_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n([^\n]+)', texto)
            nome_responsavel_da_pessoa_juridica_perante_rfb = nome_responsavel_da_pessoa_juridica_perante_rfb_match.group(
                1) if nome_responsavel_da_pessoa_juridica_perante_rfb_match else None

            # CPF do Responsável da Pessoa Jurídica Perante a RFB
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match = re.search(
                r'Dados do Responsável da Pessoa Jurídica Perante a RFB\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB = cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match.group(
                1) if cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB_match else None

            # Dados do Responsável pelo Preenchimento
            nome_responsavel_pelo_preechimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n([^\n]+)', texto)
            nome_responsavel_pelo_preechimento = nome_responsavel_pelo_preechimento_match.group(
                1) if nome_responsavel_pelo_preechimento_match else None

            # CPF do responsável pelo preechimento
            cpf_do_responsavel_pelo_preenchimento_match = re.search(
                r'Dados do Responsável pelo Preenchimento\nNome\n[^\n]+\nCPF\n([^\n]+)', texto)
            cpf_do_responsavel_pelo_preenchimento = cpf_do_responsavel_pelo_preenchimento_match.group(
                1) if cpf_do_responsavel_pelo_preenchimento_match else None

            # Tentativa de encontrar "Informado em Processo Administrativo Anterior"
            informado_em_processo_admistrativo_anterior_match = re.search(
                r'Informado em Processo Administrativo Anterior\n([^\n]+)', texto)

            # Caso não encontre, tenta "Informado em Processo Administrativo anterior"
            if not informado_em_processo_admistrativo_anterior_match:
                informado_em_processo_admistrativo_anterior_match = re.search(
                    r'Informado em Processo Administrativo anterior\n([^\n]+)', texto)

            # Captura o valor encontrado ou define como None
            informado_em_processo_admistrativo_anterior = (
                informado_em_processo_admistrativo_anterior_match.group(1)
                if informado_em_processo_admistrativo_anterior_match
                else None
            )
            informado_em_processo_admistrativo_anterior = self.converter_para_booleano(informado_em_processo_admistrativo_anterior)

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_outro_perdcomp_match.group(
                1) if informado_em_outro_perdcomp_match else None
            informado_em_outro_perdcomp = self.converter_para_booleano(informado_em_outro_perdcomp)

            # Crédito de Sucedido
            credito_sucedido_match = re.search(r'Crédito de Sucedida\n([^\n]+)', texto)
            credito_sucedido = credito_sucedido_match.group(1) if credito_sucedido_match else None
            credito_sucedido = self.converter_para_booleano(credito_sucedido)

            # Forma de Tributação do Lucro
            forma_tributacao_lucro_match = re.search(r'Forma de Tributação do Lucro\n([^\n]+)', texto)
            if not forma_tributacao_lucro_match:
                forma_tributacao_lucro_match = re.search(r'Forma de Tributação no Período\n([^\n]+)', texto)

            forma_tributacao_lucro = forma_tributacao_lucro_match.group(1) if forma_tributacao_lucro_match else None

            # Forma de Apuração
            forma_apuracao_match = re.search(r'Forma de Apuração\n([^\n]+)', texto)
            forma_apuracao = forma_apuracao_match.group(1) if forma_apuracao_match else None

            # Exercício
            exercicio_match = re.search(r'Exercício\n([^\n]+)', texto)
            exercicio = exercicio_match.group(1) if exercicio_match else None

            # Data incial do período
            data_inicial_periodo_match = re.search(r'Data Inicial do Período\n([^\n]+)', texto)
            data_inicial_periodo = data_inicial_periodo_match.group(1) if data_inicial_periodo_match else None
            data_inicial_periodo = self.converter_data(data_inicial_periodo)

            # Data final do período
            data_final_periodo_match = re.search(r'Data Final do Período\n([^\n]+)', texto)
            data_final_periodo = data_final_periodo_match.group(1) if data_final_periodo_match else None
            data_final_periodo = self.converter_data(data_final_periodo)

            # Selic Acumulada
            selic_acumulada_match = re.search(r'Selic Acumulada\n([^\n]+)', texto)
            selic_acumulada = selic_acumulada_match.group(1) if selic_acumulada_match else None
            selic_acumulada = self.converter_valor(selic_acumulada)

            # Imposto Devido
            imposto_devido_match = re.search(r'Imposto Devido\n([^\n]+)', texto)

            if not imposto_devido_match:
                imposto_devido_match = re.search(r'CSLL Devida\n([^\n]+)', texto)

            imposto_devido = imposto_devido_match.group(1) if imposto_devido_match else None
            imposto_devido = self.converter_valor(imposto_devido)

            # Total das Parcelas de composição do Crédito
            total_das_parcelas_composicao_credito_match = re.search(
                r'([^\n]+)\nTotal das Parcelas de Composição do Crédito', texto)
            total_das_parcelas_composicao_credito = total_das_parcelas_composicao_credito_match.group(
                1) if total_das_parcelas_composicao_credito_match else None

            total_das_parcelas_composicao_credito = self.converter_valor(total_das_parcelas_composicao_credito)

            # Valor do Saldo Negativo
            valor_do_saldo_negativo_match = re.search(r'Valor do Saldo Negativo\n([^\n]+)', texto)
            valor_do_saldo_negativo = valor_do_saldo_negativo_match.group(1) if valor_do_saldo_negativo_match else None
            valor_do_saldo_negativo = self.converter_valor(valor_do_saldo_negativo)

            # Crédito Original na data de entrega
            credito_original_match = re.search(r'([\d\.,]+)\nSelic Acumulada', texto)
            credito_original = credito_original_match.group(1) if credito_original_match else None
            credito_original = self.converter_valor(credito_original)

            # Crédito Atualizado
            credito_atualizado_match = re.search(r'Crédito Atualizado\n([^\n]+)', texto)
            credito_atualizado = credito_atualizado_match.group(1) if credito_atualizado_match else None
            credito_atualizado = self.converter_valor(credito_atualizado)

            # Procura a posição de "Total dos Débitos deste Documento" no texto
            total_dos_debitos_deste_documento_match = re.match(r'\n([^\n]+)Total dos Débitos deste Documento', texto)

            if not total_dos_debitos_deste_documento_match:
                # Caso não encontre, tenta "Total dos Débitos desta DCOMP"
                total_dos_debitos_deste_documento_match = re.search(r'Total dos débitos desta DCOMP\n([^\n]+)', texto)

            total_dos_debitos = total_dos_debitos_deste_documento_match.group(1)
            total_dos_debitos = self.converter_valor(total_dos_debitos)

            # Total do Crédito Original Utilizado neste Documento
            total_do_credito_original_utilizado_neste_documento_match = re.search(
                r'Total do Crédito Original Utilizado nesta DCOMP\n([^\n]+)', texto)
            total_do_credito_original_utilizado_neste_documento = total_do_credito_original_utilizado_neste_documento_match.group(
                1) if total_do_credito_original_utilizado_neste_documento_match else None

            total_do_credito_original_utilizado_neste_documento = self.converter_valor(total_do_credito_original_utilizado_neste_documento)

            # Saldo do Crédito Original
            saldo_do_credito_original_match = re.search(r'Saldo do Crédito Original\n([^\n]+)', texto)
            saldo_do_credito_original = saldo_do_credito_original_match.group(
                1) if saldo_do_credito_original_match else None

            saldo_do_credito_original = self.converter_valor(saldo_do_credito_original)

            dcomp = Dcomp.objects.create(
                empresa=empresa,
                versao_perdcomp=perdcomp_version,
                cnpj=cnpj,
                numero_perdcomp=perdcomp_number,
                numero_perdcomp_inicial=per_instance,
                nome_empresarial=nome_empresarial,
                data_criacao=data_de_criacao,
                data_transmissao=data_de_transmissao,
                tipo_documento=tipo_documento,
                tipo_credito=tipo_credito,
                perdcomp_retificador=perdcomp_retificador,
                numero_perdcomp_retificador=numero_perdcomp_retificador,
                credito_oriundo_de_acao_judicial=credito_oriundo_de_acao_judicial,
                qualificacao=qualificacao,
                pessoa_juridica_extinta_por_liquidacao_voluntaria=pessoa_juridica_extinta_por_liquidacao_voluntaria,
                nome_responsavel_da_pessoa_juridica_perante_rfb=nome_responsavel_da_pessoa_juridica_perante_rfb,
                cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB=cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                nome_responsavel_pelo_preechimento=nome_responsavel_pelo_preechimento,
                cpf_do_responsavel_pelo_preenchimento=cpf_do_responsavel_pelo_preenchimento,
                informado_em_processo_admistrativo_anterior=informado_em_processo_admistrativo_anterior,
                informado_em_outro_perdcomp=informado_em_outro_perdcomp,
                credito_sucedido=credito_sucedido,
                forma_tributacao_lucro=forma_tributacao_lucro,
                forma_apuracao=forma_apuracao,
                exercicio=exercicio,
                data_inicial_periodo=data_inicial_periodo,
                data_final_periodo=data_final_periodo,
                selic_acumulada=selic_acumulada,
                imposto_devido=imposto_devido,
                total_parcelas_composicao_credito=total_das_parcelas_composicao_credito,
                valor_saldo_negativo=valor_do_saldo_negativo,
                credito_original=credito_original,
                credito_atualizado=credito_atualizado,
                total_dos_debitos=total_dos_debitos,
                total_do_credito_original_utilizado_neste_documento=total_do_credito_original_utilizado_neste_documento,
                saldo_do_credito_original=saldo_do_credito_original,
            )

            self.stdout.write(f"Dcomp registrada: {dcomp}")
            self.stdout.write(
                f"Processando Declaração de Compensação Saldo Negativo de IRPJ: versão {perdcomp_version}, CNPJ {cnpj}")
        except Exception as e:
            err_variable = str(e)
            self.stderr.write(
                f"Erro ao processar Declaração de Compensação Saldo Negativo de CSLL: {err_variable}. Variável envolvida: {e.args}")





