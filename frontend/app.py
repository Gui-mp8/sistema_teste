# app.py
from contracts.contrato import Contrato
import streamlit as st
from pydantic import ValidationError
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_column_letter(n):
    """Converte um índice de coluna (1-based) em uma letra de coluna."""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def main():
    # Carregar estilos personalizados
    def local_css(file_name):
        with open(file_name, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    # Chamar a função para carregar o CSS
    local_css("styles.css")

    # Cabeçalho com logotipo (opcional)
    st.markdown("""
        <div class="header">
            <h1>Sistema de Cadastro de Contratos de Cuidadoras</h1>
            <p>Bem-vindo ao sistema de cadastro de contratos. Por favor, preencha as informações abaixo.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    # Uso de formulário para agrupar campos
    with st.form(key='contract_form'):
        # Campos do formulário
        cpf = st.text_input("CPF*", placeholder="Digite o CPF do contratante")
        inicio_contrato_date = st.date_input("Início do Contrato*")
        valor_contrato = st.number_input("Valor do Contrato (R$)*", min_value=0.0, format="%.2f")
        qtd_funcionarios = st.number_input("Quantidade de Funcionários*", min_value=1, step=1)

        # Botão de submissão estilizado
        submit_button = st.form_submit_button(label='Salvar Contrato')

    if submit_button:
        inicio_contrato = datetime.combine(inicio_contrato_date, datetime.min.time())
        try:
            contrato = Contrato(
                cpf=cpf,
                inicio_contrato=inicio_contrato,
                valor_contrato=valor_contrato,
                qtd_funcionarios=qtd_funcionarios
            )

            # Autenticação com o Google Sheets
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/11HdvzxvVdOqu7iNYtq53heNPKgtdf-elUp3NO63DaOc/edit#gid=0')
            worksheet = sheet.get_worksheet(0)

            # Obter os cabeçalhos (primeira linha)
            headers = worksheet.row_values(1)
            if not headers:
                st.error("A planilha não possui cabeçalhos.")
                return

            # Encontrar o índice da coluna 'cpf'
            try:
                cpf_column_index = headers.index('cpf') + 1  # Índices de coluna começam em 1
            except ValueError:
                st.error("A coluna 'cpf' não foi encontrada na planilha.")
                return

            # Procurar o CPF na coluna específica
            try:
                cell = worksheet.find(contrato.cpf, in_column=cpf_column_index)
                # CPF encontrado, atualizar os dados na linha correspondente
                row_number = cell.row

                # Preparar os dados para atualização (na ordem dos cabeçalhos)
                data_to_update = []
                for header in headers:
                    if header == 'cpf':
                        data_to_update.append(contrato.cpf)
                    elif header == 'inicio_contrato':
                        data_to_update.append(contrato.inicio_contrato.strftime('%d/%m/%Y'))
                    elif header == 'valor_contrato':
                        data_to_update.append(f"{contrato.valor_contrato:.2f}")
                    elif header == 'qtd_funcionarios':
                        data_to_update.append(contrato.qtd_funcionarios)
                    else:
                        data_to_update.append('')  # Deixar vazio se houver colunas extras

                # Atualizar a linha na planilha
                last_column_letter = get_column_letter(len(headers))
                update_range = f"A{row_number}:{last_column_letter}{row_number}"
                worksheet.update(update_range, [data_to_update])

                st.success("Contrato atualizado com sucesso na planilha do Google Sheets!")

            except gspread.exceptions.CellNotFound:
                # CPF não encontrado, inserir nova linha
                data = []
                for header in headers:
                    if header == 'cpf':
                        data.append(contrato.cpf)
                    elif header == 'inicio_contrato':
                        data.append(contrato.inicio_contrato.strftime('%d/%m/%Y'))
                    elif header == 'valor_contrato':
                        data.append(f"{contrato.valor_contrato:.2f}")
                    elif header == 'qtd_funcionarios':
                        data.append(contrato.qtd_funcionarios)
                    else:
                        data.append('')  # Deixar vazio se houver colunas extras

                worksheet.append_row(data)
                st.success("Contrato salvo com sucesso e enviado para o Google Sheets!")

            # Exibir os dados salvos de forma organizada
            st.markdown(f"""
                <div class="saved-data">
                    <h3>Dados Salvos:</h3>
                    <p><strong>CPF Contratante:</strong> {contrato.cpf}</p>
                    <p><strong>Início do Contrato:</strong> {contrato.inicio_contrato.strftime('%d/%m/%Y')}</p>
                    <p><strong>Valor do Contrato:</strong> R$ {contrato.valor_contrato:.2f}</p>
                    <p><strong>Quantidade de Funcionários Alocados:</strong> {contrato.qtd_funcionarios}</p>
                </div>
            """, unsafe_allow_html=True)

        except ValidationError as e:
            for error in e.errors():
                st.error(f"Erro no campo '{error['loc'][0]}': {error['msg']}")
        except Exception as e:
            st.error(f"Ocorreu um erro ao salvar os dados: {e}")

    # Rodapé
    st.markdown("""
        <hr>
        <div class="footer">
            <p>&copy; 2023 Empresa de Cuidadoras. Todos os direitos reservados.</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
