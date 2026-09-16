# Controle de Reembolsos

Aplicativo desktop para Windows feito em Python + PySide6 para controlar reembolsos pagos a motoristas/funcionários.

O sistema registra reembolsos com múltiplos itens, calcula o total automaticamente, gera PDF, mantém histórico em SQLite e permite exportar dados em CSV.

## Funcionalidades

- Cadastro de motoristas com status ativo/inativo.
- Cadastro de tipos de serviço com status ativo/inativo.
- Lançamento de reembolso com uma ou várias linhas.
- Data individual por item do reembolso.
- Campos opcionais de placa e O.S.
- Valores em Real brasileiro.
- Cálculo automático do total.
- Número sequencial automático para cada reembolso.
- Histórico pesquisável por número, motorista, placa, período e tipo de serviço.
- Visualização detalhada de reembolsos.
- Geração e regeração de PDF.
- Exportação CSV compatível com Excel em português/Brasil.
- Backup e restauração do banco SQLite.
- Banco persistente fora do executável.

## Estrutura

```text
ControleReembolsos/
├── assets/
├── database/
├── services/
├── ui/
├── utils/
├── main.py
├── ControleReembolsos.spec
├── requirements.txt
└── README.md
```

## Banco de dados

Por padrão, o banco SQLite é criado em:

```text
%LOCALAPPDATA%\ControleReembolsos\reembolsos.db
```

Se o Windows negar acesso a esse local, o app usa como fallback uma pasta `data` ao lado do executável.

## Executar em desenvolvimento

Recomendado: Python 3.13.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Gerar o executável

Use Python 3.13 para o build. Em testes, Python 3.14 abriu o app em desenvolvimento, mas gerou erro de DLL do Qt ao empacotar com PyInstaller.

```powershell
venv\Scripts\activate
pyinstaller ControleReembolsos.spec --noconfirm
```

O executável será criado em:

```text
dist\ControleReembolsos.exe
```

## Observações

- Os arquivos de build, ambientes virtuais e bancos locais não devem ser versionados.
- O executável final pode ser distribuído separadamente da origem.
- A substituição do `.exe` por uma versão nova não apaga os dados persistidos no banco.
