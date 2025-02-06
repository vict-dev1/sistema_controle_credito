from django.core.management.base import BaseCommand
from perdcomp.models import Dcomp, Empresa,PER
import fitz
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation



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
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            print(f"Data inválida: {data_str}")
            return None

    def converter_valor(self, valor_str):
        try:
            valor_str = valor_str.replace('.', '').replace(',', '.')
            return Decimal(valor_str)
        except InvalidOperation:
            print(f"Valor inválido: {valor_str}")
            return None

    def converter_para_booleano(self, valor_str):
        if valor_str.strip().lower() in ['sim', 'yes', 'true', 'Sim', 'SIM']:
            return True
        elif valor_str.strip().lower() in ['não', 'no', 'false', 'Não', 'NÃO']:
            return False
        else:
            return None

    def processar_pedido_restituicao(self, texto):
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
                r'Informado em Processo Administrativo Anterior\n([^\n]+)', texto)
            informado_em_processo_admistrativo_anterior = informado_em_processo_admistrativo_anterior_match.group(
                1) if informado_em_processo_admistrativo_anterior_match else None
            informado_em_processo_admistrativo_anterior = self.converter_para_booleano(
                informado_em_processo_admistrativo_anterior)

            # Informado em Outro PER/DCOMP
            informado_em_outro_perdcomp_match = re.search(r'Informado em Outro PER/DCOMP\n([^\n]+)', texto)
            informado_em_outro_perdcomp = informado_em_processo_admistrativo_anterior_match.group(
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

    def processar_declaracao_compensacao(self, texto):
        try:
            # CNPJ
            cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            cnpj = cnpj_match.group(1) if cnpj_match else None

            cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()  # Remove formatações

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
            selic_acumulada_match = re.search(r'Situação Especial do Titular do Crédito\n([^\n]+)', texto)
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
