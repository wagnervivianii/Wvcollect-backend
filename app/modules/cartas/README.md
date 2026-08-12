# Módulo Cartas

O módulo `cartas` é um domínio independente dentro do backend do WVCollect.

## Responsabilidade

O módulo é responsável por:

- cadastrar e versionar modelos de cartas;
- associar modelos a redes;
- identificar os campos exigidos pelos modelos variáveis;
- analisar planilhas temporárias de geração;
- selecionar automaticamente o modelo correto por rede;
- validar os dados necessários antes da geração;
- gerar documentos variáveis;
- reutilizar documentos estáticos;
- preparar lotes para revisão;
- preparar documentos para envio pelo WhatsApp.

## Isolamento

O módulo não deve reutilizar tabelas operacionais existentes do WVCollect
para persistir informações próprias de cartas.

Todas as tabelas deste domínio devem possuir prefixo `carta_`.

Toda alteração de schema deve ser realizada por migration Alembic.

Não devem ser realizadas alterações manuais no PostgreSQL.

## Planilhas

A planilha enviada pelo operador é um dado transitório.

Fluxo:

1. receber o arquivo;
2. analisar a estrutura;
3. identificar redes;
4. identificar os modelos necessários;
5. validar campos obrigatórios;
6. preparar ou gerar as cartas;
7. descartar a planilha.

As linhas da planilha não devem ser persistidas permanentemente no banco.

## Storage

Arquivos de modelos e documentos gerados não devem ser armazenados como
BLOB no PostgreSQL.

Estrutura inicial prevista:

storage/
└── cartas/
    ├── modelos/
    │   ├── estaticos/
    │   └── variaveis/
    ├── temporarios/
    └── gerados/

O banco deve guardar somente os metadados e o caminho/chave do arquivo.

A camada de storage deverá permitir futura substituição do filesystem local
por S3 ou solução equivalente sem alterar o domínio.

## Tipos de modelo

### ESTATICO

Documento pronto para utilização.

Exemplo:

- modelo PDF cadastrado para uma rede;
- o arquivo não sofre modificação;
- o sistema apenas seleciona o documento correto.

### VARIAVEL

Documento que contém campos substituíveis.

Exemplo:

- modelo DOCX;
- campos identificados no modelo;
- dados obtidos temporariamente da planilha;
- geração de novo documento/PDF.

## Granularidade

### PROMOTOR_REDE

Um único documento para:

PROMOTOR + REDE + MODELO

Mesmo que o promotor possua vários PDVs da mesma rede.

### PDV

Um documento por:

PROMOTOR + PDV + MODELO

Utilizado quando o conteúdo da carta contém informações específicas da loja.

## Persistência inicialmente prevista

Primeiro ciclo:

- carta_modelo
- carta_modelo_rede
- carta_modelo_campo
- carta_modelo_versao

Segundo ciclo, quando a geração estiver implementada:

- carta_lote
- carta_envio

As tabelas do segundo ciclo não devem ser antecipadas enquanto o fluxo real
de geração e envio ainda estiver sendo construído.
