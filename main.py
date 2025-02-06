import xml.etree.ElementTree as ET
import pandas as pd

import xml.etree.ElementTree as ET
import pandas as pd


# Função para extrair informações de um arquivo XML
def ler_nfse(arquivo_xml):
    # Carregar o arquivo XML
    tree = ET.parse(arquivo_xml)
    root = tree.getroot()

    # Namespaces usados no XML
    namespaces = {
        'ns2': 'http://www.w3.org/2000/09/xmldsig#',
        'ns3': 'http://www.ginfes.com.br/tipos',
        'ns4': 'http://www.ginfes.com.br/servico_consultar_nfse_envio',
        'ns5': 'http://www.ginfes.com.br/servico_cancelar_nfse_envio'
    }

    # Lista para armazenar as informações de cada nota
    notas = []

    # Iterar sobre cada Nfse no arquivo
    for nfse in root.findall('ns2:Nfse', namespaces):
        # Dicionário para armazenar os dados de uma nota
        dados_nfse = {}

        # Identificação da Nfse
        identificacao = nfse.find('ns3:IdentificacaoNfse', namespaces)
        if identificacao is not None:
            dados_nfse['Numero'] = identificacao.find('ns3:Numero', namespaces).text
            dados_nfse['CodigoVerificacao'] = identificacao.find('ns3:CodigoVerificacao', namespaces).text
        dados_nfse['DataEmissao'] = nfse.find('ns3:DataEmissao', namespaces).text

        # Informações do serviço
        servico = nfse.find('ns3:Servico', namespaces)
        if servico is not None:
            valores = servico.find('ns3:Valores', namespaces)
            if valores is not None:
                dados_nfse['ValorServicos'] = valores.find('ns3:ValorServicos', namespaces).text
                dados_nfse['ValorIss'] = valores.find('ns3:ValorIss', namespaces).text
                dados_nfse['ValorLiquidoNfse'] = valores.find('ns3:ValorLiquidoNfse', namespaces).text
            dados_nfse['Discriminacao'] = servico.find('ns3:Discriminacao', namespaces).text

        # Prestador de serviço
        prestador = nfse.find('ns3:PrestadorServico', namespaces)
        if prestador is not None:
            prestador_identificacao = prestador.find('ns3:IdentificacaoPrestador', namespaces)
            if prestador_identificacao is not None:
                dados_nfse['PrestadorCNPJ'] = prestador_identificacao.find('ns3:Cnpj', namespaces).text
            dados_nfse['PrestadorRazaoSocial'] = prestador.find('ns3:RazaoSocial', namespaces).text

        # Tomador de serviço
        tomador = nfse.find('ns3:TomadorServico', namespaces)
        if tomador is not None:
            tomador_identificacao = tomador.find('ns3:IdentificacaoTomador', namespaces)
            if tomador_identificacao is not None:
                cpf_cnpj = tomador_identificacao.find('ns3:CpfCnpj/ns3:Cnpj', namespaces)
                if cpf_cnpj is not None:
                    dados_nfse['TomadorCNPJ'] = cpf_cnpj.text
                else:
                    dados_nfse['TomadorCNPJ'] = 'N/A'
            else:
                dados_nfse['TomadorCNPJ'] = 'N/A'
            dados_nfse['TomadorRazaoSocial'] = tomador.find('ns3:RazaoSocial', namespaces).text

        # Adicionar os dados da nota à lista
        notas.append(dados_nfse)

    return notas


# Função para salvar os dados em um arquivo Excel
def salvar_em_excel(dados, nome_arquivo):
    # Criar um DataFrame do pandas com os dados
    df = pd.DataFrame(dados)

    # Salvar o DataFrame em um arquivo Excel
    df.to_excel(nome_arquivo, index=False)


# Exemplo de uso das funções
arquivo_xml = r'C:\Users\rn202\OneDrive - Rosa Neto Tributos\Documentos Partilhados\1. Arquivos do Cliente\Maria Clara e JP\30798173000168\Demais documentos\ENC_ Documentos Solicitados para Planejamento Tributário\3.119860966840482E8.xml'  # Substitua pelo caminho do seu arquivo XML
notas = ler_nfse(arquivo_xml)

# Salvar os dados extraídos em um arquivo Excel
nome_arquivo_excel = 'notas_fiscais.xlsx'
salvar_em_excel(notas, nome_arquivo_excel)

print(f"Arquivo Excel '{nome_arquivo_excel}' gerado com sucesso!")

#arquivo_xml = r'C:\Users\rn202\OneDrive - Rosa Neto Tributos\Documentos Partilhados\1. Arquivos do Cliente\Maria Clara e JP\30798173000168\Demais documentos\ENC_ Documentos Solicitados para Planejamento Tributário\3.119860966840482E8.xml'  # Substitua pelo caminho do seu arquivo XML
