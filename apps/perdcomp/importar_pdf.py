import os
import pandas as pd
import fitz  # Biblioteca PyMuPDF
import re
from django.core.management.base import BaseCommand
from perdcomp.models import Empresa, PER, DCOMP, Debitos



# Função para ler PDFs
def read_pdf(file_path):
    document = fitz.open(file_path)
    pdf_text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        pdf_text += page.get_text()
    return pdf_text


# Classe para processar os PDFs
class Command(BaseCommand):
    help = "Importa dados dos PDFs PER, DCOMP e Débitos e associa às empresas."

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-dir',
            type=str,
            help="Caminho para o diretório de arquivos PER",
        )
        parser.add_argument(
            '--dcomp-dir',
            type=str,
            help="Caminho para o diretório de arquivos DCOMP",
        )
        parser.add_argument(
            '--debitos-dir',
            type=str,
            help="Caminho para o diretório de arquivos de Débitos",
        )

    def handle(self, *args, **options):
        # Caminhos dos diretórios com PDFs passados pelo usuário
        directory_paths = {
            'PER': options['per_dir'],
            'DCOMP': options['dcomp_dir'],
            'Débitos': options['debitos_dir']
        }

        # Verifica se o usuário forneceu todos os caminhos necessários
        for tipo, directory in directory_paths.items():
            if not directory:
                self.stdout.write(self.style.ERROR(
                    f"Por favor, forneça o caminho para o diretório de {tipo} usando a opção --{tipo.lower()}-dir"))
                return

        # Processa cada tipo de PDF e associa dados às empresas
        for tipo, directory in directory_paths.items():
            print(f"Processando arquivos {tipo} no diretório {directory}...")
            if tipo == 'PER':
                self.processar_per(directory)
            elif tipo == 'DCOMP':
                self.processar_dcomp(directory)
            elif tipo == 'Débitos':
                self.processar_debitos(directory)

    def processar_per(self, directory):
        all_texts = [read_pdf(os.path.join(directory, f)) for f in os.listdir(directory) if
                     f.endswith('.pdf') and "PER" in f and "DECLARAÇÃO" in f]
        data = []

        for texto in all_texts:
            # Extração de dados do PER
            # Versão do perdcomp
            version_match = re.search(r'PERDCOMP\s+(\d+\.\d+)', texto)
            perdcomp_version = version_match.group(1) if version_match else None

            # CNPJ
            cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            cnpj = cnpj_match.group(1) if cnpj_match else None

            # Número da perdcomp
            perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
            perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

            # Nome empresarial
            nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
            nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

            # Data de Criação
            data_de_criacao_match = re.search(r'Data de Criação\n([^\n]+)', texto)
            data_de_criacao = data_de_criacao_match.group(1) if data_de_criacao_match else None

            # Data de Transmissão
            data_de_transmissao_match = re.search(r'Data de Transmissão\n([^\n]+)', texto)
            data_de_transmissao = data_de_transmissao_match.group(1) if data_de_transmissao_match else None

            # Tipo de Documento
            tipo_documento_match = re.search(r'Tipo de Documento\n([^\n]+)', texto)
            tipo_documento = tipo_documento_match.group(1) if tipo_documento_match else None

            # Tipo de Crédito
            tipo_credito_match = re.search(r'Tipo de Crédito\n([^\n]+)', texto)
            tipo_credito = tipo_credito_match.group(1) if tipo_credito_match else None

            # PER/DCOMP Retificador
            perdcomp_retificador_match = re.search(r'PER/DCOMP Retificador\n([^\n]+)', texto)
            perdcomp_retificador = perdcomp_retificador_match.group(1) if perdcomp_retificador_match else None

            # Número PER/DCOMP Retificador

            # Crédito Oriundo de Ação Judicial
            credito_oriundo_de_acao_judicial_match = re.search(r'Crédito Oriundo de Ação Judicial\n([^\n]+)', texto)
            credito_oriundo_de_acao_judicial = credito_oriundo_de_acao_judicial_match.group(
                1) if credito_oriundo_de_acao_judicial_match else None

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

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_processo_admistrativo_anterior_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None

            # Situação Especial do Titular do Crédito
            situacao_especial_do_titular_credito_match = re.search(r'Situação Especial do Titular do Crédito\n([^\n]+)',
                                                                   texto)
            situacao_especial_do_titular_credito = situacao_especial_do_titular_credito_match.group(
                1) if situacao_especial_do_titular_credito_match else None

            # Crédito de Sucedido
            credito_sucedido_match = re.search(r'Crédito de Sucedida\n([^\n]+)', texto)
            credito_sucedido = credito_sucedido_match.group(1) if credito_sucedido_match else None

            # Valor Original do Crédito Inicial
            valor_original_do_credito_inicial_match = re.search(r'Valor Original do Crédito Inicial\n([^\n]+)', texto)
            valor_original_do_credito_inicial = valor_original_do_credito_inicial_match.group(
                1) if valor_original_do_credito_inicial_match else None

            # Crédito Original na Data da Entrega
            credito_original_match = re.search(r'([^\n]+)\nCrédito Original na Data da Entrega', texto)
            credito_original = credito_original_match.group(1) if credito_original_match else None

            # Valor do Pedido de Restituição
            valor_do_pedido_restituicao_match = re.search(r'Valor do Pedido de Restituição\n([^\n]+)', texto)
            valor_do_pedido_restituicao = valor_do_pedido_restituicao_match.group(
                1) if valor_do_pedido_restituicao_match else None

            # Período de Apuração
            periodo_de_apuracao_origem_credito_match = re.search(r'([^\n]+)\nPeríodo de Apuração', texto)
            periodo_de_apuracao_origem_credito = periodo_de_apuracao_origem_credito_match.group(
                1) if periodo_de_apuracao_origem_credito_match else None

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

            # Valor do Principal
            valor_do_principal_match = re.search(r'Valor do Principal\n([^\n]+)', texto)
            valor_do_principal = valor_do_principal_match.group(1) if valor_do_principal_match else None

            # Valor da Multa
            valor_da_multa_match = re.search(r'Valor da Multa\n([^\n]+)', texto)
            valor_da_multa = valor_da_multa_match.group(1) if valor_da_multa_match else None

            # Valor dos Juros
            valor_do_juros_match = re.search(r'([^\n]+)\nValor dos Juros', texto)
            valor_do_juros = valor_do_juros_match.group(1) if valor_do_juros_match else None

            # Valor Total
            valor_total_origem_credito_match = re.search(r'Valor Total\n([^\n]+)', texto)
            valor_total_origem_credito = valor_total_origem_credito_match.group(
                1) if valor_total_origem_credito_match else None

            # Criando ou associando empresa
            empresa, created = Empresa.objects.get_or_create(
                cnpj=cnpj,
                defaults={'nome': nome_empresarial}
            )

            # Cria ou atualiza os dados PER
            PER.objects.update_or_create(
                empresa=empresa,
                perdcomp_number=perdcomp_number,  # Usa perdcomp_number como identificador único
                defaults={
                    'versao': perdcomp_version,
                    'data_de_criacao': data_de_criacao,
                    'data_de_transmissao': data_de_transmissao,
                    'tipo_documento': tipo_documento,
                    'tipo_credito': tipo_credito,
                    'perdcomp_retificador': perdcomp_retificador,
                    'credito_oriundo_de_acao_judicial': credito_oriundo_de_acao_judicial,
                    'tipo_da_conta': tipo_da_conta,
                    'banco': banco,
                    'agencia': agencia,
                    'conta': conta,
                    'qualificacao': qualificacao,
                    'pessoa_juridica_extinta_por_liquidacao_voluntaria': pessoa_juridica_extinta_por_liquidacao_voluntaria,
                    'nome_responsavel_da_pessoa_juridica_perante_rfb': nome_responsavel_da_pessoa_juridica_perante_rfb,
                    'cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB': cpf_do_responsavel_da_pessoa_juridica_perante_a_RFB,
                    'nome_responsavel_pelo_preechimento': nome_responsavel_pelo_preechimento,
                    'cpf_do_responsavel_pelo_preenchimento': cpf_do_responsavel_pelo_preenchimento,
                    'informado_em_processo_admistrativo_anterior': informado_em_processo_admistrativo_anterior,
                    'informado_em_outro_perdcomp': informado_em_outro_perdcomp,
                    'situacao_especial_do_titular_credito': situacao_especial_do_titular_credito,
                    'credito_sucedido': credito_sucedido,
                    'valor_original_do_credito_inicial': valor_original_do_credito_inicial,
                    'credito_original': credito_original,
                    'valor_do_pedido_restituicao': valor_do_pedido_restituicao,
                    'periodo_de_apuracao_origem_credito': periodo_de_apuracao_origem_credito,
                    'cnpj_do_pagamento_origem_credito': cnpj_do_pagamento_origem_credito,
                    'codigo_da_receita': codigo_da_receita,
                    'grupo_do_tributo': grupo_do_tributo,
                    'data_de_arrecadacao': data_de_arrecadacao,
                    'valor_do_principal': valor_do_principal,
                    'valor_da_multa': valor_da_multa,
                    'valor_do_juros': valor_do_juros,
                    'valor_total_origem_credito': valor_total_origem_credito
                }
            )

    def processar_dcomp(self, directory):
        def processar_dcomp(self, directory):
            data = []

            # Função para ler todos os PDFs no diretório
            def read_pdfs_in_directory(directory_path):
                all_text = []
                for filename in os.listdir(directory_path):
                    if filename.endswith('.pdf') and "DCOMP" in filename and "DECLARAÇÃO" in filename:
                        file_path = os.path.join(directory_path, filename)
                        self.stdout.write(f"Lendo arquivo: {file_path}")
                        pdf_text = read_pdf(file_path)
                        all_text.append(pdf_text)
                return all_text

            # Processa cada PDF e extrai dados
            textos = read_pdfs_in_directory(directory)
            for texto in textos:

        pass

    def processar_debitos(self, directory):
        # Exemplo: lógica de processamento Débitos
        pass

    def regex_match(self, pattern, text):
        """Retorna a primeira correspondência de um padrão regex, ou None se não houver."""
        match = re.search(pattern, text)
        return match.group(1) if match else None
