from django.core.management.base import BaseCommand
from perdcomp.models import DcompDebitos, Empresa
import fitz
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


class Command(BaseCommand):
    help = "Importa informações de PDFs de DCOMP Débitos e salva no banco de dados."

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
                if filename.endswith('.pdf') and "DCOMP" in filename and "DECLARAÇÃO" in filename:
                    file_path = os.path.join(directory_path, filename)
                    self.stdout.write(f"Lendo arquivo: {file_path}")
                    pdf_text = self.read_pdf(file_path)
                    if pdf_text:
                        all_text.append(pdf_text)
            return all_text
        except Exception as e:
            self.stderr.write(f"Erro ao processar o diretório '{directory_path}': {str(e)}")
            return []

    def converter_data(self,data_str):
        try:
            # Tenta converter a data para o formato correto
            return datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            # Se não for possível converter, retorna None
            print(f"Data inválida: {data_str}")
            return None

    def converter_valor(self,valor_str):
        try:
            # Remove pontos de milhar e substitui vírgulas por ponto
            valor_str = valor_str.replace('.', '').replace(',', '.')
            return Decimal(valor_str)
        except InvalidOperation:
            print(f"Valor inválido: {valor_str}")
            return None  # Retorna None se a conversão falhar

    def handle(self, *args, **options):
        directory_path = options['directory']

        if not os.path.exists(directory_path):
            self.stderr.write(f"Erro: O diretório especificado '{directory_path}' não existe.")
            return

        textos = self.read_pdfs_in_directory(directory_path)

        if not textos:
            self.stdout.write("Nenhum texto extraído dos PDFs. Verifique os arquivos no diretório.")
            return

        for texto in textos:
            try:
                # Extrair dados principais do PDF
                cnpj_match = re.search(r'PERDCOMP\s+\d+\.\d+\s+CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
                cnpj = cnpj_match.group(1) if cnpj_match else None

                cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()  # Remove formatações

                print(f"CNPJ extraído: {cnpj} (tamanho: {len(cnpj)})")

                perdcomp_number_match = re.search(r'(\d{5}\.\d{5}\.\d{6}\.\d\.\d\.\d{2}-\d{4})\nDADOS INICIAIS', texto)
                perdcomp_number = perdcomp_number_match.group(1) if perdcomp_number_match else None

                nome_empresarial_match = re.search(r'Nome Empresarial\n([^\n]+)', texto)
                nome_empresarial = nome_empresarial_match.group(1) if nome_empresarial_match else None

                if not cnpj or not perdcomp_number:
                    self.stderr.write("Erro: CNPJ ou Número de DCOMP não encontrados no texto.")
                    continue

                # Verificar se a empresa já existe no banco
                empresa, created = Empresa.objects.get_or_create(
                    cnpj=cnpj,
                    defaults={'nome': nome_empresarial}
                )

                if created:
                    self.stdout.write(f"Empresa criada: {empresa}")
                else:
                    self.stdout.write(f"Empresa já existente: {empresa}")

                debitos = re.findall(r'(\d{3}\.\s+Débito\s+[^\n]+)', texto)

                for debito in debitos:
                    try:
                        debito_start = texto.find(debito)
                        subsequent_text = texto[debito_start:]

                        grupo_de_tributo_match = re.search(r'Grupo de Tributo\s+([^\n]+)', subsequent_text)
                        grupo_de_tributo = grupo_de_tributo_match.group(1) if grupo_de_tributo_match else None

                        codigo_da_receita_denominacao_match = re.search(r'Código da Receita/Denominação\s+([^\n]+)', subsequent_text)
                        codigo_da_receita_denominacao = codigo_da_receita_denominacao_match.group(1) if codigo_da_receita_denominacao_match else None

                        periodo_da_apuracao_match = re.search(r'Período de Apuração\s+([^\n]+)', subsequent_text)
                        periodo_da_apuracao = periodo_da_apuracao_match.group(1) if periodo_da_apuracao_match else None

                        data_de_vencimento_do_tributo_quota_match = re.search(r'Data de Vencimento do Tributo/Quota\s+([^\n]+)', subsequent_text)
                        data_de_vencimento_do_tributo_quota = data_de_vencimento_do_tributo_quota_match.group(1) if data_de_vencimento_do_tributo_quota_match else None

                        data_de_vencimento_do_tributo_quota = self.converter_data(data_de_vencimento_do_tributo_quota)

                        periocidade_dctf_web_match = re.search(r'Periodicidade DCTFWeb\s+([^\n]+)', subsequent_text)
                        periocidade_dctf_web = periocidade_dctf_web_match.group(1) if periocidade_dctf_web_match else None

                        periodo_apuracao_dctfweb_match = re.search(r'([^\n]+)\nPeríodo Apuração DCTFWeb', subsequent_text)
                        periodo_apuracao_dctfweb = periodo_apuracao_dctfweb_match.group(1) if periodo_apuracao_dctfweb_match else None

                        valor_principal_match = re.search(r'Principal\s+([\d.,]+)', subsequent_text)
                        valor_principal = valor_principal_match.group(1).replace(',', '.') if valor_principal_match else None

                        multa_principal_match = re.search(r'Multa\s+([\d.,]+)', subsequent_text)
                        valor_multa = multa_principal_match.group(1).replace(',', '.') if multa_principal_match else None

                        juros_principal_match = re.search(r'Juros\s+([\d.,]+)', subsequent_text)
                        valor_juros = juros_principal_match.group(1).replace(',', '.') if juros_principal_match else None

                        valor_total_match = re.search(r'Total\s+([\d.,]+)', subsequent_text)
                        valor_total = valor_total_match.group(1).replace(',', '.') if valor_total_match else None

                        # Converte os valores para o formato decimal
                        valor_principal = self.converter_valor(valor_principal) if valor_principal else None
                        valor_multa = self.converter_valor(valor_multa) if valor_multa else None
                        valor_juros = self.converter_valor(valor_juros) if valor_juros else None
                        valor_total = self.converter_valor(valor_total) if valor_total else None

                        # Salvar os dados no banco de dados
                        debito = DcompDebitos.objects.create(
                            empresa=empresa,
                            cnpj=cnpj,
                            numero_dcomp=perdcomp_number,
                            nome_empresarial=nome_empresarial,
                            grupo_tributo=grupo_de_tributo,
                            codigo_da_receita_denominacao=codigo_da_receita_denominacao,
                            periodo_da_apuracao=periodo_da_apuracao,
                            periodicidade=periocidade_dctf_web,
                            data_de_vencimento_do_tributo_quota=data_de_vencimento_do_tributo_quota,
                            periocidade_dctf_web=periocidade_dctf_web,
                            periodo_apuracao_dctfweb=periodo_apuracao_dctfweb,
                            valor_principal=valor_principal,
                            valor_multa=valor_multa,
                            valor_juros=valor_juros,
                            valor_total=valor_total,
                        )
                        self.stdout.write(f"Débito registrado: {debito}")
                    except Exception as e:
                        self.stderr.write(f"Erro ao processar débito: {str(e)}")
            except Exception as e:
                self.stderr.write(f"Erro ao processar texto: {str(e)}")
